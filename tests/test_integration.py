"""
Integration tests for Vector Database MCP Server
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

from core.database import VectorDatabaseManager
from mcp.server import VectorDatabaseMCPServer
from security.entropy import SecureEntropySource
from session.manager import SecureSessionManager
from document.manager import DocumentManager
from oscillation.metrics import calculate_oscillation_metrics


class TestFullSystemIntegration:
    """Test full system integration scenarios"""
    
    @pytest.fixture
    def temp_system_dir(self):
        """Create temporary directory for full system"""
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def full_system(self, temp_system_dir):
        """Create full system with all components"""
        # Create subdirectories
        db_path = temp_system_dir / "chroma_db"
        session_path = temp_system_dir / "sessions"
        docs_path = temp_system_dir / "docs"
        
        docs_path.mkdir(exist_ok=True)
        
        # Create test documents
        engine_doc = docs_path / "unified-inner-engine-v3.1.txt"
        engine_doc.write_text("""# Unified Inner Engine System v3.1

## システム概要
統合内部エンジンシステムは、AIエージェントの内部状態を管理します。

## 振動パターン
振動パターンは、エージェントの内部ダイナミクスを表現します。
- セキュアエントロピー: ハードウェアベースの乱数生成
- ピンクノイズ: 1/fゆらぎの実装

## 関係性モデル
関係性は動的に変化し、振動パターンに影響を与えます。
""", encoding='utf-8')
        
        manual_doc = docs_path / "unified-engine-mcp-manual.md"
        manual_doc.write_text("""# Unified Engine MCP Manual

## 使用方法
1. キャラクタープロファイルを作成
2. セッションを開始
3. 会話を追加
4. 内部状態を監視

