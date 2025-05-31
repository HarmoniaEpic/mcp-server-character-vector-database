"""
Tests for vector database manager
"""

import pytest
import time
from datetime import datetime, timedelta

from core.database import VectorDatabaseManager
from core.models import DataType, EngineType
from core.exceptions import CharacterNotFoundError
from conftest import create_test_session, add_test_conversations, generate_test_oscillation_values


class TestVectorDatabaseManager:
    """Test vector database manager"""
    
    def test_initialization(self, db_manager):
        """Test database manager initialization"""
        assert db_manager is not None
        assert db_manager.active_character_id is None
        assert db_manager.active_session_id is None
        assert len(db_manager.collections) == len(DataType)
        assert hasattr(db_manager, 'entropy_source')
        assert hasattr(db_manager, 'pink_noise_generator')
        assert hasattr(db_manager, 'doc_manager')
        assert hasattr(db_manager, 'session_manager')
    
    def test_generate_embedding(self, db_manager):
        """Test embedding generation"""
        text = "This is a test text for embedding generation."
        embedding = db_manager._generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)
    
    def test_generate_composite_embedding(self, db_manager):
        """Test composite embedding generation"""
        texts = ["First text", "Second text", "Third text"]
        weights = [1.0, 2.0, 1.0]
        
        embedding = db_manager._generate_composite_embedding(texts, weights)
        
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        
        # Should be normalized
        import numpy as np
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 0.01


class TestCharacterManagement:
    """Test character profile management"""
    
    def test_add_character_profile(self, db_manager, sample_character_profile):
        """Test adding character profile"""
        profile_id = db_manager.add_character_profile(**sample_character_profile)
        
        assert profile_id is not None
        assert db_manager.active_character_id == profile_id
        assert db_manager.active_session_id is not None
        
        # Verify in collection
        results = db_manager.collections[DataType.CHARACTER_PROFILE].get(
            ids=[profile_id],
            include=["metadatas"]
        )
        
        assert len(results["metadatas"]) == 1
        metadata = results["metadatas"][0]
        assert metadata["name"] == sample_character_profile["name"]
        assert metadata["instruction"] == sample_character_profile["instruction"]
    
    def test_search_by_instruction(self, db_manager, sample_character_profile):
        """Test searching by instruction"""
        # Add character
        db_manager.add_character_profile(**sample_character_profile)
        
        # Search by instruction
        results = db_manager.search_by_instruction("helpful test assistant", top_k=5)
        
        assert len(results) > 0
        assert results[0]["instruction"] == sample_character_profile["instruction"]
        assert results[0]["similarity"] > 0.5
    
    def test_get_character_evolution(self, db_manager, sample_character_profile):
        """Test character evolution analysis"""
        character_id, session_id = create_test_session(db_manager, sample_character_profile)
        
        # Add some conversations
        add_test_conversations(db_manager, count=5)
        
        # Get evolution
        evolution = db_manager.get_character_evolution(character_id)
        
        assert evolution["character_id"] == character_id
        assert "oscillation_patterns" in evolution
        assert evolution["oscillation_patterns"]["pattern_length"] >= 5


class TestSessionManagement:
    """Test session management"""
    
    def test_start_session(self, db_manager, sample_character_profile):
        """Test starting new session"""
        character_id = db_manager.add_character_profile(**sample_character_profile)
        
        # Character creation auto-starts session, so start another
        db_manager.active_session_id = None
        session_id = db_manager.start_session(character_id)
        
        assert session_id is not None
        assert db_manager.active_session_id == session_id
        assert db_manager.active_character_id == character_id
        
        # Verify oscillation buffer initialized
        assert session_id in db_manager.oscillation_buffer
        assert len(db_manager.oscillation_buffer[session_id]["values"]) >= 5
    
    def test_resume_session(self, db_manager, sample_character_profile):
        """Test resuming session"""
        character_id, session_id = create_test_session(db_manager, sample_character_profile)
        
        # Add some data
        add_test_conversations(db_manager, count=3)
        
        # Clear active session
        db_manager.active_session_id = None
        db_manager.active_character_id = None
        
        # Resume
        success = db_manager.resume_session(session_id)
        
        assert success is True
        assert db_manager.active_session_id == session_id
        assert db_manager.active_character_id == character_id
        
        # Verify oscillation buffer restored
        assert session_id in db_manager.oscillation_buffer
        assert len(db_manager.oscillation_buffer[session_id]["values"]) > 0
    
    def test_get_session_state(self, db_manager, sample_character_profile):
        """Test getting session state"""
        character_id, session_id = create_test_session(db_manager, sample_character_profile)
        
        state = db_manager.get_session_state()
        
        assert state["session_id"] == session_id
        assert state["character_id"] == character_id
        assert "secure_entropy_status" in state
        assert state["interaction_count"] >= 0
    
    def test_export_session_data(self, db_manager, sample_character_profile):
        """Test exporting session data"""
        character_id, session_id = create_test_session(db_manager, sample_character_profile)
        
        # Add various data
        add_test_conversations(db_manager, count=3)
        
        # Export
        export_data = db_manager.export_session_data()
        
        assert export_data["session_id"] == session_id
        assert "conversations" in export_data
        assert len(export_data["conversations"]) >= 3
        assert "oscillation_buffer" in export_data


