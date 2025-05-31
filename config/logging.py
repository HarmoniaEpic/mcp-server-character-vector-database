"""
Logging configuration
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from .settings import LOG_LEVEL, LOG_FORMAT, LOG_FILE, DEBUG


def setup_logging(
    name: Optional[str] = None,
    level: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup logging configuration
    
    Args:
        name: Logger name (default: root logger)
        level: Log level (default: from settings)
        log_file: Log file path (default: from settings)
    
    Returns:
        Configured logger
    """
    # Get logger
    logger = logging.getLogger(name)
    
    # Set level
    log_level = getattr(logging, (level or LOG_LEVEL).upper())
    logger.setLevel(log_level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    file_path = log_file or LOG_FILE
    if file_path:
        try:
            # Create log directory if needed
            log_path = Path(file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create file handler
            file_handler = logging.FileHandler(file_path, encoding='utf-8')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Failed to create log file handler: {e}")
    
    # Debug mode adjustments
    if DEBUG:
        logger.setLevel(logging.DEBUG)
        # Add more detailed formatter for debug
        debug_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(filename)s:%(lineno)d - %(funcName)s() - %(message)s'
        )
        for handler in logger.handlers:
            handler.setFormatter(debug_formatter)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Configure logging for common libraries
def configure_library_logging():
    """Configure logging levels for common libraries"""
    # Reduce noise from libraries
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Enable debug for our modules in debug mode
    if DEBUG:
        logging.getLogger("vector_database_mcp").setLevel(logging.DEBUG)


# Initialize library logging configuration
configure_library_logging()
