"""
Tests for document management
"""

import pytest
from pathlib import Path

from document.manager import DocumentManager
from document.search import DocumentSearcher
from core.exceptions import DocumentNotFoundError, DocumentAccessError


class TestDocumentSearcher:
    """Test document searcher"""
    
    def test_initialization(self):
        """Test searcher initialization"""
        searcher = DocumentSearcher()
        assert searcher is not None
        assert len(searcher.search_cache) == 0
    
    def test_search_in_document(self):
        """Test document search"""
        searcher = DocumentSearcher()
        content = """Line 1: This is a test document.
Line 2: It contains multiple lines.
Line 3: We will search for specific words.
Line 4: This line also contains test.
Line 5: Final line of the document."""
        
        # Search for "test"
        results = searcher.search_in_document(content, "test", max_results=10)
        assert len(results) == 2
        assert results[0]["line_number"] == 1
        assert results[1]["line_number"] == 4
        
        # Check context
        assert "Line 1:" in results[0]["context"]
        assert "Line 4:" in results[1]["context"]
    
    def test_case_sensitive_search(self):
        """Test case-sensitive search"""
        searcher = DocumentSearcher()
        content = "Test TEST test TeSt"
        
        # Case insensitive (default)
        results = searcher.search_in_document(content, "test", case_sensitive=False)
        assert len(results) == 1
        assert len(results[0]["match_positions"]) == 4
        
        # Case sensitive
        results = searcher.search_in_document(content, "test", case_sensitive=True)
        assert len(results) == 1
        assert len(results[0]["match_positions"]) == 1
    
    def test_whole_word_search(self):
        """Test whole word search"""
        searcher = DocumentSearcher()
        content = "test testing tested pretest test"
        
        # Without whole word
        results = searcher.search_in_document(content, "test", whole_word=False)
        assert len(results) == 1
        assert len(results[0]["match_positions"]) == 5
        
        # With whole word
        results = searcher.search_in_document(content, "test", whole_word=True)
        assert len(results) == 1
        assert len(results[0]["match_positions"]) == 2
    
    def test_extract_section(self):
        """Test section extraction"""
        searcher = DocumentSearcher()
        content = """# Document Title

## Section 1
Content of section 1.

## Section 2
Content of section 2.
More content.

### Subsection 2.1
Subsection content.

## Section 3
Final section."""
        
        # Extract section
        section = searcher.extract_section(content, "Section 2")
        assert "## Section 2" in section
        assert "Content of section 2." in section
        assert "### Subsection 2.1" in section
        assert "## Section 3" not in section
    
    def test_find_headers(self):
        """Test finding headers"""
        searcher = DocumentSearcher()
        content = """# Main Title

## Chapter 1
### Section 1.1
#### Subsection 1.1.1

## Chapter 2
// Comment Header
Regular text"""
        
        headers = searcher.find_headers(content)
        assert len(headers) >= 5
        
        # Check main title
        assert headers[0]["title"] == "Main Title"
        assert headers[0]["level"] == 1
        assert headers[0]["type"] == "markdown"
        
        # Check subsection
        subsection = next(h for h in headers if h["title"] == "Subsection 1.1.1")
        assert subsection["level"] == 4
    
    def test_get_table_of_contents(self):
        """Test table of contents generation"""
        searcher = DocumentSearcher()
        content = """# Title

## Chapter 1
### Section 1.1
### Section 1.2

## Chapter 2
### Section 2.1"""
        
        toc = searcher.get_table_of_contents(content)
        assert "# Table of Contents" in toc
        assert "- Title" in toc
        assert "  - Chapter 1" in toc
        assert "    - Section 1.1" in toc
    
    def test_search_multiple_documents(self):
        """Test searching multiple documents"""
        searcher = DocumentSearcher()
        documents = {
            "doc1": "This is document 1 with test content.",
            "doc2": "This is document 2 without the word.",
            "doc3": "This is document 3 with test data."
        }
        
        results = searcher.search_multiple_documents(documents, "test")
        assert len(results) == 2
        assert "doc1" in results
        assert "doc3" in results
        assert "doc2" not in results
    
    def test_highlight_matches(self):
        """Test match highlighting"""
        searcher = DocumentSearcher()
        text = "This is a test of the highlighting test feature."
        
        highlighted = searcher.highlight_matches(text, "test")
        assert highlighted == "This is a **test** of the highlighting **test** feature."
        
        # Custom markers
        highlighted = searcher.highlight_matches(text, "test", "<em>", "</em>")
        assert highlighted == "This is a <em>test</em> of the highlighting <em>test</em> feature."
    
    def test_get_word_frequency(self):
        """Test word frequency analysis"""
        searcher = DocumentSearcher()
        content = """The quick brown fox jumps over the lazy dog.
The dog was really lazy. The fox was very quick and brown."""
        
        frequencies = searcher.get_word_frequency(content, min_length=3, top_n=5)
        
        # "the" and "was" should be most frequent
        assert len(frequencies) <= 5
        word_dict = dict(frequencies)
        assert word_dict.get("the", 0) >= 3
        assert word_dict.get("was", 0) >= 2
    
    def test_search_cache(self):
        """Test search result caching"""
        searcher = DocumentSearcher()
        content = "Test content for caching"
        
        # First search
        results1 = searcher.search_in_document(content, "test")
        cache_size1 = len(searcher.search_cache)
        
        # Same search should use cache
        results2 = searcher.search_in_document(content, "test")
        cache_size2 = len(searcher.search_cache)
        
        assert results1 == results2
        assert cache_size1 == cache_size2
        
        # Different search should add to cache
        searcher.search_in_document(content, "content")
        assert len(searcher.search_cache) > cache_size2
        
        # Clear cache
        searcher.clear_cache()
        assert len(searcher.search_cache) == 0


