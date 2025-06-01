"""
Monitor server launcher
"""

import sys
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config.logging import setup_logging
from core.database import VectorDatabaseManager
from monitor.gradio_app import MonitorApp

# Setup logging
logger = setup_logging()


def main():
    """Launch monitor server"""
    logger.info("Starting MCP Server Monitor...")
    
    # Initialize database manager
    db_manager = VectorDatabaseManager()
    
    # Create monitor app
    app = MonitorApp(db_manager)
    
    # Launch
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=True,
        favicon_path=None
    )


if __name__ == "__main__":
    main()
