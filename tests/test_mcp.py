"""
Tests for MCP server and tools
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from vdb_server.server import VectorDatabaseMCPServer
from vdb_server.tools import get_tool_definitions
from vdb_server.handlers import ToolHandlers
from mcp.types import TextContent  # これはMCPパッケージからのインポートなのでそのまま
from core.models import EngineType


class TestToolDefinitions:
    """Test MCP tool definitions"""
    
    def test_get_tool_definitions(self):
        """Test getting tool definitions"""
        tools = get_tool_definitions()
        
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        # Check required tools exist
        tool_names = [tool.name for tool in tools]
        required_tools = [
            "start_session",
            "resume_session",
            "get_session_state",
            "export_session_data",
            "get_secure_entropy_status",
            "test_secure_entropy",
            "read_documentation",
            "search_documentation",
            "list_available_documents",
            "add_character_profile",
            "add_internal_state",
            "add_relationship_state",
            "add_oscillation_pattern",
            "calculate_oscillation_metrics",
            "add_conversation",
            "search_by_instruction",
            "get_character_evolution",
            "add_engine_state",
            "add_memory",
            "reset_database"
        ]
        
        for required_tool in required_tools:
            assert required_tool in tool_names
    
    def test_tool_schema_validation(self):
        """Test tool schema definitions"""
        tools = get_tool_definitions()
        
        for tool in tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'inputSchema')
            
            # Check input schema
            schema = tool.inputSchema
            assert isinstance(schema, dict)
            assert schema.get('type') == 'object'
            assert 'properties' in schema
            
            # Required fields should be valid
            if 'required' in schema:
                assert isinstance(schema['required'], list)
                for required_field in schema['required']:
                    assert required_field in schema['properties']


class TestToolHandlers:
    """Test MCP tool handlers"""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager"""
        mock = MagicMock()
        mock.entropy_source = MagicMock()
        mock.pink_noise_generator = MagicMock()
        mock.doc_manager = MagicMock()
        return mock
    
    @pytest.fixture
    def handlers(self, mock_db_manager):
        """Create handlers with mock DB"""
        return ToolHandlers(mock_db_manager)
    
    @pytest.mark.asyncio
    async def test_handle_start_session(self, handlers, mock_db_manager):
        """Test start session handler"""
        mock_db_manager.start_session.return_value = "session-123"
        
        result = await handlers.handle_start_session({"character_id": "char-456"})
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "session-123" in result[0].text
        mock_db_manager.start_session.assert_called_once_with("char-456")
    
    @pytest.mark.asyncio
    async def test_handle_resume_session(self, handlers, mock_db_manager):
        """Test resume session handler"""
        mock_db_manager.resume_session.return_value = True
        
        result = await handlers.handle_resume_session({"session_id": "session-123"})
        
        assert len(result) == 1
        assert "再開しました" in result[0].text
        
        # Test failure case
        mock_db_manager.resume_session.return_value = False
        result = await handlers.handle_resume_session({"session_id": "bad-session"})
        assert "失敗しました" in result[0].text
    
    @pytest.mark.asyncio
    async def test_handle_get_session_state(self, handlers, mock_db_manager):
        """Test get session state handler"""
        mock_state = {
            "session_id": "session-123",
            "character_id": "char-456",
            "interaction_count": 5
        }
        mock_db_manager.get_session_state.return_value = mock_state
        
        result = await handlers.handle_get_session_state({})
        
        assert len(result) == 1
        assert "session-123" in result[0].text
        assert "char-456" in result[0].text
    
    @pytest.mark.asyncio
    async def test_handle_test_secure_entropy(self, handlers, mock_db_manager):
        """Test secure entropy test handler"""
        mock_db_manager.entropy_source.get_secure_entropy.return_value = 12345
        mock_db_manager.entropy_source.get_normalized_entropy.return_value = 0.5
        mock_db_manager.pink_noise_generator.generate_secure_pink_noise.return_value = 0.1
        mock_db_manager.entropy_source.get_thermal_oscillation.return_value = 0.05
        mock_db_manager.entropy_source.assess_entropy_quality.return_value = {
            "entropy_source": "secure_combined",
            "success_rate": 1.0
        }
        mock_db_manager.entropy_source.entropy_source = "secure_combined"
        mock_db_manager.entropy_source.has_rdrand = False
        mock_db_manager.entropy_source.has_rdseed = False
        
        result = await handlers.handle_test_secure_entropy({"sample_count": 2})
        
        assert len(result) == 1
        data = result[0].text
        assert "test_samples" in data
        assert "entropy_quality" in data
    
    @pytest.mark.asyncio
    async def test_handle_read_documentation(self, handlers, mock_db_manager):
        """Test read documentation handler"""
        mock_db_manager.doc_manager.read_document.return_value = "Document content"
        mock_db_manager.doc_manager.available_docs = {"engine_system": "engine.txt"}
        
        result = await handlers.handle_read_documentation({"document": "engine_system"})
        
        assert len(result) == 1
        assert "Document content" in result[0].text
        assert "engine.txt" in result[0].text
        
        # Test with section
        mock_db_manager.doc_manager.extract_section.return_value = "Section content"
        result = await handlers.handle_read_documentation({
            "document": "engine_system",
            "section": "概要"
        })
        assert "Section content" in result[0].text
    
    @pytest.mark.asyncio
    async def test_handle_search_documentation(self, handlers, mock_db_manager):
        """Test search documentation handler"""
        mock_db_manager.doc_manager.available_docs = {"doc1": "doc1.txt"}
        mock_db_manager.doc_manager.read_document.return_value = "Content with test word"
        mock_db_manager.doc_manager.search_in_document.return_value = [
            {
                "line_number": 1,
                "matched_line": "test word",
                "context": "Context"
            }
        ]
        
        result = await handlers.handle_search_documentation({
            "query": "test",
            "document": "doc1"
        })
        
        assert len(result) == 1
        assert "doc1.txt" in result[0].text
        assert "行 1" in result[0].text
    
    @pytest.mark.asyncio
    async def test_handle_add_character_profile(self, handlers, mock_db_manager):
        """Test add character profile handler"""
        mock_db_manager.add_character_profile.return_value = "profile-123"
        
        args = {
            "name": "TestChar",
            "background": "Test background",
            "instruction": "Test instruction",
            "personality_traits": {
                "openness": 0.8,
                "conscientiousness": 0.7,
                "extraversion": 0.6,
                "agreeableness": 0.9,
                "neuroticism": 0.3
            }
        }
        
        result = await handlers.handle_add_character_profile(args)
        
        assert len(result) == 1
        assert "profile-123" in result[0].text
        assert "v3.1" in result[0].text
    
    @pytest.mark.asyncio
    async def test_handle_add_conversation(self, handlers, mock_db_manager):
        """Test add conversation handler"""
        mock_db_manager.add_conversation.return_value = "conv-123"
        
        args = {
            "user_input": "Hello",
            "ai_response": "Hi there!",
            "context": {"topic": "greeting"}
        }
        
        result = await handlers.handle_add_conversation(args)
        
        assert len(result) == 1
        assert "conv-123" in result[0].text
    
    @pytest.mark.asyncio
    async def test_handle_calculate_oscillation_metrics(self, handlers, mock_db_manager):
        """Test calculate oscillation metrics handler"""
        mock_metrics = {
            "data_level": "full",
            "total_samples": 100,
            "mean": 0.5,
            "stability": 0.8
        }
        mock_db_manager.calculate_oscillation_metrics.return_value = mock_metrics
        
        result = await handlers.handle_calculate_oscillation_metrics({})
        
        assert len(result) == 1
        assert "data_level" in result[0].text
        assert "stability" in result[0].text
    
    @pytest.mark.asyncio
    async def test_handle_add_engine_state(self, handlers, mock_db_manager):
        """Test add engine state handler"""
        mock_db_manager.add_engine_state.return_value = "state-123"
        
        args = {
            "engine_type": "consciousness",
            "state_data": {"level": 3}
        }
        
        result = await handlers.handle_add_engine_state(args)
        
        assert len(result) == 1
        assert "state-123" in result[0].text
        mock_db_manager.add_engine_state.assert_called_once_with(
            EngineType.CONSCIOUSNESS,
            {"level": 3}
        )
    
    @pytest.mark.asyncio
    async def test_handle_reset_database(self, handlers, mock_db_manager):
        """Test reset database handler"""
        result = await handlers.handle_reset_database({})
        
        assert len(result) == 1
        assert "リセットしました" in result[0].text
        assert "session_backups" in result[0].text
        mock_db_manager.reset_database.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_tool_unknown(self, handlers):
        """Test handling unknown tool"""
        result = await handlers.handle_tool("unknown_tool", {})
        
        assert len(result) == 1
        assert "不明なツール" in result[0].text
    
    @pytest.mark.asyncio
    async def test_handle_tool_error(self, handlers, mock_db_manager):
        """Test error handling in tool execution"""
        mock_db_manager.start_session.side_effect = Exception("Test error")
        
        result = await handlers.handle_tool("start_session", {"character_id": "test"})
        
        assert len(result) == 1
        assert "エラーが発生しました" in result[0].text
        assert "Test error" in result[0].text


