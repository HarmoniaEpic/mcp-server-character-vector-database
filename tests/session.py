"""
Tests for session management
"""

import pytest
import uuid
import time
from datetime import datetime, timedelta
from pathlib import Path

from session.manager import SecureSessionManager
from session.state import SessionState, SessionEnvironment
from session.storage import SessionStorage
from core.exceptions import SessionError, SessionNotFoundError, PathTraversalError


class TestSessionEnvironment:
    """Test session environment"""
    
    def test_initialization(self):
        """Test environment initialization"""
        env = SessionEnvironment()
        assert env.session_duration == 0.0
        assert env.interaction_count == 0
        assert env.emotional_volatility == 0.3
        assert env.topic_consistency == 0.7
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        env = SessionEnvironment(
            session_duration=120.5,
            interaction_count=10,
            emotional_volatility=0.4,
            topic_consistency=0.8
        )
        
        data = env.to_dict()
        assert data["session_duration"] == 120.5
        assert data["interaction_count"] == 10
        assert data["emotional_volatility"] == 0.4
        assert data["topic_consistency"] == 0.8
    
    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            "session_duration": 60.0,
            "interaction_count": 5,
            "emotional_volatility": 0.2,
            "topic_consistency": 0.9
        }
        
        env = SessionEnvironment.from_dict(data)
        assert env.session_duration == 60.0
        assert env.interaction_count == 5
        assert env.emotional_volatility == 0.2
        assert env.topic_consistency == 0.9


class TestSessionState:
    """Test session state"""
    
    def test_initialization(self):
        """Test state initialization"""
        session_id = str(uuid.uuid4())
        character_id = str(uuid.uuid4())
        
        state = SessionState(
            session_id=session_id,
            character_id=character_id,
            start_time=datetime.now(),
            last_update=datetime.now()
        )
        
        assert state.session_id == session_id
        assert state.character_id == character_id
        assert state.interaction_count == 0
        assert state.internal_state_id == ""
        assert state.relationship_state_id == ""
        assert state.oscillation_history == []
        assert state.active is True
        assert isinstance(state.environment, SessionEnvironment)
    
    def test_update_interaction(self):
        """Test interaction update"""
        state = SessionState(
            session_id=str(uuid.uuid4()),
            character_id=str(uuid.uuid4()),
            start_time=datetime.now(),
            last_update=datetime.now()
        )
        
        initial_count = state.interaction_count
        initial_update = state.last_update
        
        time.sleep(0.01)  # Ensure time difference
        state.update_interaction()
        
        assert state.interaction_count == initial_count + 1
        assert state.last_update > initial_update
        assert state.environment.interaction_count == state.interaction_count
    
    def test_update_duration(self):
        """Test duration update"""
        start_time = datetime.now() - timedelta(minutes=5)
        state = SessionState(
            session_id=str(uuid.uuid4()),
            character_id=str(uuid.uuid4()),
            start_time=start_time,
            last_update=start_time
        )
        
        state.update_duration()
        
        assert state.environment.session_duration >= 300.0  # At least 5 minutes
        assert state.last_update > start_time
    
    def test_add_oscillation_value(self):
        """Test adding oscillation values"""
        state = SessionState(
            session_id=str(uuid.uuid4()),
            character_id=str(uuid.uuid4()),
            start_time=datetime.now(),
            last_update=datetime.now()
        )
        
        # Add values
        for i in range(10):
            state.add_oscillation_value(i * 0.1)
        
        assert len(state.oscillation_history) == 10
        assert state.oscillation_history[-1] == 0.9
    
    def test_oscillation_history_limit(self):
        """Test oscillation history size limit"""
        state = SessionState(
            session_id=str(uuid.uuid4()),
            character_id=str(uuid.uuid4()),
            start_time=datetime.now(),
            last_update=datetime.now()
        )
        
        # Add more than limit
        for i in range(1100):
            state.add_oscillation_value(i * 0.001)
        
        assert len(state.oscillation_history) == 1000  # Limited to 1000
        assert state.oscillation_history[0] == 0.1  # First 100 values removed
    
    def test_get_recent_oscillations(self):
        """Test getting recent oscillations"""
        state = SessionState(
            session_id=str(uuid.uuid4()),
            character_id=str(uuid.uuid4()),
            start_time=datetime.now(),
            last_update=datetime.now()
        )
        
        # Add values
        for i in range(20):
            state.add_oscillation_value(i * 0.1)
        
        recent = state.get_recent_oscillations(5)
        assert len(recent) == 5
        assert recent == [1.5, 1.6, 1.7, 1.8, 1.9]
    
    def test_deactivate_reactivate(self):
        """Test session deactivation and reactivation"""
        state = SessionState(
            session_id=str(uuid.uuid4()),
            character_id=str(uuid.uuid4()),
            start_time=datetime.now(),
            last_update=datetime.now()
        )
        
        assert state.active is True
        
        state.deactivate()
        assert state.active is False
        
        state.reactivate()
        assert state.active is True
    
    def test_to_from_dict(self):
        """Test serialization and deserialization"""
        state = SessionState(
            session_id=str(uuid.uuid4()),
            character_id=str(uuid.uuid4()),
            start_time=datetime.now(),
            last_update=datetime.now(),
            interaction_count=5,
            internal_state_id="internal_123",
            relationship_state_id="rel_456",
            oscillation_history=[0.1, 0.2, 0.3],
            active=True
        )
        
        # Convert to dict
        data = state.to_dict()
        
        # Recreate from dict
        new_state = SessionState.from_dict(data)
        
        assert new_state.session_id == state.session_id
        assert new_state.character_id == state.character_id
        assert new_state.interaction_count == state.interaction_count
        assert new_state.internal_state_id == state.internal_state_id
        assert new_state.relationship_state_id == state.relationship_state_id
        assert new_state.oscillation_history == state.oscillation_history
        assert new_state.active == state.active


