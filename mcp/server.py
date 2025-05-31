"""
MCP server implementation
"""

from typing import List

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from config.settings import MCP_SERVER_NAME, MCP_SERVER_VERSION
from config.logging import get_logger
from core.database import VectorDatabaseManager
from .tools import get_tool_definitions
from .handlers import ToolHandlers

logger = get_logger(__name__)


class VectorDatabaseMCPServer:
    """ベクトルデータベース MCP サーバー（v3.1対応版 + セキュアエントロピー統合・修正版 + ドキュメント統合版 + 振動メトリクス修正版）"""
    
    def __init__(self):
        """Initialize MCP server"""
        self.db = VectorDatabaseManager()
        self.server = Server(MCP_SERVER_NAME)
        self.handlers = ToolHandlers(self.db)
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup MCP tools"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools"""
            return get_tool_definitions()
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> List[TextContent]:
            """Execute tool call"""
            return await self.handlers.handle_tool(name, arguments)
    
    async def run(self):
        """Run MCP server"""
        logger.info(f"Starting {MCP_SERVER_NAME} version {MCP_SERVER_VERSION}...")
        logger.info("Unified Inner Engine System v3.1 対応版 - セキュアエントロピー統合版 - ChromaDBメタデータ処理エラー修正版 - ドキュメント読み込み機能統合版 - 振動メトリクス問題修正版")
        logger.info("Security Features: No dynamic compilation, No pickle, No subprocess")
        logger.info("Document Features: Secure file reading, Section extraction, Content search")
        logger.info("Oscillation Metrics: Fixed session continuity, Buffer restoration, Data sufficiency handling")
        
        async with stdio_server() as streams:
            await self.server.run(
                streams[0], 
                streams[1], 
                InitializationOptions(
                    server_name=MCP_SERVER_NAME,
                    server_version=MCP_SERVER_VERSION,
                    capabilities={}
                )
            )