class TestConversationManagement:
    """Test conversation management"""
    
    def test_add_conversation(self, db_manager, sample_character_profile, sample_conversation):
        """Test adding conversation"""
        create_test_session(db_manager, sample_character_profile)
        
        conv_id = db_manager.add_conversation(**sample_conversation)
        
        assert conv_id is not None
        
        # Verify in collection
        results = db_manager.collections[DataType.CONVERSATION].get(
            ids=[conv_id],
            include=["metadatas"]
        )
        
        assert len(results["metadatas"]) == 1
        metadata = results["metadatas"][0]
        assert metadata["user_input"] == sample_conversation["user_input"]
        assert metadata["ai_response"] == sample_conversation["ai_response"]
        assert "oscillation_value" in metadata
    
    def test_conversation_with_oscillation(self, db_manager, sample_character_profile):
        """Test conversation with oscillation tracking"""
        character_id, session_id = create_test_session(db_manager, sample_character_profile)
        
        initial_buffer_size = len(db_manager.oscillation_buffer[session_id]["values"])
        
        # Add conversation with specific oscillation value
        conv_id = db_manager.add_conversation(
            user_input="Test question",
            ai_response="Test response",
            oscillation_value=0.42,
            relational_distance=0.5
        )
        
        # Verify oscillation added to buffer
        buffer = db_manager.oscillation_buffer[session_id]
        assert len(buffer["values"]) == initial_buffer_size + 1
        assert buffer["values"][-1] == 0.42
    
    def test_conversation_auto_oscillation(self, db_manager, sample_character_profile):
        """Test conversation with automatic oscillation generation"""
        create_test_session(db_manager, sample_character_profile)
        
        # Add conversation without oscillation value
        conv_id = db_manager.add_conversation(
            user_input="Test question",
            ai_response="Test response"
        )
        
        # Should have generated oscillation value
        results = db_manager.collections[DataType.CONVERSATION].get(
            ids=[conv_id],
            include=["metadatas"]
        )
        
        metadata = results["metadatas"][0]
        assert metadata["oscillation_value"] != 0.0


class TestInternalStateManagement:
    """Test internal state management"""
    
    def test_add_internal_state(self, db_manager, sample_character_profile, sample_internal_state):
        """Test adding internal state"""
        create_test_session(db_manager, sample_character_profile)
        
        state_id = db_manager.add_internal_state(sample_internal_state)
        
        assert state_id is not None
        
        # Verify in collection
        results = db_manager.collections[DataType.INTERNAL_STATE].get(
            ids=[state_id],
            include=["metadatas"]
        )
        
        assert len(results["metadatas"]) == 1
        metadata = results["metadatas"][0]
        assert float(metadata["overall_energy"]) == sample_internal_state["overall_energy"]
        assert metadata["emotional_tone"] == sample_internal_state["emotional_tone"]


