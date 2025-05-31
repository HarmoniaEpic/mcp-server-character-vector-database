"""
MCP tool handlers
"""

from typing import List, Dict, Any
from mcp.types import TextContent

from config.logging import get_logger
from core.database import VectorDatabaseManager
from core.models import EngineType
from core.utils import safe_json_dumps

logger = get_logger(__name__)


class ToolHandlers:
    """Tool handler implementations"""
    
    def __init__(self, db_manager: VectorDatabaseManager):
        """
        Initialize handlers
        
        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
    
    async def handle_start_session(self, arguments: dict) -> List[TextContent]:
        """Handle start_session tool"""
        session_id = self.db.start_session(arguments["character_id"])
        return [TextContent(
            type="text",
            text=f"新しいセッションを開始しました。セッションID: {session_id}"
        )]
    
    async def handle_resume_session(self, arguments: dict) -> List[TextContent]:
        """Handle resume_session tool"""
        success = self.db.resume_session(arguments["session_id"])
        if success:
            return [TextContent(
                type="text",
                text=f"セッションを再開しました: {arguments['session_id']}"
            )]
        else:
            return [TextContent(
                type="text",
                text="セッションの再開に失敗しました"
            )]
    
    async def handle_get_session_state(self, arguments: dict) -> List[TextContent]:
        """Handle get_session_state tool"""
        state = self.db.get_session_state(arguments.get("session_id"))
        return [TextContent(
            type="text",
            text=safe_json_dumps(state, ensure_ascii=False, indent=2)
        )]
    
    async def handle_export_session_data(self, arguments: dict) -> List[TextContent]:
        """Handle export_session_data tool"""
        export_data = self.db.export_session_data(arguments.get("session_id"))
        return [TextContent(
            type="text",
            text=safe_json_dumps(export_data, ensure_ascii=False, indent=2)
        )]
    
    async def handle_get_secure_entropy_status(self, arguments: dict) -> List[TextContent]:
        """Handle get_secure_entropy_status tool"""
        status = self.db.get_secure_entropy_status()
        return [TextContent(
            type="text",
            text=safe_json_dumps(status, ensure_ascii=False, indent=2)
        )]
    
    async def handle_test_secure_entropy(self, arguments: dict) -> List[TextContent]:
        """Handle test_secure_entropy tool"""
        sample_count = arguments.get("sample_count", 10)
        results = []
        
        for i in range(sample_count):
            entropy_val = self.db.entropy_source.get_secure_entropy(4)
            normalized_val = self.db.entropy_source.get_normalized_entropy()
            pink_noise = self.db.pink_noise_generator.generate_secure_pink_noise()
            thermal_osc = self.db.entropy_source.get_thermal_oscillation(0.1)
            
            results.append({
                "sample": i + 1,
                "raw_entropy": entropy_val,
                "normalized": normalized_val,
                "pink_noise": pink_noise,
                "thermal_oscillation": thermal_osc
            })
        
        test_result = {
            "test_samples": results,
            "entropy_quality": self.db.entropy_source.assess_entropy_quality(),
            "system_info": {
                "entropy_source": self.db.entropy_source.entropy_source,
                "has_rdrand": self.db.entropy_source.has_rdrand,
                "has_rdseed": self.db.entropy_source.has_rdseed,
                "secure_mode": True
            }
        }
        
        return [TextContent(
            type="text",
            text=safe_json_dumps(test_result, ensure_ascii=False, indent=2)
        )]
    
    async def handle_read_documentation(self, arguments: dict) -> List[TextContent]:
        """Handle read_documentation tool"""
        doc_key = arguments["document"]
        section = arguments.get("section")
        
        try:
            content = self.db.doc_manager.read_document(doc_key)
            
            if section:
                # Extract specific section
                extracted_content = self.db.doc_manager.extract_section(content, section)
                if extracted_content:
                    content = extracted_content
                else:
                    return [TextContent(
                        type="text",
                        text=f"セクション '{section}' が見つかりませんでした"
                    )]
            
            doc_filename = self.db.doc_manager.available_docs[doc_key]
            return [TextContent(
                type="text",
                text=f"=== {doc_filename} ===\n\n{content}"
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"ドキュメント読み込みエラー: {str(e)}"
            )]
    
    async def handle_search_documentation(self, arguments: dict) -> List[TextContent]:
        """Handle search_documentation tool"""
        query = arguments["query"]
        target_doc = arguments.get("document", "all")
        
        results = []
        
        if target_doc == "all":
            search_docs = list(self.db.doc_manager.available_docs.keys())
        else:
            search_docs = [target_doc]
        
        for doc_key in search_docs:
            try:
                content = self.db.doc_manager.read_document(doc_key)
                matches = self.db.doc_manager.search_in_document(content, query)
                
                if matches:
                    results.append(f"=== {self.db.doc_manager.available_docs[doc_key]} ===")
                    for match in matches:
                        results.append(f"行 {match['line_number']}: {match['matched_line']}")
                        results.append(match['context'])
                        results.append("---")
                    results.append("")
                    
            except Exception as e:
                results.append(f"検索エラー ({doc_key}): {str(e)}")
        
        if not results:
            return [TextContent(
                type="text",
                text=f"'{query}' に関する情報が見つかりませんでした"
            )]
        
        return [TextContent(
            type="text",
            text="\n".join(results)
        )]
    
    async def handle_list_available_documents(self, arguments: dict) -> List[TextContent]:
        """Handle list_available_documents tool"""
        doc_info = self.db.doc_manager.get_document_info()
        return [TextContent(
            type="text",
            text=safe_json_dumps(doc_info, ensure_ascii=False, indent=2)
        )]
    
    async def handle_add_character_profile(self, arguments: dict) -> List[TextContent]:
        """Handle add_character_profile tool"""
        result_id = self.db.add_character_profile(
            arguments["name"],
            arguments["background"],
            arguments["instruction"],
            arguments["personality_traits"],
            arguments.get("values", {}),
            arguments.get("goals", []),
            arguments.get("fears", []),
            arguments.get("existential_parameters", {}),
            arguments.get("engine_parameters", {})
        )
        return [TextContent(
            type="text",
            text=f"セキュアエントロピー統合キャラクタープロファイル（v3.1）を追加しました。ID: {result_id}"
        )]
    
    async def handle_add_internal_state(self, arguments: dict) -> List[TextContent]:
        """Handle add_internal_state tool"""
        result_id = self.db.add_internal_state(arguments["state_data"])
        return [TextContent(
            type="text",
            text=f"統合内部状態を保存しました。ID: {result_id}"
        )]
    
    async def handle_add_relationship_state(self, arguments: dict) -> List[TextContent]:
        """Handle add_relationship_state tool"""
        result_id = self.db.add_relationship_state(
            arguments["attachment_level"],
            arguments["optimal_distance"],
            arguments["current_distance"],
            arguments["paradox_tension"],
            arguments.get("oscillation_pattern"),
            arguments.get("stability_index", 0.7),
            arguments.get("dependency_risk", 0.2),
            arguments.get("growth_potential", 0.8)
        )
        return [TextContent(
            type="text",
            text=f"セキュアエントロピー強化関係性状態を保存しました。ID: {result_id}"
        )]
    
    async def handle_add_oscillation_pattern(self, arguments: dict) -> List[TextContent]:
        """Handle add_oscillation_pattern tool"""
        result_id = self.db.add_oscillation_pattern(arguments["pattern_data"])
        return [TextContent(
            type="text",
            text=f"セキュアエントロピー強化振動パターンを記録しました。ID: {result_id}"
        )]
    
    async def handle_calculate_oscillation_metrics(self, arguments: dict) -> List[TextContent]:
        """Handle calculate_oscillation_metrics tool"""
        metrics = self.db.calculate_oscillation_metrics(arguments.get("session_id"))
        return [TextContent(
            type="text",
            text=safe_json_dumps(metrics, ensure_ascii=False, indent=2)
        )]
    
    async def handle_add_conversation(self, arguments: dict) -> List[TextContent]:
        """Handle add_conversation tool"""
        result_id = self.db.add_conversation(
            arguments["user_input"],
            arguments["ai_response"],
            arguments.get("context", {}),
            arguments.get("consciousness_level"),
            arguments.get("emotional_state"),
            arguments.get("oscillation_value"),
            arguments.get("relational_distance")
        )
        return [TextContent(
            type="text",
            text=f"セキュアエントロピー強化会話データを追加しました。ID: {result_id}"
        )]
    
    async def handle_search_by_instruction(self, arguments: dict) -> List[TextContent]:
        """Handle search_by_instruction tool"""
        results = self.db.search_by_instruction(
            arguments["query"],
            arguments.get("top_k", 5)
        )
        return [TextContent(
            type="text",
            text=safe_json_dumps(results, ensure_ascii=False, indent=2)
        )]
    
    async def handle_get_character_evolution(self, arguments: dict) -> List[TextContent]:
        """Handle get_character_evolution tool"""
        evolution = self.db.get_character_evolution(
            arguments.get("character_id"),
            arguments.get("time_window")
        )
        return [TextContent(
            type="text",
            text=safe_json_dumps(evolution, ensure_ascii=False, indent=2)
        )]
    
    async def handle_add_engine_state(self, arguments: dict) -> List[TextContent]:
        """Handle add_engine_state tool"""
        engine_type = EngineType(arguments["engine_type"])
        result_id = self.db.add_engine_state(engine_type, arguments["state_data"])
        return [TextContent(
            type="text",
            text=f"エンジン状態を記録しました。ID: {result_id}"
        )]
    
    async def handle_add_memory(self, arguments: dict) -> List[TextContent]:
        """Handle add_memory tool"""
        result_id = self.db.add_memory(
            arguments["content"],
            arguments["memory_type"],
            arguments["relevance_score"],
            arguments.get("associated_engines"),
            arguments.get("emotional_context")
        )
        return [TextContent(
            type="text",
            text=f"記憶データを追加しました。ID: {result_id}"
        )]
    
    async def handle_reset_database(self, arguments: dict) -> List[TextContent]:
        """Handle reset_database tool"""
        self.db.reset_database()
        return [TextContent(
            type="text",
            text="データベースをリセットしました。セキュアバックアップは./session_backups/に保存されています。"
        )]
    
    async def handle_tool(self, name: str, arguments: dict) -> List[TextContent]:
        """
        Route tool calls to appropriate handlers
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool response
        """
        handler_map = {
            "start_session": self.handle_start_session,
            "resume_session": self.handle_resume_session,
            "get_session_state": self.handle_get_session_state,
            "export_session_data": self.handle_export_session_data,
            "get_secure_entropy_status": self.handle_get_secure_entropy_status,
            "test_secure_entropy": self.handle_test_secure_entropy,
            "read_documentation": self.handle_read_documentation,
            "search_documentation": self.handle_search_documentation,
            "list_available_documents": self.handle_list_available_documents,
            "add_character_profile": self.handle_add_character_profile,
            "add_internal_state": self.handle_add_internal_state,
            "add_relationship_state": self.handle_add_relationship_state,
            "add_oscillation_pattern": self.handle_add_oscillation_pattern,
            "calculate_oscillation_metrics": self.handle_calculate_oscillation_metrics,
            "add_conversation": self.handle_add_conversation,
            "search_by_instruction": self.handle_search_by_instruction,
            "get_character_evolution": self.handle_get_character_evolution,
            "add_engine_state": self.handle_add_engine_state,
            "add_memory": self.handle_add_memory,
            "reset_database": self.handle_reset_database,
        }
        
        handler = handler_map.get(name)
        if handler:
            try:
                return await handler(arguments)
            except Exception as e:
                logger.error(f"Tool execution error for {name}: {e}")
                return [TextContent(
                    type="text",
                    text=f"エラーが発生しました: {str(e)}"
                )]
        else:
            return [TextContent(
                type="text",
                text=f"不明なツール: {name}"
            )]
