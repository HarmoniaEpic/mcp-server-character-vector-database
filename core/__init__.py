"""
Core module for Vector Database MCP Server
"""

from .database import VectorDatabaseManager
from .exceptions import (
    VectorDatabaseError,
    SessionError,
    DocumentError,
    ValidationError,
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
    DateTimeEncoder,
    safe_json_dumps,
    safe_json_loads,
    filter_metadata,
    safe_metadata_value,
    datetime_hook,
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
    "DateTimeEncoder",
    "safe_json_dumps",
    "safe_json_loads",
    "filter_metadata",
    "safe_metadata_value",
    "datetime_hook",
]