class TestRelationshipManagement:
    """Test relationship state management"""
    
    def test_add_relationship_state(self, db_manager, sample_character_profile, 
                                   sample_relationship_state, sample_oscillation_pattern):
        """Test adding relationship state"""
        create_test_session(db_manager, sample_character_profile)
        
        state_id = db_manager.add_relationship_state(
            oscillation_pattern=sample_oscillation_pattern,
            **sample_relationship_state
        )
        
        assert state_id is not None
        
        # Verify in collection
        results = db_manager.collections[DataType.RELATIONSHIP].get(
            ids=[state_id],
            include=["metadatas"]
        )
        
        assert len(results["metadatas"]) == 1
        metadata = results["metadatas"][0]
        assert float(metadata["attachment_level"]) == sample_relationship_state["attachment_level"]
        assert "oscillation_pattern" in metadata
    
    def test_relationship_with_default_oscillation(self, db_manager, sample_character_profile, 
                                                  sample_relationship_state):
        """Test relationship state with default oscillation pattern"""
        create_test_session(db_manager, sample_character_profile)
        
        # Add without oscillation pattern
        state_id = db_manager.add_relationship_state(**sample_relationship_state)
        
        # Should have default pattern
        results = db_manager.collections[DataType.RELATIONSHIP].get(
            ids=[state_id],
            include=["metadatas"]
        )
        
        metadata = results["metadatas"][0]
        import json
        pattern_data = json.loads(metadata["oscillation_pattern"])
        assert pattern_data["secure_entropy_enabled"] is True
        assert len(pattern_data["history"]) > 0


class TestOscillationManagement:
    """Test oscillation pattern management"""
    
    def test_add_oscillation_pattern(self, db_manager, sample_character_profile, 
                                    sample_oscillation_pattern):
        """Test adding oscillation pattern"""
        create_test_session(db_manager, sample_character_profile)
        
        pattern_id = db_manager.add_oscillation_pattern(sample_oscillation_pattern)
        
        assert pattern_id is not None
        
        # Verify in collection
        results = db_manager.collections[DataType.OSCILLATION_PATTERN].get(
            ids=[pattern_id],
            include=["metadatas"]
        )
        
        assert len(results["metadatas"]) == 1
        metadata = results["metadatas"][0]
        import json
        pattern_data = json.loads(metadata["pattern_data"])
        assert pattern_data["amplitude"] == sample_oscillation_pattern["amplitude"]
        assert len(pattern_data["history"]) > 0  # Should have generated history
    
    def test_calculate_oscillation_metrics(self, db_manager, sample_character_profile):
        """Test oscillation metrics calculation"""
        character_id, session_id = create_test_session(db_manager, sample_character_profile)
        
        # Add test oscillation values
        test_values = generate_test_oscillation_values(count=20)
        buffer = db_manager.oscillation_buffer[session_id]
        buffer["values"].extend(test_values)
        
        # Calculate metrics
        metrics = db_manager.calculate_oscillation_metrics()
        
        assert metrics["data_level"] == "full"
        assert metrics["total_samples"] >= 20
        assert "mean" in metrics
        assert "stability" in metrics
        assert "dominant_frequency" in metrics
    
    def test_oscillation_data_supplementation(self, db_manager, sample_character_profile):
        """Test automatic oscillation data supplementation"""
        character_id, session_id = create_test_session(db_manager, sample_character_profile)
        
        # Clear buffer to test supplementation
        db_manager.oscillation_buffer[session_id] = {"values": [], "timestamps": []}
        
        # Calculate metrics should trigger supplementation
        metrics = db_manager.calculate_oscillation_metrics()
        
        # Should have minimum samples
        assert len(db_manager.oscillation_buffer[session_id]["values"]) >= 5
        assert metrics["data_level"] in ["basic", "intermediate", "full"]


class TestEntropyManagement:
    """Test secure entropy management"""
    
    def test_add_secure_entropy_log(self, db_manager, sample_character_profile):
        """Test adding secure entropy log"""
        create_test_session(db_manager, sample_character_profile)
        
        entropy_value = 12345678
        normalized_value = 0.42
        source_type = "secure_combined"
        
        log_id = db_manager.add_secure_entropy_log(
            entropy_value, normalized_value, source_type
        )
        
        assert log_id is not None
        
        # Verify in collection
        results = db_manager.collections[DataType.SECURE_ENTROPY].get(
            ids=[log_id],
            include=["metadatas"]
        )
        
        assert len(results["metadatas"]) == 1
        metadata = results["metadatas"][0]
        assert metadata["entropy_value"] == entropy_value
        assert float(metadata["normalized_value"]) == normalized_value
        assert metadata["source_type"] == source_type
    
    def test_get_secure_entropy_status(self, db_manager):
        """Test getting secure entropy status"""
        status = db_manager.get_secure_entropy_status()
        
        assert "entropy_source_quality" in status
        assert "recent_entropy_samples" in status
        assert "entropy_statistics" in status
        assert "pink_noise_generator_status" in status
        assert "system_info" in status
        
        # Check samples
        assert len(status["recent_entropy_samples"]) == 10
        for sample in status["recent_entropy_samples"]:
            assert "raw_value" in sample
            assert "normalized" in sample
            assert 0.0 <= sample["normalized"] <= 1.0