class TestDocumentManager:
    """Test document manager"""
    
    def test_initialization(self, document_manager):
        """Test manager initialization"""
        assert document_manager is not None
        assert len(document_manager.available_docs) == 2
        assert "engine_system" in document_manager.available_docs
        assert "manual" in document_manager.available_docs
    
    def test_scan_documents(self, document_manager):
        """Test document scanning"""
        # Documents should be found and accessible
        assert "engine_system" in document_manager.doc_metadata
        assert "manual" in document_manager.doc_metadata
        
        engine_meta = document_manager.doc_metadata["engine_system"]
        assert engine_meta["accessible"] is True
        assert engine_meta["size"] > 0
    
    def test_read_document(self, document_manager):
        """Test document reading"""
        # Read engine document
        content = document_manager.read_document("engine_system")
        assert "Unified Inner Engine System v3.1" in content
        assert "システム概要" in content
        
        # Read manual
        content = document_manager.read_document("manual")
        assert "MCP Manual" in content
    
    def test_read_nonexistent_document(self, document_manager):
        """Test reading non-existent document"""
        with pytest.raises(DocumentNotFoundError):
            document_manager.read_document("nonexistent")
    
    def test_document_caching(self, document_manager):
        """Test document caching"""
        # First read
        content1 = document_manager.read_document("engine_system")
        assert "engine_system" in document_manager.doc_cache
        
        # Second read should use cache
        content2 = document_manager.read_document("engine_system")
        assert content1 == content2
    
    def test_extract_section(self, document_manager):
        """Test section extraction"""
        content = document_manager.read_document("engine_system")
        section = document_manager.extract_section(content, "振動パターン")
        
        assert "振動パターン" in section
        assert len(section) < len(content)
    
    def test_search_in_document(self, document_manager):
        """Test document search"""
        content = document_manager.read_document("engine_system")
        results = document_manager.search_in_document(content, "振動")
        
        assert len(results) > 0
        assert results[0]["matched_line"]
        assert results[0]["context"]
    
    def test_search_all_documents(self, document_manager):
        """Test searching all documents"""
        results = document_manager.search_all_documents("システム")
        
        assert len(results) >= 1
        assert any("engine_system" in key or "manual" in key for key in results.keys())
    
    def test_get_document_info(self, document_manager):
        """Test getting document info"""
        # All documents info
        info = document_manager.get_document_info()
        assert "available_documents" in info
        assert "docs_directory" in info
        assert "cache_status" in info
        
        # Specific document info
        engine_info = document_manager.get_document_info("engine_system")
        assert "filename" in engine_info
        assert "size" in engine_info
        assert engine_info["accessible"] is True
    
    def test_get_document_headers(self, document_manager):
        """Test getting document headers"""
        headers = document_manager.get_document_headers("engine_system")
        assert len(headers) > 0
        
        # Should have main title
        main_title = next((h for h in headers if h["level"] == 1), None)
        assert main_title is not None
    
    def test_get_table_of_contents(self, document_manager):
        """Test generating table of contents"""
        toc = document_manager.get_table_of_contents("engine_system")
        assert "Table of Contents" in toc
        assert "Unified Inner Engine System" in toc
    
    def test_add_document(self, document_manager, temp_dir):
        """Test adding new document"""
        # Create new document
        new_doc = temp_dir / "docs" / "new_document.txt"
        new_doc.write_text("New document content", encoding='utf-8')
        
        # Add to manager
        success = document_manager.add_document("new_doc", "new_document.txt")
        assert success is True
        assert "new_doc" in document_manager.available_docs
        
        # Should be readable
        content = document_manager.read_document("new_doc")
        assert content == "New document content"
    
    def test_add_invalid_document(self, document_manager):
        """Test adding document with invalid filename"""
        # Invalid filename
        success = document_manager.add_document("bad", "../../../etc/passwd")
        assert success is False
    
    def test_remove_document(self, document_manager):
        """Test removing document"""
        # Can't remove core documents in test, so add one first
        document_manager.available_docs["temp_doc"] = "temp.txt"
        
        success = document_manager.remove_document("temp_doc")
        assert success is True
        assert "temp_doc" not in document_manager.available_docs
    
    def test_clear_cache(self, document_manager):
        """Test cache clearing"""
        # Read to populate cache
        document_manager.read_document("engine_system")
        assert len(document_manager.doc_cache) > 0
        
        # Clear cache
        document_manager.clear_cache()
        assert len(document_manager.doc_cache) == 0
        assert len(document_manager.searcher.search_cache) == 0
    
    def test_refresh(self, document_manager):
        """Test manager refresh"""
        # Read to populate cache
        document_manager.read_document("engine_system")
        initial_cache_size = len(document_manager.doc_cache)
        
        # Refresh
        document_manager.refresh()
        
        # Cache should be cleared
        assert len(document_manager.doc_cache) == 0
        
        # Documents should be rescanned
        assert len(document_manager.doc_metadata) >= 2
    
    def test_path_traversal_protection(self, document_manager):
        """Test path traversal attack protection"""
        # Try to access outside directory
        document_manager.available_docs["evil"] = "../../../etc/passwd"
        
        assert document_manager._validate_document_access("evil") is False
        
        with pytest.raises(DocumentNotFoundError):
            document_manager.read_document("evil")
    
    def test_file_size_limit(self, document_manager, temp_dir):
        """Test file size limit enforcement"""
        # Create large file
        large_doc = temp_dir / "docs" / "large.txt"
        large_doc.write_text("x" * (11 * 1024 * 1024), encoding='utf-8')  # 11MB
        
        document_manager.available_docs["large"] = "large.txt"
        
        with pytest.raises(DocumentAccessError) as exc_info:
            document_manager.read_document("large")
        
        assert "too large" in str(exc_info.value)


class TestDocumentIntegration:
    """Test document system integration"""
    
    def test_manager_searcher_integration(self, document_manager):
        """Test integration between manager and searcher"""
        # Search through manager
        results = document_manager.search_in_document(
            document_manager.read_document("engine_system"),
            "エントロピー"
        )
        
        assert len(results) > 0
        
        # Extract section through manager
        content = document_manager.read_document("manual")
        section = document_manager.extract_section(content, "システム概要")
        
        assert "システム概要" in section
    
    def test_cross_document_search(self, document_manager):
        """Test searching across multiple documents"""
        # Search for common term
        results = document_manager.search_all_documents("システム", max_results_per_doc=3)
        
        # Should find in multiple documents
        assert len(results) >= 1
        
        # Each result should have limited entries
        for doc_results in results.values():
            assert len(doc_results) <= 3
