"""
Data models and enumerations for Vector Database MCP Server
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


# ========================================================
# Enumerations
# ========================================================

class DataType(Enum):
    """データタイプの分類（v3.1拡張版）"""
    CONVERSATION = "conversation"
    MEMORY = "memory"
    EXPERIENCE = "experience"
    PERSONALITY = "personality"
    MOTIVATION = "motivation"
    CHARACTER_PROFILE = "character_profile"
    ENGINE_STATE = "engine_state"
    GLOBAL_CONTEXT = "global_context"
    QUALIA = "qualia"
    EMOTION = "emotion"
    EMPATHY = "empathy"
    CONFLICT = "conflict"
    RELATIONSHIP = "relationship"
    EXISTENTIAL_NEED = "existential_need"
    GROWTH_WISH = "growth_wish"
    OSCILLATION_PATTERN = "oscillation_pattern"
    SESSION_STATE = "session_state"
    INTERNAL_STATE = "internal_state"
    SECURE_ENTROPY = "secure_entropy"


class BasicEmotion(Enum):
    """8つの基本感情（Plutchikの感情の輪）"""
    JOY = "joy"
    TRUST = "trust"
    FEAR = "fear"
    SURPRISE = "surprise"
    SADNESS = "sadness"
    DISGUST = "disgust"
    ANGER = "anger"
    ANTICIPATION = "anticipation"


class ConsciousnessLevel(Enum):
    """意識レベル"""
    PERCEPTUAL = 1
    SITUATIONAL = 2
    SELF_AWARE = 3
    META_CONSCIOUS = 4


class EngineType(Enum):
    """エンジンタイプ（v3.1拡張版）"""
    CONSCIOUSNESS = "consciousness"
    QUALIA = "qualia"
    EMOTION = "emotion"
    EMPATHY = "empathy"
    MOTIVATION = "motivation"
    CURIOSITY = "curiosity"
    CONFLICT = "conflict"
    RELATIONSHIP = "relationship"
    EXISTENTIAL_NEED = "existential_need"
    GROWTH_WISH = "growth_wish"


# ========================================================
# Data Classes
# ========================================================

@dataclass
class CharacterProfileEntry:
    """完全なキャラクタープロファイル（v3.1拡張版）"""
    id: str
    name: str
    background: str
    instruction: str  # 演技指導変数（新規追加）
    personality_traits: Dict[str, float]  # Big5
    values: Dict[str, float]
    goals: List[str]
    fears: List[str]
    existential_parameters: Dict[str, float]  # 存在論的パラメータ（新規追加）
    engine_parameters: Dict[str, Dict[str, Any]]
    timestamp: datetime
    version: str = "3.1"


@dataclass
class EngineStateEntry:
    """エンジン状態エントリ（拡張版）"""
    id: str
    engine_type: EngineType
    state_data: Dict[str, Any]
    timestamp: datetime
    character_id: str
    session_id: Optional[str] = None


@dataclass
class InternalStateEntry:
    """統合内部状態エントリ（新規追加）"""
    id: str
    timestamp: datetime
    consciousness_state: Dict[str, Any]
    qualia_state: Dict[str, Any]
    emotion_state: Dict[str, Any]
    empathy_state: Dict[str, Any]
    motivation_state: Dict[str, Any]
    curiosity_state: Dict[str, Any]
    conflict_state: Dict[str, Any]
    relationship_state: Dict[str, Any]
    existential_need_state: Dict[str, Any]
    growth_wish_state: Dict[str, Any]
    overall_energy: float
    cognitive_load: float
    emotional_tone: str
    attention_focus: Optional[Dict[str, Any]]
    relational_distance: float
    paradox_tension: float
    oscillation_stability: float
    character_id: str
    session_id: str


@dataclass
class RelationshipStateEntry:
    """関係性状態エントリ（新規追加）"""
    id: str
    attachment_level: float
    optimal_distance: float
    current_distance: float
    paradox_tension: float
    oscillation_pattern: Any  # OscillationPatternData
    stability_index: float
    dependency_risk: float
    growth_potential: float
    timestamp: datetime
    character_id: str
    session_id: str


@dataclass
class SessionStateEntry:
    """セッション状態エントリ（新規追加）"""
    id: str
    session_id: str
    character_id: str
    start_time: datetime
    last_update: datetime
    interaction_count: int
    internal_state_id: str
    relationship_state_id: str
    oscillation_history: List[float]
    environment_state: Dict[str, Any]
    active: bool


@dataclass
class ConversationEntry:
    """会話エントリ（v3.1拡張版）"""
    id: str
    user_input: str
    ai_response: str
    timestamp: datetime
    context: Dict[str, Any]
    sentiment: Optional[float] = None
    importance: Optional[float] = None
    consciousness_level: Optional[int] = None
    emotional_state: Optional[Dict[str, float]] = None
    character_id: Optional[str] = None
    session_id: Optional[str] = None
    oscillation_value: Optional[float] = None  # 新規追加
    relational_distance: Optional[float] = None  # 新規追加


@dataclass
class SecureEntropyEntry:
    """セキュアエントロピーエントリ（新規追加）"""
    id: str
    entropy_value: int
    normalized_value: float
    source_type: str  # "secure_combined", "os_entropy"
    quality_metrics: Dict[str, Any]
    timestamp: datetime
    character_id: str
    session_id: str


@dataclass
class MemoryEntry:
    """記憶エントリ"""
    id: str
    content: str
    memory_type: str  # episodic, semantic, procedural
    relevance_score: float
    timestamp: datetime
    access_count: int = 0
    associated_engines: List[str] = field(default_factory=list)
    emotional_context: Optional[Dict[str, float]] = None
    character_id: Optional[str] = None
    session_id: Optional[str] = None