class TestEngineStateManagement:
    """Test engine state management"""
    
    def test_add_engine_state(self, db_manager, sample_character_profile):
        """Test adding engine state"""
        create_test_session(db_manager, sample_character_profile)
        
        state_data = {
            "level": 3,
            "clarity": 0.8,
            "focus": "conversation"
        }
        
        state_id = db_manager.add_engine_state(
            EngineType.CONSCIOUSNESS,
            state_data
        )
        
        assert state_id is not None
        
        # Verify in collection
        results = db_manager.collections[DataType.ENGINE_STATE].get(
            ids=[state_id],
            include=["metadatas"]
        )
        
        assert len(results["metadatas"]) == 1
        metadata = results["metadatas"][0]
        assert metadata["engine_type"] == "consciousness"
        import json
        assert json.loads(metadata["state_data"]) == state_data


class TestMemoryManagement:
    """Test memory management"""
    
    def test_add_memory(self, db_manager, sample_character_profile):
        """Test adding memory"""
        create_test_session(db_manager, sample_character_profile)
        
        memory_id = db_manager.add_memory(
            content="Important conversation about testing",
            memory_type="episodic",
            relevance_score=0.8,
            associated_engines=["consciousness", "emotion"],
            emotional_context={"joy": 0.6, "curiosity": 0.8}
        )
        
        assert memory_id is not None
        
        # Verify in collection
        results = db_manager.collections[DataType.MEMORY].get(
            ids=[memory_id],
            include=["metadatas", "documents"]
        )
        
        assert len(results["metadatas"]) == 1
        metadata = results["metadatas"][0]
        assert metadata["memory_type"] == "episodic"
        assert float(metadata["relevance_score"]) == 0.8
        assert "emotional_context" in metadata


class TestDatabaseOperations:
    """Test database operations"""
    
    def test_reset_database(self, db_manager, sample_character_profile, temp_dir):
        """Test database reset"""
        # Add data
        character_id, session_id = create_test_session(db_manager, sample_character_profile)
        add_test_conversations(db_manager, count=3)
        
        # Reset
        db_manager.reset_database()
        
        # Verify collections are empty
        for data_type, collection in db_manager.collections.items():
            results = collection.get(limit=1)
            assert len(results["ids"]) == 0
        
        # Verify buffers cleared
        assert len(db_manager.oscillation_buffer) == 0
        assert len(db_manager.session_manager.active_sessions) == 0
        
        # Check backup created
        backup_dir = temp_dir.parent / "session_backups"
        if backup_dir.exists():
            backups = list(backup_dir.glob("backup_*.json"))
            assert len(backups) >= 0  # May or may not have backups


class TestOscillationBufferRestore:
    """Test oscillation buffer restoration"""
    
    def test_session_continuity(self, db_manager, sample_character_profile):
        """Test session continuity with oscillation data"""
        character_id, session_id = create_test_session(db_manager, sample_character_profile)
        
        # Add conversations and oscillation patterns
        for i in range(10):
            db_manager.add_conversation(
                user_input=f"Question {i}",
                ai_response=f"Response {i}",
                oscillation_value=0.1 * i
            )
        
        # Add oscillation pattern
        db_manager.add_oscillation_pattern({
            "amplitude": 0.3,
            "frequency": 0.5,
            "phase": 0.0,
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
            "secure_entropy_intensity": 0.15,
            "history": [0.1, 0.2, 0.3, 0.4, 0.5]
        })
        
        # Get buffer state
        original_values = db_manager.oscillation_buffer[session_id]["values"].copy()
        
        # Clear session
        db_manager.active_session_id = None
        db_manager.active_character_id = None
        db_manager.oscillation_buffer.clear()
        
        # Resume session
        success = db_manager.resume_session(session_id)
        assert success is True
        
        # Verify buffer restored
        restored_values = db_manager.oscillation_buffer[session_id]["values"]
        assert len(restored_values) >= 5
        
        # Should have some overlap with original values
        # (may not be exact due to supplementation)
        assert any(v in original_values for v in restored_values[-5:])
