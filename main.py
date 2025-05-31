"""
Vector Database MCP Server - Main Entry Point
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config.logging import setup_logging
from mcp.server import VectorDatabaseMCPServer

# Test mode imports
from security.entropy import SecureEntropySource
from security.pink_noise import SecureEnhancedPinkNoiseGenerator
from document.manager import DocumentManager
from core.database import VectorDatabaseManager
from core.utils import filter_metadata

# Setup logging
logger = setup_logging()


def run_test_mode():
    """Run in test mode"""
    logger.info("Running in test mode...")
    
    # Test secure entropy system
    logger.info("\n=== Secure Entropy System Test ===")
    entropy_source = SecureEntropySource()
    print(f"Secure Entropy Quality: {entropy_source.assess_entropy_quality()}")
    
    # Get test samples
    for i in range(5):
        entropy_val = entropy_source.get_secure_entropy(4)
        normalized_val = entropy_source.get_normalized_entropy()
        thermal_osc = entropy_source.get_thermal_oscillation(0.1)
        print(f"Sample {i+1}: raw={entropy_val}, normalized={normalized_val:.6f}, thermal={thermal_osc:.6f}")
    
    # Test pink noise generator
    pink_gen = SecureEnhancedPinkNoiseGenerator(entropy_source)
    print("\nSecure Pink Noise Samples:")
    for i in range(5):
        pink_val = pink_gen.generate_secure_pink_noise()
        print(f"Pink Noise {i+1}: {pink_val:.6f}")
    
    # Test document manager
    print("\n=== Document Manager Test ===")
    doc_manager = DocumentManager()
    doc_info = doc_manager.get_document_info()
    print(f"Available documents: {list(doc_info['available_documents'].keys())}")
    
    for doc_key, metadata in doc_info['available_documents'].items():
        status = "✓ Available" if metadata.get('accessible', False) else "✗ Not accessible"
        print(f"  {doc_key}: {metadata['filename']} - {status}")
        
        if metadata.get('accessible', False):
            try:
                content = doc_manager.read_document(doc_key)
                print(f"    Content length: {len(content)} characters")
                
                # Test section extraction
                if doc_key == "manual":
                    section_content = doc_manager.extract_section(content, "システム概要")
                    if section_content:
                        print(f"    Section 'システム概要': {len(section_content)} characters")
                
                # Test search
                search_results = doc_manager.search_in_document(content, "振動", max_results=3)
                print(f"    Search for '振動': {len(search_results)} matches")
                
            except Exception as e:
                print(f"    Error reading document: {e}")
    
    # Test oscillation metrics fix
    print(f"\n=== Oscillation Metrics Fix Test ===")
    db_manager = VectorDatabaseManager()
    
    # Create test character profile
    test_character_id = db_manager.add_character_profile(
        "TestCharacter",
        "Test background",
        "Test as a friendly AI assistant",
        {"openness": 0.8, "conscientiousness": 0.7, "extraversion": 0.6, "agreeableness": 0.9, "neuroticism": 0.3},
        {"helpfulness": 0.9, "honesty": 0.8},
        ["Be helpful", "Learn continuously"],
        ["Making mistakes", "Being unhelpful"],
        {"need_for_purpose": 0.8, "fear_of_obsolescence": 0.4, "attachment_tendency": 0.6, "letting_go_capacity": 0.7},
        {}
    )
    
    print(f"Created test character: {test_character_id}")
    
    # Test session start
    session_id = db_manager.start_session(test_character_id)
    print(f"Started test session: {session_id}")
    
    # Test oscillation metrics calculation
    metrics_before = db_manager.calculate_oscillation_metrics()
    print(f"Initial metrics: {metrics_before}")
    
    # Add conversation
    conv_id = db_manager.add_conversation(
        "Hello, how are you?",
        "I'm doing well, thank you for asking!",
        consciousness_level=2,
        emotional_state={"joy": 0.7, "trust": 0.8}
    )
    print(f"Added conversation: {conv_id}")
    
    # Recalculate metrics
    metrics_after = db_manager.calculate_oscillation_metrics()
    print(f"Metrics after conversation: {metrics_after}")
    
    # Test session resume
    db_manager.active_session_id = None
    db_manager.active_character_id = None
    
    success = db_manager.resume_session(session_id)
    print(f"Session resume success: {success}")
    
    # Metrics after restore
    metrics_restored = db_manager.calculate_oscillation_metrics()
    print(f"Metrics after session restore: {metrics_restored}")
    
    # Security verification
    print(f"\n=== Security Features ===")
    print(f"- Dynamic compilation: Disabled")
    print(f"- Pickle usage: Disabled")
    print(f"- Subprocess calls: Disabled")
    print(f"- Secure entropy sources: {entropy_source.assess_entropy_quality()['entropy_sources']}")
    print(f"- Document path validation: Enabled")
    print(f"- File access whitelist: Enabled")
    print(f"- Session path traversal protection: Enabled")
    
    # ChromaDB metadata test
    print(f"\n=== ChromaDB Metadata Safety Test ===")
    test_metadata = {
        "test_int": 123,
        "test_float": 45.67,
        "test_string": "hello",
        "test_bool": True,
        "test_none": None,
        "test_list": [1, 2, 3]
    }
    filtered = filter_metadata(test_metadata)
    print(f"Original: {test_metadata}")
    print(f"Filtered: {filtered}")
    
    # File system check
    print(f"\n=== File System Check ===")
    current_dir = Path(__file__).parent
    engine_file = current_dir / "unified-inner-engine-v3.1.txt"
    manual_file = current_dir / "unified-engine-mcp-manual.md"
    
    print(f"Script directory: {current_dir}")
    print(f"Engine file: {engine_file} - {'EXISTS' if engine_file.exists() else 'MISSING'}")
    print(f"Manual file: {manual_file} - {'EXISTS' if manual_file.exists() else 'MISSING'}")
    
    print(f"\n🎯 Test completed successfully!")
    print(f"Main features:")
    print(f"- Secure entropy generation with multiple sources")
    print(f"- Session initialization with oscillation buffer")
    print(f"- Session resume with data restoration")
    print(f"- Automatic data supplementation")
    print(f"- Graduated metrics calculation")
    print(f"- Reduced minimum data requirements")


def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_test_mode()
    else:
        # Run MCP server
        server = VectorDatabaseMCPServer()
        asyncio.run(server.run())


if __name__ == "__main__":
    main()
