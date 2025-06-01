"""
Core module for Vector Database MCP Server
"""

from .database import VectorDatabaseManager
from .exceptions import (
    VectorDatabaseError,
    SessionError,
    DocumentError,
    ValidationError,
    CharacterNotFoundError,  # 追加
)
from .models import (
    DataType,
    BasicEmotion,
    ConsciousnessLevel,
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
    EnhancedJSONEncoder,  # DateTimeEncoder から変更
    safe_json_dumps,
    safe_json_loads,
    filter_metadata,
    safe_metadata_value,
    datetime_hook,
    truncate_text,  # 追加
    merge_dicts,  # 追加
    get_nested_value,  # 追加
    set_nested_value,  # 追加
    format_timestamp,  # 追加
    clean_for_json,  # 追加
)

__all__ = [
    # Database
    "VectorDatabaseManager",
    
    # Exceptions
    "VectorDatabaseError",
    "SessionError",
    "DocumentError",
    "ValidationError",
    
    # Models - Enums
    "DataType",
    "BasicEmotion",
    "ConsciousnessLevel",
    "EngineType",
    
    # Models - Data classes
    "CharacterProfileEntry",
    "EngineStateEntry",
    "InternalStateEntry",
    "RelationshipStateEntry",
    "SessionStateEntry",
    "ConversationEntry",
    "SecureEntropyEntry",
    
    # Utils
    "EnhancedJSONEncoder",
    "safe_json_dumps",
    "safe_json_loads",
    "filter_metadata",
    "safe_metadata_value",
    "datetime_hook",
]