class TestVectorDatabaseMCPServer:
    """Test MCP server"""
    
    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test server initialization"""
        server = VectorDatabaseMCPServer()
        
        assert server.db is not None
        assert server.server is not None
        assert server.handlers is not None
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test list tools functionality"""
        server = VectorDatabaseMCPServer()
        
        # Get the list_tools handler
        list_tools_handler = None
        for handler in server.server._request_handlers.values():
            if hasattr(handler, '__name__') and handler.__name__ == 'list_tools':
                list_tools_handler = handler
                break
        
        assert list_tools_handler is not None
        
        # Call the handler
        tools = await list_tools_handler()
        assert isinstance(tools, list)
        assert len(tools) > 0
    
    @pytest.mark.asyncio
    async def test_call_tool(self):
        """Test call tool functionality"""
        server = VectorDatabaseMCPServer()
        
        # Mock the database manager
        with patch.object(server.db, 'start_session', return_value='session-123'):
            # Get the call_tool handler
            call_tool_handler = None
            for handler in server.server._request_handlers.values():
                if hasattr(handler, '__name__') and handler.__name__ == 'call_tool':
                    call_tool_handler = handler
                    break
            
            assert call_tool_handler is not None
            
            # Call the handler
            result = await call_tool_handler('start_session', {'character_id': 'test-char'})
            assert isinstance(result, list)
            assert len(result) > 0
            assert isinstance(result[0], TextContent)
    
    @pytest.mark.asyncio
    async def test_server_run(self):
        """Test server run method (mock stdio)"""
        server = VectorDatabaseMCPServer()
        
        # Mock the stdio_server context manager
        mock_streams = (AsyncMock(), AsyncMock())
        
        with patch('mcp.server.stdio_server') as mock_stdio:
            mock_stdio.return_value.__aenter__.return_value = mock_streams
            mock_stdio.return_value.__aexit__.return_value = None
            
            # Mock the server.run to complete immediately
            with patch.object(server.server, 'run', new_callable=AsyncMock) as mock_run:
                await server.run()
                
                mock_run.assert_called_once()
                # Check initialization options
                call_args = mock_run.call_args[0]
                init_options = call_args[2]
                assert init_options.server_name == server.server.name
                assert init_options.server_version is not None


