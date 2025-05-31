"""
Session state management
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional


@dataclass
class SessionEnvironment:
    """セッション環境状態"""
    session_duration: float = 0.0
    interaction_count: int = 0
    emotional_volatility: float = 0.3
    topic_consistency: float = 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "session_duration": self.session_duration,
            "interaction_count": self.interaction_count,
            "emotional_volatility": self.emotional_volatility,
            "topic_consistency": self.topic_consistency
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionEnvironment':
        """辞書から復元"""
        return cls(
            session_duration=data.get("session_duration", 0.0),
            interaction_count=data.get("interaction_count", 0),
            emotional_volatility=data.get("emotional_volatility", 0.3),
            topic_consistency=data.get("topic_consistency", 0.7)
        )


@dataclass
class SessionState:
    """セッション状態データ"""
    session_id: str
    character_id: str
    start_time: datetime
    last_update: datetime
    interaction_count: int = 0
    internal_state_id: str = ""
    relationship_state_id: str = ""
    oscillation_history: List[float] = field(default_factory=list)
    environment: SessionEnvironment = field(default_factory=SessionEnvironment)
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "session_id": self.session_id,
            "character_id": self.character_id,
            "start_time": self.start_time.isoformat(),
            "last_update": self.last_update.isoformat(),
            "interaction_count": self.interaction_count,
            "internal_state_id": self.internal_state_id,
            "relationship_state_id": self.relationship_state_id,
            "oscillation_history": self.oscillation_history,
            "environment_state": self.environment.to_dict(),
            "active": self.active,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionState':
        """辞書から復元"""
        from core.utils import datetime_hook
        
        # datetime文字列を変換
        processed_data = datetime_hook(data)
        
        return cls(
            session_id=processed_data["session_id"],
            character_id=processed_data["character_id"],
            start_time=processed_data["start_time"],
            last_update=processed_data["last_update"],
            interaction_count=processed_data.get("interaction_count", 0),
            internal_state_id=processed_data.get("internal_state_id", ""),
            relationship_state_id=processed_data.get("relationship_state_id", ""),
            oscillation_history=processed_data.get("oscillation_history", []),
            environment=SessionEnvironment.from_dict(
                processed_data.get("environment_state", {})
            ),
            active=processed_data.get("active", True),
            metadata=processed_data.get("metadata", {})
        )
    
    def update_interaction(self):
        """インタラクションカウントを更新"""
        self.interaction_count += 1
        self.last_update = datetime.now()
        self.environment.interaction_count = self.interaction_count
    
    def update_duration(self):
        """セッション継続時間を更新"""
        duration = (datetime.now() - self.start_time).total_seconds()
        self.environment.session_duration = duration
        self.last_update = datetime.now()
    
    def add_oscillation_value(self, value: float):
        """振動値を追加"""
        self.oscillation_history.append(value)
        # 履歴サイズ制限
        max_history = 1000
        if len(self.oscillation_history) > max_history:
            self.oscillation_history = self.oscillation_history[-max_history:]
    
    def get_recent_oscillations(self, count: int = 10) -> List[float]:
        """最近の振動値を取得"""
        return self.oscillation_history[-count:] if self.oscillation_history else []
    
    def deactivate(self):
        """セッションを非アクティブ化"""
        self.active = False
        self.last_update = datetime.now()
    
    def reactivate(self):
        """セッションを再アクティブ化"""
        self.active = True
        self.last_update = datetime.now()
