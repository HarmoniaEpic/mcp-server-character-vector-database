"""
Secure session manager
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from config.settings import SESSION_DIR, SESSION_CLEANUP_DAYS
from config.logging import get_logger
from core.exceptions import SessionError, SessionNotFoundError
from security.validators import validate_session_id
from .state import SessionState
from .storage import SessionStorage

logger = get_logger(__name__)


class SecureSessionManager:
    """セキュアセッション間状態保存を管理するクラス（pickle排除・パス検証強化版）"""
    
    def __init__(self, session_dir: str = SESSION_DIR):
        """
        初期化
        
        Args:
            session_dir: セッション保存ディレクトリ
        """
        self.storage = SessionStorage(session_dir)
        self.active_sessions: Dict[str, SessionState] = {}
        self.session_cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"SecureSessionManager initialized with directory: {session_dir}")
    
    def _validate_session_id(self, session_id: str) -> bool:
        """セッションIDの検証（内部メソッド、互換性のため維持）"""
        return validate_session_id(session_id)
    
    def create_session(self, character_id: str) -> str:
        """
        新しいセッションを作成
        
        Args:
            character_id: キャラクターID
            
        Returns:
            セッションID
        """
        session_id = str(uuid.uuid4())
        
        # セッション状態を作成
        session_state = SessionState(
            session_id=session_id,
            character_id=character_id,
            start_time=datetime.now(),
            last_update=datetime.now()
        )
        
        # メモリに保存
        self.active_sessions[session_id] = session_state
        
        # ファイルに保存
        session_data = session_state.to_dict()
        self.storage.save(session_id, session_data)
        
        # キャッシュに追加
        self.session_cache[session_id] = session_data
        
        logger.info(f"Created new session: {session_id} for character: {character_id}")
        return session_id
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        セッションを読み込み（JSONベース）
        
        Args:
            session_id: セッションID
            
        Returns:
            セッションデータまたはNone
        """
        # キャッシュチェック
        if session_id in self.session_cache:
            logger.debug(f"Loading session from cache: {session_id}")
            return self.session_cache[session_id]
        
        # ストレージから読み込み
        session_data = self.storage.load(session_id)
        if session_data:
            self.session_cache[session_id] = session_data
            
            # SessionStateオブジェクトも復元
            try:
                session_state = SessionState.from_dict(session_data)
                self.active_sessions[session_id] = session_state
            except Exception as e:
                logger.warning(f"Failed to restore SessionState object: {e}")
        
        return session_data
    
    def save_session(self, session_id: str, session_data: Dict[str, Any]):
        """
        セッションを保存（JSONベース）
        
        Args:
            session_id: セッションID
            session_data: セッションデータ
        """
        # ストレージに保存
        if self.storage.save(session_id, session_data):
            # キャッシュ更新
            self.session_cache[session_id] = session_data
            logger.debug(f"Saved session: {session_id}")
        else:
            logger.error(f"Failed to save session: {session_id}")
    
    def update_session(self, session_id: str, updates: Dict[str, Any]):
        """
        セッションを更新
        
        Args:
            session_id: セッションID
            updates: 更新する内容
        """
        session_data = self.load_session(session_id)
        if session_data:
            session_data.update(updates)
            session_data["last_update"] = datetime.now().isoformat()
            self.save_session(session_id, session_data)
            
            # SessionStateオブジェクトも更新
            if session_id in self.active_sessions:
                state = self.active_sessions[session_id]
                state.last_update = datetime.now()
                for key, value in updates.items():
                    if hasattr(state, key):
                        setattr(state, key, value)
        else:
            raise SessionNotFoundError(f"Session not found: {session_id}")
    
    def get_session_state(self, session_id: str) -> Optional[SessionState]:
        """
        SessionStateオブジェクトを取得
        
        Args:
            session_id: セッションID
            
        Returns:
            SessionStateオブジェクトまたはNone
        """
        # メモリにある場合
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # ファイルから復元
        session_data = self.load_session(session_id)
        if session_data:
            try:
                session_state = SessionState.from_dict(session_data)
                self.active_sessions[session_id] = session_state
                return session_state
            except Exception as e:
                logger.error(f"Failed to restore SessionState: {e}")
                return None
        
        return None
    
    def delete_session(self, session_id: str) -> bool:
        """
        セッションを削除
        
        Args:
            session_id: セッションID
            
        Returns:
            成功した場合True
        """
        # メモリから削除
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        # キャッシュから削除
        if session_id in self.session_cache:
            del self.session_cache[session_id]
        
        # ストレージから削除
        return self.storage.delete(session_id)
    
    def list_sessions(self) -> list[str]:
        """
        すべてのセッション一覧を取得
        
        Returns:
            セッションIDのリスト
        """
        return self.storage.list_sessions()
    
    def list_active_sessions(self) -> list[str]:
        """
        アクティブなセッション一覧を取得
        
        Returns:
            アクティブなセッションIDのリスト
        """
        active_ids = []
        
        for session_id in self.list_sessions():
            session_data = self.load_session(session_id)
            if session_data and session_data.get("active", False):
                active_ids.append(session_id)
        
        return active_ids
    
    def cleanup_old_sessions(self, days: int = SESSION_CLEANUP_DAYS) -> int:
        """
        古いセッションをクリーンアップ
        
        Args:
            days: 保持する日数
            
        Returns:
            削除したセッション数
        """
        # メモリとキャッシュもクリア
        old_sessions = []
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for session_id, state in self.active_sessions.items():
            if state.last_update.timestamp() < cutoff_time:
                old_sessions.append(session_id)
        
        for session_id in old_sessions:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            if session_id in self.session_cache:
                del self.session_cache[session_id]
        
        # ストレージからクリーンアップ
        return self.storage.cleanup_old_sessions(days)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        セッション情報を取得（詳細版）
        
        Args:
            session_id: セッションID
            
        Returns:
            セッション情報またはNone
        """
        session_data = self.load_session(session_id)
        if not session_data:
            return None
        
        # 追加情報を計算
        start_time = datetime.fromisoformat(session_data["start_time"])
        last_update = datetime.fromisoformat(session_data["last_update"])
        duration = (datetime.now() - start_time).total_seconds()
        idle_time = (datetime.now() - last_update).total_seconds()
        
        return {
            "session_id": session_id,
            "character_id": session_data.get("character_id"),
            "start_time": session_data["start_time"],
            "last_update": session_data["last_update"],
            "duration_seconds": duration,
            "idle_seconds": idle_time,
            "interaction_count": session_data.get("interaction_count", 0),
            "active": session_data.get("active", False),
            "environment_state": session_data.get("environment_state", {}),
            "oscillation_history_length": len(session_data.get("oscillation_history", []))
        }
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """
        セッションマネージャーの統計情報を取得
        
        Returns:
            統計情報
        """
        storage_stats = self.storage.get_storage_stats()
        
        return {
            "total_sessions": len(self.list_sessions()),
            "active_sessions": len(self.list_active_sessions()),
            "cached_sessions": len(self.session_cache),
            "memory_sessions": len(self.active_sessions),
            "storage_stats": storage_stats
        }
    
    def clear_cache(self):
        """キャッシュをクリア"""
        self.session_cache.clear()
        logger.info("Session cache cleared")
    
    def deactivate_session(self, session_id: str):
        """
        セッションを非アクティブ化
        
        Args:
            session_id: セッションID
        """
        self.update_session(session_id, {"active": False})
        
        if session_id in self.active_sessions:
            self.active_sessions[session_id].deactivate()
    
    def reactivate_session(self, session_id: str):
        """
        セッションを再アクティブ化
        
        Args:
            session_id: セッションID
        """
        self.update_session(session_id, {"active": True})
        
        if session_id in self.active_sessions:
            self.active_sessions[session_id].reactivate()
