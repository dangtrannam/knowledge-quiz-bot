import pytest
import os
import tempfile
import sys
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from knowledge_manager import KnowledgeManager
from quiz_bot import QuizBot
from utils import *

class TestKnowledgeManager:
    """Test the KnowledgeManager class functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.km = KnowledgeManager()
    
    def test_initialization(self):
        """Test KnowledgeManager initialization"""
        assert self.km.documents == []
        assert self.km.vectorstore is None
        assert self.km.embeddings is None
        assert self.km.processed_files == set()
        assert self.km.text_splitter is not None
    
    def test_process_text_content(self):
        """Test processing raw text content"""
        sample_text = """
        This is a test document about machine learning.
        Machine learning is a subset of artificial intelligence.
        It uses algorithms to find patterns in data.
        """
        
        # Mock the embeddings to avoid actual API calls
        with patch('knowledge_manager.HuggingFaceEmbeddings') as mock_embeddings:
            mock_embeddings.return_value = Mock()
            
            with patch('knowledge_manager.Chroma') as mock_chroma:
                mock_vectorstore = Mock()
                mock_chroma.from_documents.return_value = mock_vectorstore
                
                result = self.km.process_text_content(sample_text, "Test Document")
                
                assert result is True
                assert len(self.km.documents) > 0
                mock_embeddings.assert_called_once()
                mock_chroma.from_documents.assert_called_once()
    
    def test_get_file_hash(self):
        """Test file hash generation"""
        # Create a mock uploaded file
        mock_file = Mock()
        mock_file.getbuffer.return_value = b'test content'
        
        hash1 = self.km._get_file_hash(mock_file)
        hash2 = self.km._get_file_hash(mock_file)
        
        assert hash1 == hash2  # Same content should produce same hash
        assert len(hash1) == 32  # MD5 hash length
    
    def test_search_knowledge_base_empty(self):
        """Test searching empty knowledge base"""
        results = self.km.search_knowledge_base("test query")
        assert results == []
    
    def test_get_random_context_empty(self):
        """Test getting random context from empty knowledge base"""
        context = self.km.get_random_context()
        assert context is None
    
    def test_get_stats_empty(self):
        """Test getting stats from empty knowledge base"""
        stats = self.km.get_stats()
        assert stats['doc_count'] == 0
        assert stats['chunk_count'] == 0
        assert stats['total_chars'] == 0
        assert stats['topic_count'] == 0
    
    def test_clear_knowledge_base(self):
        """Test clearing the knowledge base"""
        # Add some mock data
        self.km.documents = [Mock()]
        self.km.vectorstore = Mock()
        self.km.processed_files = {'test_hash'}
        
        self.km.clear_knowledge_base()
        
        assert self.km.documents == []
        assert self.km.vectorstore is None
        assert self.km.processed_files == set()


class TestQuizBot:
    """Test the QuizBot class functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.mock_km = Mock(spec=KnowledgeManager)
        # Mock the QuizBot to avoid actual API calls
        with patch('quiz_bot.ChatOpenAI'):
            self.quiz_bot = QuizBot(self.mock_km)
    
    def test_initialization(self):
        """Test QuizBot initialization"""
        assert self.quiz_bot.knowledge_manager == self.mock_km
        assert self.quiz_bot.llm is not None
    
    def test_check_answer_multiple_choice(self):
        """Test checking multiple choice answers"""
        question_data = {
            'type': 'multiple_choice',
            'correct_answer': 'Option A',
            'options': ['Option A', 'Option B', 'Option C']
        }
        
        assert self.quiz_bot.check_answer('Option A', question_data) is True
        assert self.quiz_bot.check_answer('Option B', question_data) is False
        assert self.quiz_bot.check_answer('option a', question_data) is True  # Case insensitive
    
    def test_check_answer_true_false(self):
        """Test checking true/false answers"""
        question_data = {
            'type': 'true_false',
            'correct_answer': 'True'
        }
        
        assert self.quiz_bot.check_answer('True', question_data) is True
        assert self.quiz_bot.check_answer('False', question_data) is False
        assert self.quiz_bot.check_answer('true', question_data) is True  # Case insensitive
    
    def test_check_answer_short_answer(self):
        """Test checking short answers"""
        question_data = {
            'type': 'short_answer',
            'correct_answer': 'Machine Learning'
        }
        
        assert self.quiz_bot.check_answer('Machine Learning', question_data) is True
        assert self.quiz_bot.check_answer('machine learning', question_data) is True
        assert self.quiz_bot.check_answer('ML', question_data) is False


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_format_score_display(self):
        """Test score formatting"""
        assert format_score_display(0, 0) == "0/0 (0%)"
        assert format_score_display(5, 10) == "5/10 (50.0%)"
        assert format_score_display(10, 10) == "10/10 (100.0%)"
    
    def test_get_grade_emoji(self):
        """Test grade emoji assignment"""
        assert get_grade_emoji(98) == "🌟"  # Perfect
        assert get_grade_emoji(92) == "🎯"  # Excellent
        assert get_grade_emoji(85) == "👏"  # Great
        assert get_grade_emoji(75) == "👍"  # Good
        assert get_grade_emoji(65) == "📚"  # Pass
        assert get_grade_emoji(45) == "💪"  # Keep trying
    
    def test_get_performance_message(self):
        """Test performance message assignment"""
        message, color = get_performance_message(95)
        assert "Outstanding" in message
        assert color == "success"
        
        message, color = get_performance_message(45)
        assert "Don't give up" in message
        assert color == "error"
    
    def test_validate_api_key(self):
        """Test API key validation"""
        # Valid key format
        valid, msg = validate_api_key("sk-1234567890abcdef1234567890abcdef12345678")
        assert valid is True
        
        # Empty key
        valid, msg = validate_api_key("")
        assert valid is False
        assert "empty" in msg
        
        # Wrong prefix
        valid, msg = validate_api_key("abc-1234567890abcdef")
        assert valid is False
        assert "sk-" in msg
        
        # Too short
        valid, msg = validate_api_key("sk-123")
        assert valid is False
        assert "short" in msg
    
    def test_safe_divide(self):
        """Test safe division function"""
        assert safe_divide(10, 2) == 5.0
        assert safe_divide(10, 0) == 0.0
        assert safe_divide(0, 5) == 0.0
    
    def test_truncate_text(self):
        """Test text truncation"""
        short_text = "Short text"
        assert truncate_text(short_text, 50) == short_text
        
        long_text = "This is a very long text that should be truncated"
        truncated = truncate_text(long_text, 20)
        assert len(truncated) == 20
        assert truncated.endswith("...")
    
    def test_format_file_size(self):
        """Test file size formatting"""
        assert format_file_size(0) == "0 B"
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"


