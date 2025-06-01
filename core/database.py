"""
Vector Database Manager - Core implementation
"""

import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np

from config.settings import (
    CHROMA_DB_PATH,
    EMBEDDING_MODEL,
    MIN_OSCILLATION_SAMPLES,
)
from config.logging import get_logger

from .models import (
    DataType,
    EngineType,
    CharacterProfileEntry,
    EngineStateEntry,
    InternalStateEntry,
    RelationshipStateEntry,
    SessionStateEntry,
    ConversationEntry,
    SecureEntropyEntry,
)
from .utils import (
    safe_json_dumps,
    safe_json_loads,
    filter_metadata,
    safe_metadata_value,
)
from .exceptions import (
    VectorDatabaseError,
    SessionError,
    CharacterNotFoundError,
)

from security.entropy import SecureEntropySource
from security.pink_noise import SecureEnhancedPinkNoiseGenerator
from session.manager import SecureSessionManager
from document.manager import DocumentManager
from oscillation.patterns import OscillationPatternData

logger = get_logger(__name__)


class VectorDatabaseManager:
    """ベクトルデータベース管理システム（v3.1対応版 + セキュアエントロピー統合 + ChromaDB修正版 + ドキュメント統合版 + 振動メトリクス修正版）"""
    
    def __init__(self, db_path: str = CHROMA_DB_PATH, model_name: str = EMBEDDING_MODEL):
        """初期化"""
        self.db_path = db_path
        self.model_name = model_name
        
        # セキュアエントロピー源の初期化
        logger.info("Initializing Secure Entropy Source...")
        self.entropy_source = SecureEntropySource()
        
        # セキュア強化ピンクノイズジェネレータ
        self.pink_noise_generator = SecureEnhancedPinkNoiseGenerator(self.entropy_source)
        
        # ドキュメント管理システムの初期化
        logger.info("Initializing Document Manager...")
        self.doc_manager = DocumentManager()
        
        # SentenceTransformerモデル初期化
        logger.info(f"Loading embedding model: {model_name}")
        self.embedding_model = SentenceTransformer(model_name)
        
        # ChromaDB初期化
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(allow_reset=True)
        )
        
        # コレクション初期化
        self._init_collections()
        
        # セキュアセッション管理初期化
        self.session_manager = SecureSessionManager()
        
        # アクティブキャラクターとセッション
        self.active_character_id = None
        self.active_session_id = None
        
        # 振動履歴管理（修正版：より堅牢な管理）
        self.oscillation_buffer = defaultdict(lambda: {"values": [], "timestamps": []})
        
        logger.info("VectorDatabaseManager v3.1 with Secure Entropy, ChromaDB fixes, Document integration, and Fixed Oscillation Metrics initialized successfully")
        
        # エントロピー品質のログ出力
        quality = self.entropy_source.assess_entropy_quality()
        logger.info(f"Secure Entropy Quality: {quality}")
        
        # ドキュメント状況のログ出力
        doc_info = self.doc_manager.get_document_info()
        logger.info(f"Document Manager Status: {len(doc_info['available_documents'])} documents configured")
    
    def _init_collections(self):
        """コレクションの初期化（v3.1拡張版）"""
        self.collections = {}
        
        for data_type in DataType:
            collection_name = f"agent_{data_type.value}_v31_secure_docs_oscillation_fixed"
            try:
                self.collections[data_type] = self.client.get_collection(collection_name)
                logger.info(f"Loaded existing collection: {collection_name}")
            except:
                self.collections[data_type] = self.client.create_collection(
                    name=collection_name,
                    metadata={"description": f"Collection for {data_type.value} data (v3.1 secure docs oscillation fixed)"}
                )
                logger.info(f"Created new collection: {collection_name}")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """テキストの埋め込みベクトル生成"""
        embedding = self.embedding_model.encode(text)
        return embedding.tolist()
    
    def _generate_composite_embedding(self, texts: List[str], weights: Optional[List[float]] = None) -> List[float]:
        """複数テキストの重み付き合成埋め込み生成"""
        if weights is None:
            weights = [1.0] * len(texts)
        
        embeddings = [self.embedding_model.encode(text) for text in texts]
        weighted_embedding = np.zeros_like(embeddings[0])
        
        for embedding, weight in zip(embeddings, weights):
            weighted_embedding += embedding * weight
        
        # 正規化
        norm = np.linalg.norm(weighted_embedding)
        if norm > 0:
            weighted_embedding /= norm
        
        return weighted_embedding.tolist()
    
    def start_session(self, character_id: str) -> str:
        """新しいセッションを開始"""
        session_id = self.session_manager.create_session(character_id)
        self.active_session_id = session_id
        self.active_character_id = character_id
        
        # セッション状態エントリを作成
        session_state = SessionStateEntry(
            id=str(uuid.uuid4()),
            session_id=session_id,
            character_id=character_id,
            start_time=datetime.now(),
            last_update=datetime.now(),
            interaction_count=0,
            internal_state_id="",
            relationship_state_id="",
            oscillation_history=[],
            environment_state={
                "session_duration": 0.0,
                "interaction_count": 0,
                "emotional_volatility": 0.3,
                "topic_consistency": 0.7
            },
            active=True
        )
        
        # データベースに保存
        self._save_session_state(session_state)
        
        # 振動バッファを初期化
        self._initialize_oscillation_buffer(session_id)
        
        logger.info(f"Started new session: {session_id} for character: {character_id}")
        return session_id
    
    def resume_session(self, session_id: str) -> bool:
        """既存のセッションを再開（修正版：振動バッファ復元付き）"""
        session_data = self.session_manager.load_session(session_id)
        if session_data:
            self.active_session_id = session_id
            self.active_character_id = session_data.get("character_id")
            
            # セッション状態を更新
            self._update_session_state(session_id, {"active": True, "last_update": datetime.now()})
            
            # 振動バッファを復元
            self._restore_oscillation_buffer(session_id)
            
            logger.info(f"Resumed session: {session_id} with oscillation buffer restored")
            return True
        return False
    
    def _initialize_oscillation_buffer(self, session_id: str):
        """振動バッファの初期化（新規追加）"""
        buffer = self.oscillation_buffer[session_id]
        
        # セキュアエントロピーで初期値を生成
        for _ in range(5):  # 最小限の初期値を生成
            secure_oscillation = float(self.entropy_source.get_thermal_oscillation(0.3))
            buffer["values"].append(secure_oscillation)
            buffer["timestamps"].append(datetime.now())
        
        logger.info(f"Initialized oscillation buffer for session {session_id} with {len(buffer['values'])} initial values")
    
    def _restore_oscillation_buffer(self, session_id: str):
        """振動バッファをデータベースから復元（新規追加）"""
        try:
            # データベースから振動パターンを取得
            oscillation_results = self.collections[DataType.OSCILLATION_PATTERN].get(
                where={"session_id": session_id},
                include=["metadatas"],
                limit=50  # 直近50件
            )
            
            buffer = self.oscillation_buffer[session_id]
            restored_count = 0
            
            if oscillation_results["metadatas"]:
                for metadata in oscillation_results["metadatas"]:
                    try:
                        pattern_data = safe_json_loads(metadata["pattern_data"])
                        if "history" in pattern_data and pattern_data["history"]:
                            for value in pattern_data["history"]:
                                buffer["values"].append(float(value))
                                # タイムスタンプも復元
                                timestamp = datetime.fromisoformat(metadata["timestamp"])
                                buffer["timestamps"].append(timestamp)
                                restored_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to restore oscillation pattern: {e}")
                        continue
            
            # 会話データからも振動値を復元
            conversation_results = self.collections[DataType.CONVERSATION].get(
                where={"session_id": session_id},
                include=["metadatas"],
                limit=50
            )
            
            if conversation_results["metadatas"]:
                for metadata in conversation_results["metadatas"]:
                    try:
                        if "oscillation_value" in metadata and metadata["oscillation_value"] is not None:
                            buffer["values"].append(float(metadata["oscillation_value"]))
                            timestamp = datetime.fromisoformat(metadata["timestamp"])
                            buffer["timestamps"].append(timestamp)
                            restored_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to restore conversation oscillation: {e}")
                        continue
            
            # データが不足している場合は補充
            if len(buffer["values"]) < 5:
                shortage = 5 - len(buffer["values"])
                logger.info(f"Insufficient restored data ({len(buffer['values'])}), generating {shortage} supplementary values")
                
                for _ in range(shortage):
                    secure_oscillation = float(self.entropy_source.get_thermal_oscillation(0.3))
                    buffer["values"].append(secure_oscillation)
                    buffer["timestamps"].append(datetime.now())
                    restored_count += 1
            
            # タイムスタンプ順にソート
            if len(buffer["values"]) == len(buffer["timestamps"]):
                combined = list(zip(buffer["timestamps"], buffer["values"]))
                combined.sort(key=lambda x: x[0])
                buffer["timestamps"], buffer["values"] = zip(*combined)
                buffer["timestamps"] = list(buffer["timestamps"])
                buffer["values"] = list(buffer["values"])
            
            logger.info(f"Restored {restored_count} oscillation values for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to restore oscillation buffer: {e}")
            # フォールバック：最小限の値を生成
            self._initialize_oscillation_buffer(session_id)
    
    def _ensure_oscillation_data(self, session_id: str, min_samples: int = MIN_OSCILLATION_SAMPLES):
        """振動データが不足している場合の自動補充（新規追加）"""
        buffer = self.oscillation_buffer[session_id]
        
        if len(buffer["values"]) < min_samples:
            shortage = min_samples - len(buffer["values"])
            logger.info(f"Supplementing {shortage} oscillation samples for session {session_id}")
            
            for _ in range(shortage):
                secure_oscillation = float(self.entropy_source.get_thermal_oscillation(0.3))
                pink_component = float(self.pink_noise_generator.generate_secure_pink_noise())
                combined = float(secure_oscillation * 0.7 + pink_component * 0.3)
                
                buffer["values"].append(combined)
                buffer["timestamps"].append(datetime.now())
    
    def _save_session_state(self, session_state: SessionStateEntry):
        """セッション状態をデータベースに保存（修正版）"""
        state_text = f"Session: {session_state.session_id}\nCharacter: {session_state.character_id}"
        embedding = self._generate_embedding(state_text)
        
        # メタデータの安全な構築
        metadata = {
            "id": str(session_state.id),
            "session_id": str(session_state.session_id),
            "character_id": str(session_state.character_id),
            "start_time": session_state.start_time.isoformat(),
            "last_update": session_state.last_update.isoformat(),
            "interaction_count": int(session_state.interaction_count),
            "internal_state_id": str(session_state.internal_state_id),
            "relationship_state_id": str(session_state.relationship_state_id),
            "oscillation_history": safe_json_dumps(session_state.oscillation_history),
            "environment_state": safe_json_dumps(session_state.environment_state),
            "active": bool(session_state.active)
        }
        
        # フィルタリングを適用
        metadata = filter_metadata(metadata)
        
        self.collections[DataType.SESSION_STATE].add(
            embeddings=[embedding],
            documents=[state_text],
            metadatas=[metadata],
            ids=[session_state.id]
        )
    
    def _update_session_state(self, session_id: str, updates: Dict[str, Any]):
        """セッション状態を更新"""
        # セッション管理システムを更新
        self.session_manager.update_session(session_id, updates)
    
    def _update_oscillation_history(self, pattern: OscillationPatternData):
        """振動履歴を更新（セキュアエントロピー統合版・修正版）"""
        if self.active_session_id:
            buffer = self.oscillation_buffer[self.active_session_id]
            
            # セキュアエントロピーベースの新しい振動値を生成
            if pattern.secure_entropy_enabled:
                secure_pink_noise = float(self.pink_noise_generator.generate_secure_pink_noise())
                thermal_oscillation = float(self.entropy_source.get_thermal_oscillation(pattern.amplitude))
                combined_oscillation = float(secure_pink_noise * 0.7 + thermal_oscillation * 0.3)
                buffer["values"].append(combined_oscillation)
            else:
                # パターンの履歴から値を追加
                if pattern.history:
                    buffer["values"].extend([float(v) for v in pattern.history])
                else:
                    # フォールバック：基本的な振動値を生成
                    fallback_oscillation = float(self.entropy_source.get_thermal_oscillation(pattern.amplitude))
                    buffer["values"].append(fallback_oscillation)
            
            buffer["timestamps"].append(pattern.timestamp)
            
            # バッファサイズ制限
            max_size = 1000
            if len(buffer["values"]) > max_size:
                buffer["values"] = buffer["values"][-max_size:]
                buffer["timestamps"] = buffer["timestamps"][-max_size:]
            
            logger.debug(f"Updated oscillation history for session {self.active_session_id}: {len(buffer['values'])} values")
    
    def add_character_profile(self, name: str, background: str, instruction: str,
                            personality_traits: Dict[str, float],
                            values: Dict[str, float],
                            goals: List[str],
                            fears: List[str],
                            existential_parameters: Dict[str, float],
                            engine_parameters: Dict[str, Dict[str, Any]]) -> str:
        """完全なキャラクタープロファイルの追加（v3.1対応・修正版）"""
        profile_id = str(uuid.uuid4())
        entry = CharacterProfileEntry(
            id=profile_id,
            name=name,
            background=background,
            instruction=instruction,  # 演技指導変数
            personality_traits=personality_traits,
            values=values,
            goals=goals,
            fears=fears,
            existential_parameters=existential_parameters,
            engine_parameters=engine_parameters,
            timestamp=datetime.now(),
            version="3.1"
        )
        
        # プロファイルの埋め込み作成（演技指導を重視）
        profile_texts = [
            f"Name: {name}",
            f"Background: {background}",
            f"Instruction: {instruction}",  # 演技指導を含める
            f"Personality: {safe_json_dumps(personality_traits)}",
            f"Values: {safe_json_dumps(values)}",
            f"Goals: {', '.join(goals)}",
            f"Fears: {', '.join(fears)}",
            f"Existential: {safe_json_dumps(existential_parameters)}"
        ]
        
        # 演技指導に高い重みを与える
        weights = [1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.5]
        embedding = self._generate_composite_embedding(profile_texts, weights)
        
        # メタデータの安全な構築
        metadata = filter_metadata({
            "id": str(profile_id),
            "name": str(name),
            "background": str(background),
            "instruction": str(instruction),
            "personality_traits": safe_json_dumps(personality_traits),
            "values": safe_json_dumps(values),
            "goals": safe_json_dumps(goals),
            "fears": safe_json_dumps(fears),
            "existential_parameters": safe_json_dumps(existential_parameters),
            "engine_parameters": safe_json_dumps(engine_parameters),
            "timestamp": entry.timestamp.isoformat(),
            "version": str(entry.version)
        })
        
        self.collections[DataType.CHARACTER_PROFILE].add(
            embeddings=[embedding],
            documents=["\n".join(profile_texts)],
            metadatas=[metadata],
            ids=[profile_id]
        )
        
        self.active_character_id = profile_id
        
        # 新しいセッションを自動開始
        self.start_session(profile_id)
        
        logger.info(f"Added character profile v3.1: {name} (ID: {profile_id})")
        return profile_id
    
    def add_internal_state(self, state_data: Dict[str, Any]) -> str:
        """統合内部状態の保存（修正版）"""
        state_id = str(uuid.uuid4())
        entry = InternalStateEntry(
            id=state_id,
            timestamp=datetime.now(),
            consciousness_state=state_data.get("consciousness_state", {}),
            qualia_state=state_data.get("qualia_state", {}),
            emotion_state=state_data.get("emotion_state", {}),
            empathy_state=state_data.get("empathy_state", {}),
            motivation_state=state_data.get("motivation_state", {}),
            curiosity_state=state_data.get("curiosity_state", {}),
            conflict_state=state_data.get("conflict_state", {}),
            relationship_state=state_data.get("relationship_state", {}),
            existential_need_state=state_data.get("existential_need_state", {}),
            growth_wish_state=state_data.get("growth_wish_state", {}),
            overall_energy=state_data.get("overall_energy", 0.5),
            cognitive_load=state_data.get("cognitive_load", 0.3),
            emotional_tone=state_data.get("emotional_tone", "neutral"),
            attention_focus=state_data.get("attention_focus"),
            relational_distance=state_data.get("relational_distance", 0.6),
            paradox_tension=state_data.get("paradox_tension", 0.5),
            oscillation_stability=state_data.get("oscillation_stability", 0.7),
            character_id=self.active_character_id or "",
            session_id=self.active_session_id or ""
        )
        
        # 統合状態の埋め込み作成
        state_summary = f"""
        Energy: {entry.overall_energy}
        Cognitive Load: {entry.cognitive_load}
        Emotional Tone: {entry.emotional_tone}
        Relational Distance: {entry.relational_distance}
        Paradox Tension: {entry.paradox_tension}
        Oscillation Stability: {entry.oscillation_stability}
        """
        embedding = self._generate_embedding(state_summary)
        
        # メタデータの安全な構築
        metadata = filter_metadata({
            "id": str(state_id),
            "timestamp": entry.timestamp.isoformat(),
            "consciousness_state": safe_json_dumps(entry.consciousness_state),
            "qualia_state": safe_json_dumps(entry.qualia_state),
            "emotion_state": safe_json_dumps(entry.emotion_state),
            "empathy_state": safe_json_dumps(entry.empathy_state),
            "motivation_state": safe_json_dumps(entry.motivation_state),
            "curiosity_state": safe_json_dumps(entry.curiosity_state),
            "conflict_state": safe_json_dumps(entry.conflict_state),
            "relationship_state": safe_json_dumps(entry.relationship_state),
            "existential_need_state": safe_json_dumps(entry.existential_need_state),
            "growth_wish_state": safe_json_dumps(entry.growth_wish_state),
            "overall_energy": safe_metadata_value(entry.overall_energy, 0.5),
            "cognitive_load": safe_metadata_value(entry.cognitive_load, 0.3),
            "emotional_tone": str(entry.emotional_tone),
            "attention_focus": safe_json_dumps(entry.attention_focus) if entry.attention_focus else "",
            "relational_distance": safe_metadata_value(entry.relational_distance, 0.6),
            "paradox_tension": safe_metadata_value(entry.paradox_tension, 0.5),
            "oscillation_stability": safe_metadata_value(entry.oscillation_stability, 0.7),
            "character_id": str(entry.character_id),
            "session_id": str(entry.session_id)
        })
        
        self.collections[DataType.INTERNAL_STATE].add(
            embeddings=[embedding],
            documents=[state_summary],
            metadatas=[metadata],
            ids=[state_id]
        )
        
        # セッション状態を更新
        if self.active_session_id:
            self._update_session_state(self.active_session_id, {"internal_state_id": state_id})
        
        logger.info(f"Added internal state: {state_id}")
        return state_id
    
    def add_relationship_state(self, attachment_level: float, optimal_distance: float,
                             current_distance: float, paradox_tension: float,
                             oscillation_pattern: Optional[Dict[str, Any]] = None,
                             stability_index: float = 0.7, dependency_risk: float = 0.2,
                             growth_potential: float = 0.8) -> str:
        """関係性状態の保存（セキュアエントロピー統合版・修正版）"""
        state_id = str(uuid.uuid4())
        
        # セキュアエントロピー強化振動パターンの処理
        if oscillation_pattern:
            if isinstance(oscillation_pattern, dict):
                pattern_data = OscillationPatternData(
                    amplitude=oscillation_pattern.get("amplitude", 0.3),
                    frequency=oscillation_pattern.get("frequency", 0.5),
                    phase=oscillation_pattern.get("phase", 0.0),
                    pink_noise_enabled=oscillation_pattern.get("pink_noise_enabled", True),
                    pink_noise_intensity=oscillation_pattern.get("pink_noise_intensity", 0.15),
                    spectral_slope=oscillation_pattern.get("spectral_slope", -1.0),
                    damping_coefficient=oscillation_pattern.get("damping_coefficient", 0.7),
                    damping_type=oscillation_pattern.get("damping_type", "underdamped"),
                    natural_frequency=oscillation_pattern.get("natural_frequency", 2.0),
                    current_velocity=oscillation_pattern.get("current_velocity", 0.0),
                    target_value=oscillation_pattern.get("target_value", 0.0),
                    chaotic_enabled=oscillation_pattern.get("chaotic_enabled", False),
                    lyapunov_exponent=oscillation_pattern.get("lyapunov_exponent", 0.1),
                    attractor_strength=oscillation_pattern.get("attractor_strength", 0.5),
                    secure_entropy_enabled=oscillation_pattern.get("secure_entropy_enabled", True),
                    secure_entropy_intensity=oscillation_pattern.get("secure_entropy_intensity", 0.15),
                    history=oscillation_pattern.get("history", [])
                )
            else:
                pattern_data = oscillation_pattern
        else:
            # セキュアエントロピー強化デフォルト振動パターン
            pattern_data = OscillationPatternData(
                amplitude=0.3,
                frequency=0.5,
                phase=0.0,
                pink_noise_enabled=True,
                pink_noise_intensity=0.15,
                spectral_slope=-1.0,
                damping_coefficient=0.7,
                damping_type="underdamped",
                natural_frequency=2.0,
                current_velocity=0.0,
                target_value=0.0,
                chaotic_enabled=False,
                lyapunov_exponent=0.1,
                attractor_strength=0.5,
                secure_entropy_enabled=True,
                secure_entropy_intensity=0.15,
                history=[]
            )
        
        # セキュアエントロピー情報を追加
        entropy_quality = self.entropy_source.assess_entropy_quality()
        pattern_data.entropy_source_info = entropy_quality
        
        # セキュアエントロピーベースの初期履歴生成
        if pattern_data.secure_entropy_enabled and not pattern_data.history:
            for _ in range(10):
                secure_oscillation = float(self.entropy_source.get_thermal_oscillation(pattern_data.amplitude))
                pattern_data.history.append(secure_oscillation)
        
        entry = RelationshipStateEntry(
            id=state_id,
            attachment_level=attachment_level,
            optimal_distance=optimal_distance,
            current_distance=current_distance,
            paradox_tension=paradox_tension,
            oscillation_pattern=pattern_data,
            stability_index=stability_index,
            dependency_risk=dependency_risk,
            growth_potential=growth_potential,
            timestamp=datetime.now(),
            character_id=self.active_character_id or "",
            session_id=self.active_session_id or ""
        )
        
        # 関係性状態の埋め込み作成
        relationship_text = f"""
        Attachment: {attachment_level}
        Current Distance: {current_distance}
        Optimal Distance: {optimal_distance}
        Paradox Tension: {paradox_tension}
        Stability: {stability_index}
        Dependency Risk: {dependency_risk}
        Growth Potential: {growth_potential}
        Secure Entropy: {pattern_data.secure_entropy_enabled}
        Entropy Source: {entropy_quality.get('entropy_source', 'unknown')}
        """
        embedding = self._generate_embedding(relationship_text)
        
        # メタデータの安全な構築
        metadata = filter_metadata({
            "id": str(state_id),
            "attachment_level": safe_metadata_value(attachment_level, 0.5),
            "optimal_distance": safe_metadata_value(optimal_distance, 0.5),
            "current_distance": safe_metadata_value(current_distance, 0.5),
            "paradox_tension": safe_metadata_value(paradox_tension, 0.5),
            "oscillation_pattern": safe_json_dumps(pattern_data.to_dict()),
            "stability_index": safe_metadata_value(stability_index, 0.7),
            "dependency_risk": safe_metadata_value(dependency_risk, 0.2),
            "growth_potential": safe_metadata_value(growth_potential, 0.8),
            "timestamp": entry.timestamp.isoformat(),
            "character_id": str(entry.character_id),
            "session_id": str(entry.session_id)
        })
        
        self.collections[DataType.RELATIONSHIP].add(
            embeddings=[embedding],
            documents=[relationship_text],
            metadatas=[metadata],
            ids=[state_id]
        )
        
        # セッション状態を更新
        if self.active_session_id:
            self._update_session_state(self.active_session_id, {"relationship_state_id": state_id})
        
        # 振動履歴を更新（修正版）
        self._update_oscillation_history(pattern_data)
        
        logger.info(f"Added relationship state with secure entropy: {state_id}")
        return state_id
    
    def add_oscillation_pattern(self, pattern_data: Dict[str, Any]) -> str:
        """振動パターンの保存（セキュアエントロピー統合版・修正版）"""
        pattern_id = str(uuid.uuid4())
        
        pattern = OscillationPatternData(
            amplitude=pattern_data.get("amplitude", 0.3),
            frequency=pattern_data.get("frequency", 0.5),
            phase=pattern_data.get("phase", 0.0),
            pink_noise_enabled=pattern_data.get("pink_noise_enabled", True),
            pink_noise_intensity=pattern_data.get("pink_noise_intensity", 0.15),
            spectral_slope=pattern_data.get("spectral_slope", -1.0),
            damping_coefficient=pattern_data.get("damping_coefficient", 0.7),
            damping_type=pattern_data.get("damping_type", "underdamped"),
            natural_frequency=pattern_data.get("natural_frequency", 2.0),
            current_velocity=pattern_data.get("current_velocity", 0.0),
            target_value=pattern_data.get("target_value", 0.0),
            chaotic_enabled=pattern_data.get("chaotic_enabled", False),
            lyapunov_exponent=pattern_data.get("lyapunov_exponent", 0.1),
            attractor_strength=pattern_data.get("attractor_strength", 0.5),
            secure_entropy_enabled=pattern_data.get("secure_entropy_enabled", True),
            secure_entropy_intensity=pattern_data.get("secure_entropy_intensity", 0.15),
            history=pattern_data.get("history", [])
        )
        
        # セキュアエントロピー情報を追加
        pattern.entropy_source_info = self.entropy_source.assess_entropy_quality()
        
        # セキュアエントロピーベースの履歴生成
        if pattern.secure_entropy_enabled:
            enhanced_history = []
            for _ in range(20):  # より長い履歴
                secure_oscillation = float(self.entropy_source.get_thermal_oscillation(pattern.amplitude))
                pink_component = float(self.pink_noise_generator.generate_secure_pink_noise())
                combined = float(secure_oscillation * 0.6 + pink_component * 0.4)
                enhanced_history.append(combined)
            pattern.history = enhanced_history
        
        # 振動パターンの埋め込み作成
        pattern_text = f"""
        Secure Enhanced Oscillation Pattern:
        Amplitude: {pattern.amplitude}
        Frequency: {pattern.frequency}
        Damping: {pattern.damping_coefficient} ({pattern.damping_type})
        Pink Noise: {pattern.pink_noise_intensity if pattern.pink_noise_enabled else 0}
        Secure Entropy: {pattern.secure_entropy_enabled}
        Entropy Source: {pattern.entropy_source_info.get('entropy_source', 'unknown')}
        Stability: {1.0 / (1.0 + np.std(pattern.history) if pattern.history else 1.0)}
        """
        embedding = self._generate_embedding(pattern_text)
        
        # メタデータの安全な構築
        metadata = filter_metadata({
            "id": str(pattern_id),
            "pattern_data": safe_json_dumps(pattern.to_dict()),
            "timestamp": pattern.timestamp.isoformat(),
            "character_id": str(self.active_character_id or ""),
            "session_id": str(self.active_session_id or "")
        })
        
        self.collections[DataType.OSCILLATION_PATTERN].add(
            embeddings=[embedding],
            documents=[pattern_text],
            metadatas=[metadata],
            ids=[pattern_id]
        )
        
        # 振動履歴を更新
        self._update_oscillation_history(pattern)
        
        logger.info(f"Added secure-enhanced oscillation pattern: {pattern_id}")
        return pattern_id
    
    def add_secure_entropy_log(self, entropy_value: int, normalized_value: float, 
                              source_type: str) -> str:
        """セキュアエントロピーログの保存（修正版）"""
        entropy_id = str(uuid.uuid4())
        quality_metrics = self.entropy_source.assess_entropy_quality()
        
        entry = SecureEntropyEntry(
            id=entropy_id,
            entropy_value=entropy_value,
            normalized_value=normalized_value,
            source_type=source_type,
            quality_metrics=quality_metrics,
            timestamp=datetime.now(),
            character_id=self.active_character_id or "",
            session_id=self.active_session_id or ""
        )
        
        # エントロピーログの埋め込み作成
        entropy_text = f"""
        Secure Entropy Log:
        Source: {source_type}
        Value: {entropy_value}
        Normalized: {normalized_value:.6f}
        Quality: {quality_metrics.get('success_rate', 0.0):.3f}
        Architecture: {quality_metrics.get('architecture', 'unknown')}
        """
        embedding = self._generate_embedding(entropy_text)
        
        # メタデータの安全な構築
        metadata = filter_metadata({
            "id": str(entropy_id),
            "entropy_value": int(entropy_value),
            "normalized_value": safe_metadata_value(normalized_value, 0.5),
            "source_type": str(source_type),
            "quality_metrics": safe_json_dumps(quality_metrics),
            "timestamp": entry.timestamp.isoformat(),
            "character_id": str(entry.character_id),
            "session_id": str(entry.session_id)
        })
        
        self.collections[DataType.SECURE_ENTROPY].add(
            embeddings=[embedding],
            documents=[entropy_text],
            metadatas=[metadata],
            ids=[entropy_id]
        )
        
        logger.info(f"Added secure entropy log: {entropy_id} (source: {source_type})")
        return entropy_id
    
    def get_secure_entropy_status(self) -> Dict[str, Any]:
        """セキュアエントロピーシステムの状態取得（新規追加）"""
        quality = self.entropy_source.assess_entropy_quality()
        
        # 最近のエントロピー履歴
        recent_entropy = []
        for _ in range(10):
            entropy_val = self.entropy_source.get_secure_entropy(4)
            normalized_val = self.entropy_source.get_normalized_entropy()
            recent_entropy.append({
                "raw_value": int(entropy_val),
                "normalized": float(normalized_val)
            })
        
        # 統計計算
        normalized_values = [e["normalized"] for e in recent_entropy]
        mean_entropy = float(np.mean(normalized_values))
        std_entropy = float(np.std(normalized_values))
        
        return {
            "entropy_source_quality": quality,
            "recent_entropy_samples": recent_entropy,
            "entropy_statistics": {
                "mean": float(mean_entropy),
                "std": float(std_entropy),
                "min": float(np.min(normalized_values)),
                "max": float(np.max(normalized_values))
            },
            "pink_noise_generator_status": {
                "octaves": self.pink_noise_generator.octaves,
                "current_key": self.pink_noise_generator.key,
                "buffer_size": len(self.pink_noise_generator.pink_values)
            },
            "system_info": {
                "architecture": self.entropy_source.arch,
                "system": self.entropy_source.system,
                "cpu_features": {
                    "rdrand": quality.get("has_rdrand", False),
                    "rdseed": quality.get("has_rdseed", False)
                },
                "security_features": {
                    "secure_mode": True,
                    "dynamic_compilation": False,
                    "pickle_usage": False,
                    "subprocess_calls": False
                }
            }
        }
    
    def get_session_state(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """セッションの現在の状態を取得（新規追加）"""
        from oscillation.metrics import calculate_oscillation_metrics
        
        sid = session_id or self.active_session_id
        if not sid:
            return {"error": "No active session"}
        
        # セッション管理システムから基本情報を取得
        session_data = self.session_manager.load_session(sid)
        if not session_data:
            return {"error": "Session not found"}
        
        # データベースから詳細情報を取得
        state = {
            "session_id": sid,
            "character_id": session_data.get("character_id"),
            "start_time": session_data.get("start_time"),
            "last_update": session_data.get("last_update"),
            "interaction_count": session_data.get("interaction_count", 0),
            "oscillation_history": session_data.get("oscillation_history", []),
            "environment_state": session_data.get("environment_state", {}),
            "internal_state": None,
            "relationship_state": None,
            "recent_conversations": [],
            "secure_entropy_status": self.get_secure_entropy_status()  # 新規追加
        }
        
        try:
            # 最新の内部状態を取得
            internal_results = self.collections[DataType.INTERNAL_STATE].get(
                where={"session_id": sid},
                include=["metadatas"],
                limit=1
            )
            if internal_results["metadatas"]:
                state["internal_state"] = internal_results["metadatas"][0]
            
            # 最新の関係性状態を取得
            relationship_results = self.collections[DataType.RELATIONSHIP].get(
                where={"session_id": sid},
                include=["metadatas"],
                limit=1
            )
            if relationship_results["metadatas"]:
                state["relationship_state"] = relationship_results["metadatas"][0]
            
            # 最近の会話を取得
            conversation_results = self.collections[DataType.CONVERSATION].get(
                where={"session_id": sid},
                include=["metadatas"],
                limit=5
            )
            state["recent_conversations"] = conversation_results["metadatas"]
            
            return state
        except Exception as e:
            logger.error(f"Error getting session state: {e}")
            return {"error": str(e)}
    
    def calculate_oscillation_metrics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """振動メトリクスを計算（外部モジュールに委譲）"""
        from oscillation.metrics import calculate_oscillation_metrics
        
        sid = session_id or self.active_session_id
        if not sid:
            return {"error": "No active session"}
        
        # 振動データが不足している場合は自動補充
        self._ensure_oscillation_data(sid, min_samples=MIN_OSCILLATION_SAMPLES)
        
        if sid not in self.oscillation_buffer:
            return {"error": "No oscillation data"}
        
        # NumPy配列の可能性があるのでリストに変換
        values = self.oscillation_buffer[sid]["values"]
        if isinstance(values, np.ndarray):
            values = values.tolist()
        else:
            # 各要素も確実にfloat型に変換
            values = [float(v) for v in values]
        
        # 外部モジュールに計算を委譲
        return calculate_oscillation_metrics(values, self.entropy_source)
    
    def add_conversation(self, user_input: str, ai_response: str, 
                        context: Dict[str, Any] = None,
                        consciousness_level: Optional[int] = None,
                        emotional_state: Optional[Dict[str, float]] = None,
                        oscillation_value: Optional[float] = None,
                        relational_distance: Optional[float] = None) -> str:
        """会話データの追加（v3.1拡張版 + セキュアエントロピー統合・修正版）"""
        conversation_id = str(uuid.uuid4())
        
        # セキュアエントロピーベースの振動値生成（指定されていない場合）
        if oscillation_value is None:
            oscillation_value = self.entropy_source.get_thermal_oscillation(0.05)
        
        # NumPy float型の可能性があるので明示的に変換
        oscillation_value = float(oscillation_value) if oscillation_value is not None else 0.0
        relational_distance = float(relational_distance) if relational_distance is not None else 0.6
        
        entry = ConversationEntry(
            id=conversation_id,
            user_input=user_input,
            ai_response=ai_response,
            timestamp=datetime.now(),
            context=context or {},
            consciousness_level=consciousness_level,
            emotional_state=emotional_state,
            character_id=self.active_character_id,
            session_id=self.active_session_id,
            oscillation_value=oscillation_value,
            relational_distance=relational_distance
        )
        
        # 埋め込み対象テキスト作成
        combined_text = f"User: {user_input}\nAI: {ai_response}"
        if consciousness_level:
            combined_text += f"\nConsciousness Level: {consciousness_level}"
        if emotional_state:
            combined_text += f"\nEmotions: {safe_json_dumps(emotional_state)}"
        if oscillation_value is not None:
            combined_text += f"\nOscillation: {oscillation_value}"
        if relational_distance is not None:
            combined_text += f"\nDistance: {relational_distance}"
        
        embedding = self._generate_embedding(combined_text)
        
        # メタデータの安全な構築（修正版）
        metadata = {
            "id": str(conversation_id),
            "user_input": str(user_input),
            "ai_response": str(ai_response),
            "timestamp": entry.timestamp.isoformat(),
            "context": safe_json_dumps(context or {}),
            "oscillation_value": safe_metadata_value(oscillation_value, 0.0),
            "relational_distance": safe_metadata_value(relational_distance, 0.6)
        }
        
        # オプション値の条件付き追加
        if consciousness_level is not None:
            metadata["consciousness_level"] = int(consciousness_level)
        
        if emotional_state is not None:
            metadata["emotional_state"] = safe_json_dumps(emotional_state)
        
        if entry.character_id is not None:
            metadata["character_id"] = str(entry.character_id)
        
        if entry.session_id is not None:
            metadata["session_id"] = str(entry.session_id)
        
        # フィルタリングを適用
        metadata = filter_metadata(metadata)
        
        self.collections[DataType.CONVERSATION].add(
            embeddings=[embedding],
            documents=[combined_text],
            metadatas=[metadata],
            ids=[conversation_id]
        )
        
        # 振動バッファに直接追加
        if self.active_session_id and oscillation_value is not None:
            buffer = self.oscillation_buffer[self.active_session_id]
            buffer["values"].append(float(oscillation_value))
            buffer["timestamps"].append(entry.timestamp)
        
        # セッションの相互作用カウントを更新
        if self.active_session_id:
            current_session = self.session_manager.load_session(self.active_session_id)
            if current_session:
                self._update_session_state(self.active_session_id, {
                    "interaction_count": current_session.get("interaction_count", 0) + 1
                })
        
        # セキュアエントロピーログの記録
        entropy_val = self.entropy_source.get_secure_entropy(4)
        normalized_val = self.entropy_source.get_normalized_entropy()
        self.add_secure_entropy_log(entropy_val, normalized_val, self.entropy_source.entropy_source)
        
        logger.info(f"Added conversation with secure entropy: {conversation_id}")
        return conversation_id
    
    def search_by_instruction(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """演技指導に基づく検索（新規追加）"""
        # 演技指導に関連するキャラクタープロファイルを検索
        query_embedding = self._generate_embedding(f"Instruction: {query}")
        
        results = self.collections[DataType.CHARACTER_PROFILE].query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        formatted_results = []
        for i in range(len(results["documents"][0])):
            metadata = results["metadatas"][0][i]
            if "instruction" in metadata:
                formatted_results.append({
                    "document": results["documents"][0][i],
                    "metadata": metadata,
                    "distance": float(results["distances"][0][i]),
                    "similarity": float(1 - results["distances"][0][i]),
                    "instruction": metadata["instruction"]
                })
        
        return formatted_results
    
    def get_character_evolution(self, character_id: Optional[str] = None, 
                              time_window: Optional[int] = None) -> Dict[str, Any]:
        """キャラクターの時間的進化を分析（新規追加）"""
        from oscillation.metrics import calculate_oscillation_metrics
        
        char_id = character_id or self.active_character_id
        if not char_id:
            return {"error": "No character specified"}
        
        evolution = {
            "character_id": char_id,
            "personality_changes": {},
            "emotional_trends": [],
            "relationship_evolution": [],
            "consciousness_progression": [],
            "oscillation_patterns": [],
            "secure_entropy_trends": []  # ハードウェアから変更
        }
        
        try:
            # 時間窓の設定
            if time_window:
                cutoff_time = datetime.now() - timedelta(hours=time_window)
            else:
                cutoff_time = datetime.min
            
            # 振動パターンの分析（修正版）
            session_ids = []
            # キャラクターに関連する全セッションを取得
            session_results = self.collections[DataType.SESSION_STATE].get(
                where={"character_id": char_id},
                include=["metadatas"]
            )
            
            for metadata in session_results["metadatas"]:
                session_ids.append(metadata["session_id"])
            
            # 振動パターンデータを統合
            all_oscillation_values = []
            for sid in session_ids:
                if sid in self.oscillation_buffer:
                    values = self.oscillation_buffer[sid]["values"]
                    # NumPy配列の場合はリストに変換
                    if isinstance(values, np.ndarray):
                        values = values.tolist()
                    all_oscillation_values.extend([float(v) for v in values])
            
            if all_oscillation_values:
                try:
                    metrics = calculate_oscillation_metrics(all_oscillation_values, self.entropy_source)
                    evolution["oscillation_patterns"] = {
                        "current_stability": metrics.get("stability", 0),
                        "pattern_length": len(all_oscillation_values),
                        "recent_values": all_oscillation_values[-10:] if len(all_oscillation_values) >= 10 else all_oscillation_values,
                        "secure_entropy_contribution": metrics.get("secure_entropy_contribution", 0),
                        "full_metrics": metrics
                    }
                except Exception as e:
                    logger.warning(f"Failed to calculate oscillation patterns: {e}")
                    evolution["oscillation_patterns"] = {
                        "error": "Calculation failed",
                        "pattern_length": len(all_oscillation_values)
                    }
            
            return evolution
            
        except Exception as e:
            logger.error(f"Error analyzing character evolution: {e}")
            return {"error": str(e)}
    
    def export_session_data(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """セッションデータのエクスポート（新規追加）"""
        sid = session_id or self.active_session_id
        if not sid:
            return {"error": "No session specified"}
        
        # 振動バッファのデータを安全に変換
        buffer_data = self.oscillation_buffer.get(sid, {"values": [], "timestamps": []})
        safe_buffer = {
            "values": [float(v) for v in buffer_data["values"]],
            "timestamps": [t.isoformat() if isinstance(t, datetime) else str(t) for t in buffer_data["timestamps"]]
        }
        
        export_data = {
            "session_id": sid,
            "export_time": datetime.now().isoformat(),
            "session_state": self.get_session_state(sid),
            "conversations": [],
            "internal_states": [],
            "relationship_states": [],
            "emotions": [],
            "memories": [],
            "secure_entropy_logs": [],  # ハードウェアから変更
            "oscillation_buffer": safe_buffer  # 振動バッファもエクスポート
        }
        
        try:
            # 各データタイプからセッション関連データを取得
            for data_type, key in [
                (DataType.CONVERSATION, "conversations"),
                (DataType.INTERNAL_STATE, "internal_states"),
                (DataType.RELATIONSHIP, "relationship_states"),
                (DataType.EMOTION, "emotions"),
                (DataType.MEMORY, "memories"),
                (DataType.SECURE_ENTROPY, "secure_entropy_logs")
            ]:
                results = self.collections[data_type].get(
                    where={"session_id": sid},
                    include=["metadatas"]
                )
                export_data[key] = results["metadatas"]
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting session data: {e}")
            return {"error": str(e)}
    
    def add_engine_state(self, engine_type: EngineType, state_data: Dict[str, Any]) -> str:
        """エンジン状態の追加（修正版）"""
        state_id = str(uuid.uuid4())
        entry = EngineStateEntry(
            id=state_id,
            engine_type=engine_type,
            state_data=state_data,
            timestamp=datetime.now(),
            character_id=self.active_character_id or "",
            session_id=self.active_session_id
        )
        
        # 状態の埋め込み作成
        state_text = f"Engine: {engine_type.value}\nState: {safe_json_dumps(state_data)}"
        embedding = self._generate_embedding(state_text)
        
        # メタデータの安全な構築
        metadata = filter_metadata({
            "id": str(state_id),
            "engine_type": str(engine_type.value),
            "state_data": safe_json_dumps(state_data),
            "timestamp": entry.timestamp.isoformat(),
            "character_id": str(entry.character_id),
            "session_id": str(entry.session_id or "")
        })
        
        self.collections[DataType.ENGINE_STATE].add(
            embeddings=[embedding],
            documents=[state_text],
            metadatas=[metadata],
            ids=[state_id]
        )
        
        logger.info(f"Added engine state: {engine_type.value} (ID: {state_id})")
        return state_id
    
    def add_memory(self, content: str, memory_type: str, relevance_score: float,
                  associated_engines: List[str] = None,
                  emotional_context: Optional[Dict[str, float]] = None) -> str:
        """記憶データの追加（拡張版・修正版）"""
        memory_id = str(uuid.uuid4())
        
        # 埋め込み作成
        memory_text = content
        if associated_engines:
            memory_text += f"\nEngines: {', '.join(associated_engines)}"
        
        embedding = self._generate_embedding(memory_text)
        
        # メタデータの安全な構築
        metadata = {
            "id": str(memory_id),
            "memory_type": str(memory_type),
            "relevance_score": safe_metadata_value(relevance_score, 0.5),
            "timestamp": datetime.now().isoformat(),
            "access_count": 0,
            "associated_engines": safe_json_dumps(associated_engines or []),
            "character_id": str(self.active_character_id or ""),
            "session_id": str(self.active_session_id or "")
        }
        
        # 感情的文脈の条件付き追加
        if emotional_context is not None:
            metadata["emotional_context"] = safe_json_dumps(emotional_context)
        
        # フィルタリングを適用
        metadata = filter_metadata(metadata)
        
        self.collections[DataType.MEMORY].add(
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata],
            ids=[memory_id]
        )
        
        logger.info(f"Added memory: {memory_id} ({memory_type})")
        return memory_id
    
    def reset_database(self):
        """データベースのリセット（警告付き）"""
        import os
        from pathlib import Path
        
        logger.warning("Resetting database...")
        
        # セッションデータをバックアップ
        backup_dir = "./session_backups"
        try:
            Path(backup_dir).mkdir(mode=0o700, exist_ok=True)  # セキュアなディレクトリ作成
            
            for session_id in self.session_manager.active_sessions:
                if self.session_manager._validate_session_id(session_id):
                    export_data = self.export_session_data(session_id)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    backup_filename = f"backup_{session_id}_{timestamp}.json"
                    backup_file = os.path.join(backup_dir, backup_filename)
                    
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        f.write(safe_json_dumps(export_data, ensure_ascii=False, indent=2))
                    
                    # セキュアな権限設定
                    os.chmod(backup_file, 0o600)
        except Exception as e:
            logger.error(f"Backup failed: {e}")
        
        # データベースリセット
        self.client.reset()
        self._init_collections()
        
        # セッション関連データをクリア
        self.oscillation_buffer.clear()
        self.session_manager.active_sessions.clear()
        self.session_manager.session_cache.clear()
        
        # ドキュメントキャッシュもクリア
        self.doc_manager.clear_cache()
        
        logger.info("Database reset completed. Backups saved to ./session_backups/")
        