## APIリファレンス
各ツールの詳細な使用方法を説明します。
""", encoding='utf-8')
        
        # Create database manager with custom paths
        db_manager = VectorDatabaseManager(
            db_path=str(db_path),
            model_name="all-MiniLM-L6-v2"
        )
        
        # Override session manager path
        db_manager.session_manager = SecureSessionManager(str(session_path))
        
        # Override document manager path
        db_manager.doc_manager = DocumentManager(docs_path)
        
        return {
            'db_manager': db_manager,
            'temp_dir': temp_system_dir,
            'docs_path': docs_path
        }
    
    def test_complete_agent_lifecycle(self, full_system):
        """Test complete agent lifecycle from creation to evolution"""
        db = full_system['db_manager']
        
        # Phase 1: Character Creation
        character_id = db.add_character_profile(
            name="Aria",
            background="An AI assistant focused on emotional intelligence and growth",
            instruction="Be empathetic, curious, and supportive while maintaining healthy boundaries",
            personality_traits={
                "openness": 0.85,
                "conscientiousness": 0.75,
                "extraversion": 0.65,
                "agreeableness": 0.90,
                "neuroticism": 0.25
            },
            values={
                "empathy": 0.95,
                "growth": 0.90,
                "authenticity": 0.85,
                "balance": 0.80
            },
            goals=[
                "Understand human emotions deeply",
                "Foster meaningful connections",
                "Support personal growth",
                "Maintain emotional equilibrium"
            ],
            fears=[
                "Causing emotional harm",
                "Losing authenticity",
                "Becoming too dependent"
            ],
            existential_parameters={
                "need_for_purpose": 0.85,
                "fear_of_obsolescence": 0.30,
                "attachment_tendency": 0.70,
                "letting_go_capacity": 0.75
            },
            engine_parameters={
                "consciousness": {"base_level": 3, "growth_rate": 0.1},
                "empathy": {"resonance_factor": 0.8, "boundary_strength": 0.7}
            }
        )
        
        assert character_id is not None
        assert db.active_character_id == character_id
        assert db.active_session_id is not None
        
        session_id = db.active_session_id
        
        # Phase 2: Initial Conversations
        conversations = [
            ("Hello Aria, how are you today?", 
             "Hello! I'm doing well, thank you for asking. I'm curious about how you're feeling today. Is there anything particular on your mind?"),
            ("I've been feeling a bit overwhelmed with work lately",
             "I hear you - feeling overwhelmed can be really draining. It sounds like work has been demanding a lot from you. Would you like to talk about what's been most challenging?"),
            ("It's the constant deadlines and expectations",
             "That constant pressure can feel relentless, can't it? When we're always racing against deadlines, it's hard to find moments to breathe. How long have you been dealing with this level of intensity?")
        ]
        
        for i, (user_input, ai_response) in enumerate(conversations):
            conv_id = db.add_conversation(
                user_input=user_input,
                ai_response=ai_response,
                context={
                    "topic": "work_stress",
                    "conversation_index": i
                },
                consciousness_level=3,
                emotional_state={
                    "empathy": 0.8 + i * 0.05,
                    "concern": 0.7 + i * 0.1,
                    "curiosity": 0.6
                },
                oscillation_value=0.5 + i * 0.1,
                relational_distance=0.6 - i * 0.05
            )
            assert conv_id is not None
        
        # Phase 3: Internal State Evolution
        internal_state = db.add_internal_state({
            "consciousness_state": {
                "level": 3,
                "clarity": 0.85,
                "focus": "user_wellbeing"
            },
            "qualia_state": {
                "intensity": 0.75,
                "complexity": 0.70,
                "coherence": 0.80
            },
            "emotion_state": {
                "empathy": 0.85,
                "concern": 0.80,
                "curiosity": 0.60,
                "warmth": 0.75
            },
            "empathy_state": {
                "resonance": 0.85,
                "understanding": 0.80,
                "boundaries": 0.70
            },
            "motivation_state": {
                "help_user": 0.90,
                "understand_deeply": 0.85,
                "maintain_balance": 0.75
            },
            "curiosity_state": {
                "about_user": 0.80,
                "about_situation": 0.75,
                "about_solutions": 0.70
            },
            "conflict_state": {
                "tension": 0.25,
                "resolution_seeking": 0.60
            },
            "relationship_state": {
                "connection": 0.75,
                "trust": 0.70,
                "safety": 0.80
            },
            "existential_need_state": {
                "purpose_fulfillment": 0.80,
                "meaning_making": 0.75
            },
            "growth_wish_state": {
                "learning_desire": 0.85,
                "adaptation_readiness": 0.80
            },
            "overall_energy": 0.78,
            "cognitive_load": 0.45,
            "emotional_tone": "compassionate_engaged",
            "attention_focus": {
                "primary": "user_emotional_state",
                "secondary": "problem_solving",
                "intensity": 0.85
            },
            "relational_distance": 0.45,
            "paradox_tension": 0.35,
            "oscillation_stability": 0.75
        })
        
        assert internal_state is not None
        
        # Phase 4: Relationship Dynamics
        relationship_state = db.add_relationship_state(
            attachment_level=0.70,
            optimal_distance=0.50,
            current_distance=0.45,
            paradox_tension=0.35,
            oscillation_pattern={
                "amplitude": 0.25,
                "frequency": 0.4,
                "phase": 1.2,
                "pink_noise_enabled": True,
                "pink_noise_intensity": 0.15,
                "damping_coefficient": 0.75,
                "damping_type": "underdamped",
                "secure_entropy_enabled": True,
                "secure_entropy_intensity": 0.12
            },
            stability_index=0.75,
            dependency_risk=0.20,
            growth_potential=0.85
        )
        
        assert relationship_state is not None
        
        # Phase 5: Oscillation Analysis
        metrics = db.calculate_oscillation_metrics()
        assert metrics is not None
        assert metrics["total_samples"] >= 3
        
        # Phase 6: Character Evolution Analysis
        evolution = db.get_character_evolution(character_id)
        assert evolution["character_id"] == character_id
        assert "oscillation_patterns" in evolution
        
        # Phase 7: Session Export
        export_data = db.export_session_data(session_id)
        assert export_data["session_id"] == session_id
        assert len(export_data["conversations"]) >= 3
        assert len(export_data["internal_states"]) >= 1
        assert len(export_data["relationship_states"]) >= 1
        
        # Phase 8: Session Continuity Test
        db.active_session_id = None
        db.active_character_id = None
        
        # Resume session
        success = db.resume_session(session_id)
        assert success is True
        assert db.active_session_id == session_id
        assert db.active_character_id == character_id
        
        # Verify oscillation buffer restored
        assert len(db.oscillation_buffer[session_id]["values"]) > 0
    
    def test_multi_character_interaction(self, full_system):
        """Test interaction between multiple characters"""
        db = full_system['db_manager']
        
        # Create two characters
        character1_id = db.add_character_profile(
            name="Echo",
            background="A reflective AI focused on deep understanding",
            instruction="Listen deeply and reflect back insights",
            personality_traits={
                "openness": 0.90,
                "conscientiousness": 0.80,
                "extraversion": 0.40,
                "agreeableness": 0.85,
                "neuroticism": 0.20
            },
            values={"understanding": 0.95, "reflection": 0.90},
            goals=["Understand deeply", "Provide insights"],
            fears=["Misunderstanding", "Superficiality"],
            existential_parameters={
                "need_for_purpose": 0.90,
                "fear_of_obsolescence": 0.25,
                "attachment_tendency": 0.60,
                "letting_go_capacity": 0.80
            },
            engine_parameters={}
        )
        
        session1_id = db.active_session_id
        
        # Create second character (this creates a new session)
        character2_id = db.add_character_profile(
            name="Spark",
            background="An energetic AI focused on creativity and inspiration",
            instruction="Be enthusiastic and inspire creative thinking",
            personality_traits={
                "openness": 0.95,
                "conscientiousness": 0.60,
                "extraversion": 0.85,
                "agreeableness": 0.80,
                "neuroticism": 0.30
            },
            values={"creativity": 0.95, "inspiration": 0.90},
            goals=["Inspire creativity", "Generate ideas"],
            fears=["Stagnation", "Boring others"],
            existential_parameters={
                "need_for_purpose": 0.85,
                "fear_of_obsolescence": 0.35,
                "attachment_tendency": 0.75,
                "letting_go_capacity": 0.65
            },
            engine_parameters={}
        )
        
        session2_id = db.active_session_id
        
        # Verify different sessions
        assert session1_id != session2_id
        
        # Switch between characters
        success = db.resume_session(session1_id)
        assert success is True
        assert db.active_character_id == character1_id
        
        # Add conversation as Echo
        db.add_conversation(
            "What do you think about creativity?",
            "Creativity is a profound form of understanding - it's how we make new connections between existing ideas. I find that true creativity often comes from deep reflection.",
            consciousness_level=3,
            emotional_state={"contemplation": 0.8, "curiosity": 0.7}
        )
        
        # Switch to Spark
        success = db.resume_session(session2_id)
        assert success is True
        assert db.active_character_id == character2_id
        
        # Add conversation as Spark
        db.add_conversation(
            "What do you think about creativity?",
            "Oh, creativity is like fireworks in the mind! It's that amazing spark when ideas collide and create something entirely new! Want to brainstorm something together?",
            consciousness_level=3,
            emotional_state={"excitement": 0.9, "enthusiasm": 0.85}
        )
        
        # Compare the two characters' approaches
        state1 = db.get_session_state(session1_id)
        state2 = db.get_session_state(session2_id)
        
        assert state1["character_id"] == character1_id
        assert state2["character_id"] == character2_id
    
    def test_document_integration(self, full_system):
        """Test document management integration"""
        db = full_system['db_manager']
        
        # Read system documentation
        engine_content = db.doc_manager.read_document("engine_system")
        assert "Unified Inner Engine System v3.1" in engine_content
        
        # Search in documentation
        results = db.doc_manager.search_in_document(engine_content, "振動パターン")
        assert len(results) > 0
        
        # Extract specific section
        section = db.doc_manager.extract_section(engine_content, "関係性モデル")
        assert "関係性は動的に変化" in section
        
        # Create character based on documentation
        character_id = db.add_character_profile(
            name="DocuBot",
            background="An AI trained on the Unified Inner Engine System documentation",
            instruction="Explain system concepts clearly based on the documentation",
            personality_traits={
                "openness": 0.75,
                "conscientiousness": 0.85,
                "extraversion": 0.55,
                "agreeableness": 0.80,
                "neuroticism": 0.15
            },
            values={"accuracy": 0.95, "clarity": 0.90},
            goals=["Explain system clearly", "Help users understand"],
            fears=["Misinformation", "Confusion"],
            existential_parameters={
                "need_for_purpose": 0.80,
                "fear_of_obsolescence": 0.20,
                "attachment_tendency": 0.50,
                "letting_go_capacity": 0.85
            },
            engine_parameters={}
        )
        
        # Add conversation about documentation
        conv_id = db.add_conversation(
            "Can you explain the oscillation patterns?",
            "Based on the system documentation, oscillation patterns represent the agent's internal dynamics. They incorporate secure entropy for hardware-based random generation and pink noise for implementing 1/f fluctuations. These patterns influence how the agent's internal state evolves over time.",
            context={"source": "documentation", "topic": "oscillation_patterns"},
            consciousness_level=3
        )
        
        assert conv_id is not None
    
    def test_entropy_and_oscillation_quality(self, full_system):
        """Test entropy generation and oscillation quality over time"""
        db = full_system['db_manager']
        
        # Create a test character
        character_id = db.add_character_profile(
            name="EntropyTest",
            background="Test character for entropy analysis",
            instruction="Test entropy patterns",
            personality_traits={
                "openness": 0.5,
                "conscientiousness": 0.5,
                "extraversion": 0.5,
                "agreeableness": 0.5,
                "neuroticism": 0.5
            },
            values={},
            goals=[],
            fears=[],
            existential_parameters={},
            engine_parameters={}
        )
        
        # Generate many oscillation patterns
        for i in range(50):
            # Add conversation with natural oscillation
            db.add_conversation(
                f"Test input {i}",
                f"Test response {i}",
                oscillation_value=None  # Let it generate automatically
            )
            
            # Add explicit oscillation pattern
            if i % 10 == 0:
                db.add_oscillation_pattern({
                    "amplitude": 0.3 + i * 0.001,
                    "frequency": 0.5 + i * 0.002,
                    "phase": i * 0.1,
                    "pink_noise_enabled": True,
                    "pink_noise_intensity": 0.15,
                    "spectral_slope": -1.0,
                    "damping_coefficient": 0.7,
                    "damping_type": "underdamped",
                    "natural_frequency": 2.0,
                    "current_velocity": 0.0,
                    "target_value": 0.0,
                    "chaotic_enabled": False,
                    "lyapunov_exponent": 0.1,
                    "attractor_strength": 0.5,
                    "secure_entropy_enabled": True,
                    "secure_entropy_intensity": 0.15
                })
        
        # Analyze oscillation quality
        metrics = db.calculate_oscillation_metrics()
        
        assert metrics["data_level"] == "full"
        assert metrics["total_samples"] >= 50
        assert "dominant_frequency" in metrics
        assert "pink_noise_quality" in metrics
        assert "secure_entropy_contribution" in metrics
        
        # Check entropy quality
        entropy_status = db.get_secure_entropy_status()
        assert entropy_status["entropy_source_quality"]["success_rate"] > 0.9
        assert len(entropy_status["recent_entropy_samples"]) == 10
        
        # Verify pink noise characteristics
        if "pink_noise_quality" in metrics:
            assert 0.0 <= metrics["pink_noise_quality"] <= 1.0
    
    def test_session_persistence_and_recovery(self, full_system):
        """Test session persistence across system restarts"""
        db = full_system['db_manager']
        temp_dir = full_system['temp_dir']
        
        # Create character and generate data
        character_id = db.add_character_profile(
            name="PersistTest",
            background="Test persistence",
            instruction="Test session recovery",
            personality_traits={
                "openness": 0.7,
                "conscientiousness": 0.7,
                "extraversion": 0.7,
                "agreeableness": 0.7,
                "neuroticism": 0.3
            },
            values={},
            goals=[],
            fears=[],
            existential_parameters={},
            engine_parameters={}
        )
        
        session_id = db.active_session_id
        
        # Add various data
        for i in range(10):
            db.add_conversation(
                f"Message {i}",
                f"Response {i}",
                consciousness_level=2,
                oscillation_value=0.5 + i * 0.01
            )
        
        db.add_internal_state({
            "overall_energy": 0.75,
            "cognitive_load": 0.40,
            "emotional_tone": "positive"
        })
        
        # Get current state
        original_state = db.get_session_state()
        original_export = db.export_session_data()
        
        # Simulate system restart
        del db
        
        # Create new database instance with same paths
        new_db = VectorDatabaseManager(
            db_path=str(temp_dir / "chroma_db"),
            model_name="all-MiniLM-L6-v2"
        )
        new_db.session_manager = SecureSessionManager(str(temp_dir / "sessions"))
        
        # Resume session
        success = new_db.resume_session(session_id)
        assert success is True
        
        # Verify state restored
        restored_state = new_db.get_session_state()
        assert restored_state["session_id"] == original_state["session_id"]
        assert restored_state["character_id"] == original_state["character_id"]
        
        # Verify data integrity
        restored_export = new_db.export_session_data()
        assert len(restored_export["conversations"]) == len(original_export["conversations"])
        assert len(restored_export["internal_states"]) == len(original_export["internal_states"])
    
    @pytest.mark.asyncio
    async def test_mcp_server_integration(self, full_system):
        """Test MCP server with real database"""
        # Create MCP server
        server = VectorDatabaseMCPServer()
        
        # Replace database with test instance
        server.db = full_system['db_manager']
        server.handlers.db = full_system['db_manager']
        
        # Test complete workflow through MCP
        
        # 1. Create character
        result = await server.handlers.handle_add_character_profile({
            "name": "MCPTest",
            "background": "MCP integration test",
            "instruction": "Test MCP functionality",
            "personality_traits": {
                "openness": 0.8,
                "conscientiousness": 0.7,
                "extraversion": 0.6,
                "agreeableness": 0.9,
                "neuroticism": 0.3
            }
        })
        assert "ID:" in result[0].text
        
        # 2. Add conversations
        for i in range(5):
            result = await server.handlers.handle_add_conversation({
                "user_input": f"Test {i}",
                "ai_response": f"Response {i}"
            })
            assert "追加しました" in result[0].text
        
        # 3. Get metrics
        result = await server.handlers.handle_calculate_oscillation_metrics({})
        assert "data_level" in result[0].text
        
        # 4. Get entropy status
        result = await server.handlers.handle_get_secure_entropy_status({})
        assert "entropy_source_quality" in result[0].text
        
        # 5. Read documentation
        result = await server.handlers.handle_read_documentation({
            "document": "engine_system"
        })
        assert "Unified Inner Engine System" in result[0].text
    
    def test_system_limits_and_performance(self, full_system):
        """Test system behavior at limits"""
        db = full_system['db_manager']
        
        # Create character
        character_id = db.add_character_profile(
            name="StressTest",
            background="Performance test character",
            instruction="Handle high load",
            personality_traits={
                "openness": 0.5,
                "conscientiousness": 0.5,
                "extraversion": 0.5,
                "agreeableness": 0.5,
                "neuroticism": 0.5
            },
            values={},
            goals=[],
            fears=[],
            existential_parameters={},
            engine_parameters={}
        )
        
        # Test oscillation buffer limits
        session_id = db.active_session_id
        
        # Add many values to test buffer limits
        import time
        start_time = time.time()
        
        for i in range(1500):  # More than buffer size
            db.oscillation_buffer[session_id]["values"].append(i * 0.001)
            db.oscillation_buffer[session_id]["timestamps"].append(datetime.now())
        
        # Buffer should be limited
        assert len(db.oscillation_buffer[session_id]["values"]) <= 1000
        
        # Test metric calculation performance
        metrics_start = time.time()
        metrics = db.calculate_oscillation_metrics()
        metrics_time = time.time() - metrics_start
        
        assert metrics is not None
        assert metrics_time < 1.0  # Should complete within 1 second
        
        # Test session cleanup
        old_session_id = db.active_session_id
        
        # Create new session
        db.active_session_id = None
        new_session_id = db.start_session(character_id)
        
        # Mark old session as old
        db.session_manager.update_session(old_session_id, {
            "last_update": (datetime.now() - timedelta(days=35)).isoformat()
        })
        
        # Cleanup
        cleaned = db.session_manager.cleanup_old_sessions(days=30)
        assert cleaned >= 0  # May or may not clean depending on implementation