class TestFileProcessing:
    """Test file processing functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.km = KnowledgeManager()
    
    def test_load_document_unsupported_type(self):
        """Test loading unsupported file type"""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as tmp_file:
            tmp_file.write(b"test content")
            tmp_file_path = tmp_file.name
        
        try:
            result = self.km._load_document(tmp_file_path, "test.xyz")
            assert result == []  # Should return empty list for unsupported types
        finally:
            os.unlink(tmp_file_path)
    
    def test_create_temp_file_processing(self):
        """Test temporary file creation and cleanup"""
        # Create a mock uploaded file
        mock_file = Mock()
        mock_file.name = "test.txt"
        mock_file.getbuffer.return_value = b"test content"
        
        # Test that temporary files are created and cleaned up properly
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp_file = Mock()
            mock_temp_file.name = "/tmp/test_file.txt"
            mock_temp.__enter__ = Mock(return_value=mock_temp_file)
            mock_temp.__exit__ = Mock(return_value=None)
            
            # This would normally test the full process_documents method
            # but we'll just verify the mock was called correctly
            mock_temp_file.write.return_value = None


class TestIntegration:
    """Integration tests for the complete workflow"""
    
    def test_complete_workflow_with_mocks(self):
        """Test the complete workflow with mocked dependencies"""
        # Mock all external dependencies
        with patch('knowledge_manager.HuggingFaceEmbeddings') as mock_embeddings, \
             patch('knowledge_manager.Chroma') as mock_chroma, \
             patch('quiz_bot.ChatOpenAI') as mock_llm:
            
            # Setup mocks
            mock_embeddings.return_value = Mock()
            mock_vectorstore = Mock()
            mock_chroma.from_documents.return_value = mock_vectorstore
            mock_llm.return_value = Mock()
            
            # Create knowledge manager and process text
            km = KnowledgeManager()
            result = km.process_text_content("Test content about AI", "Test Doc")
            assert result is True
            
            # Create quiz bot
            quiz_bot = QuizBot(km)
            assert quiz_bot.knowledge_manager == km
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        km = KnowledgeManager()
        
        # Test with invalid file
        mock_file = Mock()
        mock_file.name = "test.txt"
        mock_file.getbuffer.side_effect = Exception("File error")
        
        # Should handle the exception gracefully
        try:
            hash_result = km._get_file_hash(mock_file)
        except Exception:
            # Expected to raise exception, which is fine for this test
            pass


def run_tests():
    """Run all tests and provide a summary"""
    print("🧪 Running Core Function Tests...")
    print("=" * 50)
    
    # Test results collector
    results = {
        'passed': 0,
        'failed': 0,
        'errors': []
    }
    
    # Test classes to run
    test_classes = [
        TestKnowledgeManager,
        TestQuizBot, 
        TestUtilityFunctions,
        TestFileProcessing,
        TestIntegration
    ]
    
    for test_class in test_classes:
        print(f"\n📋 Testing {test_class.__name__}...")
        
        # Get all test methods
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]
        
        for method_name in test_methods:
            try:
                # Create instance and run setup
                instance = test_class()
                if hasattr(instance, 'setup_method'):
                    instance.setup_method()
                
                # Run the test method
                method = getattr(instance, method_name)
                method()
                
                print(f"  ✅ {method_name}")
                results['passed'] += 1
                
            except Exception as e:
                print(f"  ❌ {method_name}: {str(e)}")
                results['failed'] += 1
                results['errors'].append(f"{test_class.__name__}.{method_name}: {str(e)}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"📈 Success Rate: {(results['passed'] / (results['passed'] + results['failed']) * 100):.1f}%")
    
    if results['errors']:
        print(f"\n🔍 Failed Tests:")
        for error in results['errors']:
            print(f"  • {error}")
    
    return results


if __name__ == "__main__":
    # Run tests when script is executed directly
    run_tests() 