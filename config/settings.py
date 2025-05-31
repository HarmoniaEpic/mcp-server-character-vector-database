"""
Global settings and configuration management
"""

import os
from pathlib import Path
from typing import Optional

# Try to load from .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Base paths
BASE_DIR = Path(__file__).parent.parent
PROJECT_ROOT = BASE_DIR.parent

# Database paths
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", str(BASE_DIR / "chroma_db"))
SESSION_DIR = os.getenv("SESSION_DIR", str(BASE_DIR / "session_states"))

# Document paths
DOCS_DIR = Path(os.getenv("DOCS_DIR", str(PROJECT_ROOT)))

# Model settings
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Security settings
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))  # 10MB
SESSION_CLEANUP_DAYS = int(os.getenv("SESSION_CLEANUP_DAYS", "30"))

# Oscillation settings
OSCILLATION_BUFFER_SIZE = int(os.getenv("OSCILLATION_BUFFER_SIZE", "1000"))
MIN_OSCILLATION_SAMPLES = int(os.getenv("MIN_OSCILLATION_SAMPLES", "5"))

# Entropy settings
ENTROPY_BUFFER_SIZE = int(os.getenv("ENTROPY_BUFFER_SIZE", "1000"))

# MCP Server settings
MCP_SERVER_NAME = os.getenv("MCP_SERVER_NAME", "vector-database-server-v31-secure-entropy-docs-oscillation-fixed")
MCP_SERVER_VERSION = os.getenv("MCP_SERVER_VERSION", "3.1.4-complete-fixed")

# Available documents configuration
AVAILABLE_DOCUMENTS = {
    "engine_system": os.getenv("ENGINE_SYSTEM_DOC", "unified-inner-engine-v3.1.txt"),
    "manual": os.getenv("MANUAL_DOC", "unified-engine-mcp-manual.md")
}

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
LOG_FILE = os.getenv("LOG_FILE", None)

# Test mode settings
TEST_MODE = os.getenv("TEST_MODE", "false").lower() in ("true", "1", "yes", "on")

# Performance settings
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
CHROMADB_PERSIST_INTERVAL = int(os.getenv("CHROMADB_PERSIST_INTERVAL", "100"))

# Development settings
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on")

def get_config_summary() -> dict:
    """Get a summary of current configuration"""
    return {
        "base_dir": str(BASE_DIR),
        "chroma_db_path": CHROMA_DB_PATH,
        "session_dir": SESSION_DIR,
        "docs_dir": str(DOCS_DIR),
        "embedding_model": EMBEDDING_MODEL,
        "max_file_size": MAX_FILE_SIZE,
        "session_cleanup_days": SESSION_CLEANUP_DAYS,
        "oscillation_buffer_size": OSCILLATION_BUFFER_SIZE,
        "min_oscillation_samples": MIN_OSCILLATION_SAMPLES,
        "entropy_buffer_size": ENTROPY_BUFFER_SIZE,
        "log_level": LOG_LEVEL,
        "debug": DEBUG,
        "available_documents": AVAILABLE_DOCUMENTS,
    }