class TestSessionStorage:
    """Test session storage"""
    
    def test_initialization(self, temp_dir):
        """Test storage initialization"""
        storage = SessionStorage(str(temp_dir))
        assert storage.storage_dir == temp_dir
        assert storage.storage_dir.exists()
        assert storage.storage_dir.is_dir()
    
    def test_save_load(self, temp_dir):
        """Test saving and loading sessions"""
        storage = SessionStorage(str(temp_dir))
        session_id = str(uuid.uuid4())
        
        data = {
            "session_id": session_id,
            "character_id": str(uuid.uuid4()),
            "start_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
            "interaction_count": 10
        }
        
        # Save
        assert storage.save(session_id, data) is True
        
        # Load
        loaded_data = storage.load(session_id)
        assert loaded_data is not None
        assert loaded_data["session_id"] == session_id
        assert loaded_data["interaction_count"] == 10
    
    def test_delete(self, temp_dir):
        """Test session deletion"""
        storage = SessionStorage(str(temp_dir))
        session_id = str(uuid.uuid4())
        
        data = {"test": "data"}
        storage.save(session_id, data)
        
        assert storage.exists(session_id) is True
        assert storage.delete(session_id) is True
        assert storage.exists(session_id) is False
    
    def test_list_sessions(self, temp_dir):
        """Test listing sessions"""
        storage = SessionStorage(str(temp_dir))
        
        # Create multiple sessions
        session_ids = []
        for _ in range(5):
            session_id = str(uuid.uuid4())
            session_ids.append(session_id)
            storage.save(session_id, {"id": session_id})
        
        # List sessions
        listed = storage.list_sessions()
        assert len(listed) == 5
        assert set(listed) == set(session_ids)
    
    def test_invalid_session_id(self, temp_dir):
        """Test invalid session ID handling"""
        storage = SessionStorage(str(temp_dir))
        
        # Invalid IDs
        invalid_ids = [
            "not-a-uuid",
            "../../../etc/passwd",
            "12345",
            "",
            None
        ]
        
        for invalid_id in invalid_ids:
            if invalid_id is not None:
                with pytest.raises((SessionError, PathTraversalError)):
                    storage._get_session_path(invalid_id)
    
    def test_cleanup_old_sessions(self, temp_dir):
        """Test cleanup of old sessions"""
        storage = SessionStorage(str(temp_dir))
        
        # Create old session
        old_session_id = str(uuid.uuid4())
        old_path = storage._get_session_path(old_session_id)
        
        # Save with old timestamp
        storage.save(old_session_id, {"id": old_session_id})
        
        # Modify file time to be old
        import os
        old_time = time.time() - (35 * 24 * 60 * 60)  # 35 days ago
        os.utime(old_path, (old_time, old_time))
        
        # Create new session
        new_session_id = str(uuid.uuid4())
        storage.save(new_session_id, {"id": new_session_id})
        
        # Cleanup
        deleted = storage.cleanup_old_sessions(days=30)
        
        assert deleted == 1
        assert not storage.exists(old_session_id)
        assert storage.exists(new_session_id)
    
    def test_get_storage_stats(self, temp_dir):
        """Test storage statistics"""
        storage = SessionStorage(str(temp_dir))
        
        # Create sessions
        for _ in range(3):
            session_id = str(uuid.uuid4())
            storage.save(session_id, {"data": "x" * 1000})
        
        stats = storage.get_storage_stats()
        
        assert stats["total_sessions"] == 3
        assert stats["total_size_bytes"] > 3000
        assert "oldest_session" in stats
        assert "newest_session" in stats