class TestMCPIntegration:
    """Test MCP integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_full_session_workflow(self):
        """Test complete session workflow through MCP"""
        server = VectorDatabaseMCPServer()
        
        # 1. Add character profile
        profile_result = await server.handlers.handle_add_character_profile({
            "name": "TestChar",
            "background": "Test background",
            "instruction": "Be helpful",
            "personality_traits": {
                "openness": 0.8,
                "conscientiousness": 0.7,
                "extraversion": 0.6,
                "agreeableness": 0.9,
                "neuroticism": 0.3
            }
        })
        
        assert len(profile_result) == 1
        assert "ID:" in profile_result[0].text
        
        # Extract character ID from response
        import re
        match = re.search(r'ID: ([\w-]+)', profile_result[0].text)
        assert match is not None
        character_id = match.group(1)
        
        # 2. The session should be auto-started, get its state
        state_result = await server.handlers.handle_get_session_state({})
        assert len(state_result) == 1
        
        # 3. Add conversation
        conv_result = await server.handlers.handle_add_conversation({
            "user_input": "Hello!",
            "ai_response": "Hi there! How can I help you?",
            "consciousness_level": 2
        })
        assert len(conv_result) == 1
        
        # 4. Calculate oscillation metrics
        metrics_result = await server.handlers.handle_calculate_oscillation_metrics({})
        assert len(metrics_result) == 1
        assert "data_level" in metrics_result[0].text
        
        # 5. Export session data
        export_result = await server.handlers.handle_export_session_data({})
        assert len(export_result) == 1
        assert "session_id" in export_result[0].text
    
    @pytest.mark.asyncio
    async def test_documentation_workflow(self):
        """Test documentation access workflow"""
        server = VectorDatabaseMCPServer()
        
        # Mock document manager
        server.db.doc_manager.available_docs = {
            "engine_system": "engine.txt",
            "manual": "manual.md"
        }
        server.db.doc_manager.get_document_info.return_value = {
            "available_documents": {
                "engine_system": {"accessible": True},
                "manual": {"accessible": True}
            }
        }
        
        # 1. List available documents
        list_result = await server.handlers.handle_list_available_documents({})
        assert len(list_result) == 1
        assert "available_documents" in list_result[0].text
        
        # 2. Read a document
        server.db.doc_manager.read_document.return_value = "# Engine System\n\nContent here"
        read_result = await server.handlers.handle_read_documentation({
            "document": "engine_system"
        })
        assert len(read_result) == 1
        assert "Engine System" in read_result[0].text
        
        # 3. Search in documents
        server.db.doc_manager.search_in_document.return_value = [
            {
                "line_number": 1,
                "matched_line": "Engine System",
                "context": "# Engine System\n\nContent"
            }
        ]
        search_result = await server.handlers.handle_search_documentation({
            "query": "Engine",
            "document": "engine_system"
        })
        assert len(search_result) == 1
        assert "Engine" in search_result[0].text
    
    @pytest.mark.asyncio
    async def test_entropy_testing_workflow(self):
        """Test entropy testing workflow"""
        server = VectorDatabaseMCPServer()
        
        # 1. Get entropy status
        status_result = await server.handlers.handle_get_secure_entropy_status({})
        assert len(status_result) == 1
        assert "entropy_source_quality" in status_result[0].text
        
        # 2. Test entropy generation
        test_result = await server.handlers.handle_test_secure_entropy({
            "sample_count": 5
        })
        assert len(test_result) == 1
        assert "test_samples" in test_result[0].text
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        """Test error handling in various scenarios"""
        server = VectorDatabaseMCPServer()
        
        # 1. Invalid session ID
        result = await server.handlers.handle_resume_session({
            "session_id": "invalid-not-uuid"
        })
        assert len(result) == 1
        # Should handle gracefully
        
        # 2. Non-existent document
        server.db.doc_manager.read_document.side_effect = Exception("Document not found")
        result = await server.handlers.handle_read_documentation({
            "document": "nonexistent"
        })
        assert len(result) == 1
        assert "エラー" in result[0].text
        
        # 3. Invalid tool arguments
        result = await server.handlers.handle_tool("add_conversation", {})
        assert len(result) == 1
        assert "エラー" in result[0].text
