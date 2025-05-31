"""
Pytest configuration and shared fixtures
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import uuid

from core.database import VectorDatabaseManager
from security.entropy import SecureEntropySource
from security.pink_noise import SecureEnhancedPinkNoiseGenerator
from session.manager import SecureSessionManager
from document.manager import DocumentManager
from oscillation.buffer import OscillationBuffer
from vdb_server.server import VectorDatabaseMCPServer


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def entropy_source():
    """Create a secure entropy source"""
    return SecureEntropySource()


@pytest.fixture
def pink_noise_generator(entropy_source):
    """Create a pink noise generator"""
    return SecureEnhancedPinkNoiseGenerator(entropy_source)


@pytest.fixture
def session_manager(temp_dir):
    """Create a session manager with temporary storage"""
    session_dir = temp_dir / "sessions"
    return SecureSessionManager(str(session_dir))


@pytest.fixture
def document_manager(temp_dir):
    """Create a document manager with test documents"""
    docs_dir = temp_dir / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    # Create test documents
    engine_doc = docs_dir / "unified-inner-engine-v3.1.txt"
    engine_doc.write_text("""# Unified Inner Engine System v3.1

## システム概要
これはテスト用のエンジンドキュメントです。

## 振動パターン
振動に関する説明。

## セキュアエントロピー
エントロピーに関する説明。
""", encoding='utf-8')
    
    manual_doc = docs_dir / "unified-engine-mcp-manual.md"
    manual_doc.write_text("""# MCP Manual

## システム概要
これはテスト用のマニュアルドキュメントです。

## 使用方法
使用方法の説明。
""", encoding='utf-8')
    
    return DocumentManager(docs_dir)


@pytest.fixture
def db_manager(temp_dir):
    """Create a database manager with temporary storage"""
    db_path = str(temp_dir / "chroma_db")
    return VectorDatabaseManager(db_path=db_path)


@pytest.fixture
def mcp_server():
    """Create an MCP server instance"""
    return VectorDatabaseMCPServer()


@pytest.fixture
def oscillation_buffer():
    """Create an oscillation buffer"""
    return OscillationBuffer(max_size=100)


@pytest.fixture
def sample_character_profile():
    """Sample character profile data"""
    return {
        "name": "TestCharacter",
        "background": "A test character for unit testing",
        "instruction": "Act as a helpful test assistant",
        "personality_traits": {
            "openness": 0.8,
            "conscientiousness": 0.7,
            "extraversion": 0.6,
            "agreeableness": 0.9,
            "neuroticism": 0.3
        },
        "values": {
            "helpfulness": 0.9,
            "accuracy": 0.8,
            "friendliness": 0.7
        },
        "goals": ["Assist with testing", "Provide accurate responses"],
        "fears": ["Making errors", "Being unhelpful"],
        "existential_parameters": {
            "need_for_purpose": 0.8,
            "fear_of_obsolescence": 0.4,
            "attachment_tendency": 0.6,
            "letting_go_capacity": 0.7
        },
        "engine_parameters": {}
    }


@pytest.fixture
def sample_conversation():
    """Sample conversation data"""
    return {
        "user_input": "Hello, how are you?",
        "ai_response": "I'm doing well, thank you for asking!",
        "context": {"topic": "greeting"},
        "consciousness_level": 2,
        "emotional_state": {"joy": 0.7, "trust": 0.8}
    }


@pytest.fixture
def sample_oscillation_pattern():
    """Sample oscillation pattern data"""
    return {
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
        "history": []
    }


@pytest.fixture
def sample_internal_state():
    """Sample internal state data"""
    return {
        "consciousness_state": {"level": 2, "clarity": 0.8},
        "qualia_state": {"intensity": 0.7, "complexity": 0.6},
        "emotion_state": {"joy": 0.5, "trust": 0.6},
        "empathy_state": {"resonance": 0.7, "understanding": 0.8},
        "motivation_state": {"drive": 0.8, "direction": 0.7},
        "curiosity_state": {"level": 0.9, "focus": 0.6},
        "conflict_state": {"tension": 0.3, "resolution": 0.7},
        "relationship_state": {"connection": 0.7, "trust": 0.8},
        "existential_need_state": {"fulfillment": 0.6, "seeking": 0.7},
        "growth_wish_state": {"aspiration": 0.8, "progress": 0.6},
        "overall_energy": 0.7,
        "cognitive_load": 0.4,
        "emotional_tone": "positive",
        "attention_focus": {"target": "conversation", "intensity": 0.8},
        "relational_distance": 0.5,
        "paradox_tension": 0.4,
        "oscillation_stability": 0.8
    }


@pytest.fixture
def sample_relationship_state():
    """Sample relationship state data"""
    return {
        "attachment_level": 0.6,
        "optimal_distance": 0.5,
        "current_distance": 0.5,
        "paradox_tension": 0.4,
        "stability_index": 0.7,
        "dependency_risk": 0.3,
        "growth_potential": 0.8
    }


# Helper functions for tests

def create_test_session(db_manager, character_profile):
    """Helper to create a test session"""
    character_id = db_manager.add_character_profile(**character_profile)
    session_id = db_manager.start_session(character_id)
    return character_id, session_id


def add_test_conversations(db_manager, count=5):
    """Helper to add test conversations"""
    conversation_ids = []
    for i in range(count):
        conv_id = db_manager.add_conversation(
            user_input=f"Test question {i}?",
            ai_response=f"Test response {i}.",
            context={"index": i},
            consciousness_level=(i % 4) + 1,
            emotional_state={"joy": 0.5 + i * 0.1}
        )
        conversation_ids.append(conv_id)
    return conversation_ids


def generate_test_oscillation_values(count=20, base_amplitude=0.1):
    """Helper to generate test oscillation values"""
    import numpy as np
    t = np.linspace(0, 4 * np.pi, count)
    values = base_amplitude * np.sin(t) + np.random.normal(0, 0.01, count)
    return values.tolist()