class TestSecureSessionManager:
    """Test secure session manager"""
    
    def test_initialization(self, session_manager):
        """Test manager initialization"""
        assert session_manager is not None
        assert len(session_manager.active_sessions) == 0
        assert len(session_manager.session_cache) == 0
    
    def test_create_session(self, session_manager):
        """Test session creation"""
        character_id = str(uuid.uuid4())
        session_id = session_manager.create_session(character_id)
        
        assert session_id is not None
        assert session_manager._validate_session_id(session_id) is True
        assert session_id in session_manager.active_sessions
        assert session_id in session_manager.session_cache
    
    def test_load_session(self, session_manager):
        """Test session loading"""
        character_id = str(uuid.uuid4())
        session_id = session_manager.create_session(character_id)
        
        # Clear cache to force file load
        session_manager.session_cache.clear()
        
        # Load session
        data = session_manager.load_session(session_id)
        assert data is not None
        assert data["character_id"] == character_id
        assert data["session_id"] == session_id
    
    def test_update_session(self, session_manager):
        """Test session update"""
        character_id = str(uuid.uuid4())
        session_id = session_manager.create_session(character_id)
        
        # Update session
        updates = {
            "interaction_count": 5,
            "custom_field": "test_value"
        }
        session_manager.update_session(session_id, updates)
        
        # Verify updates
        data = session_manager.load_session(session_id)
        assert data["interaction_count"] == 5
        assert data["custom_field"] == "test_value"
    
    def test_get_session_state(self, session_manager):
        """Test getting session state object"""
        character_id = str(uuid.uuid4())
        session_id = session_manager.create_session(character_id)
        
        state = session_manager.get_session_state(session_id)
        assert isinstance(state, SessionState)
        assert state.session_id == session_id
        assert state.character_id == character_id
    
    def test_delete_session(self, session_manager):
        """Test session deletion"""
        character_id = str(uuid.uuid4())
        session_id = session_manager.create_session(character_id)
        
        assert session_manager.delete_session(session_id) is True
        assert session_id not in session_manager.active_sessions
        assert session_id not in session_manager.session_cache
        assert session_manager.storage.exists(session_id) is False
    
    def test_list_active_sessions(self, session_manager):
        """Test listing active sessions"""
        # Create active sessions
        active_ids = []
        for _ in range(3):
            session_id = session_manager.create_session(str(uuid.uuid4()))
            active_ids.append(session_id)
        
        # Create inactive session
        inactive_id = session_manager.create_session(str(uuid.uuid4()))
        session_manager.deactivate_session(inactive_id)
        
        # List active
        active_list = session_manager.list_active_sessions()
        assert len(active_list) == 3
        assert set(active_list) == set(active_ids)
        assert inactive_id not in active_list
    
    def test_session_info(self, session_manager):
        """Test getting session info"""
        character_id = str(uuid.uuid4())
        session_id = session_manager.create_session(character_id)
        
        # Add some interactions
        session_manager.update_session(session_id, {"interaction_count": 5})
        
        info = session_manager.get_session_info(session_id)
        assert info is not None
        assert info["session_id"] == session_id
        assert info["character_id"] == character_id
        assert info["interaction_count"] == 5
        assert "duration_seconds" in info
        assert "idle_seconds" in info
    
    def test_manager_stats(self, session_manager):
        """Test manager statistics"""
        # Create sessions
        for _ in range(5):
            session_manager.create_session(str(uuid.uuid4()))
        
        stats = session_manager.get_manager_stats()
        assert stats["total_sessions"] == 5
        assert stats["active_sessions"] == 5
        assert stats["cached_sessions"] == 5
        assert stats["memory_sessions"] == 5
        assert "storage_stats" in stats
    
    def test_clear_cache(self, session_manager):
        """Test cache clearing"""
        # Create sessions
        session_id = session_manager.create_session(str(uuid.uuid4()))
        
        assert len(session_manager.session_cache) > 0
        
        session_manager.clear_cache()
        assert len(session_manager.session_cache) == 0
        
        # Should still be able to load from file
        data = session_manager.load_session(session_id)
        assert data is not None
    
    def test_session_not_found(self, session_manager):
        """Test handling of non-existent session"""
        fake_id = str(uuid.uuid4())
        
        assert session_manager.load_session(fake_id) is None
        
        with pytest.raises(SessionNotFoundError):
            session_manager.update_session(fake_id, {"test": "value"})
