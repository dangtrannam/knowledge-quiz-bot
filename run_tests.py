#!/usr/bin/env python3
"""
Simple test runner for the Knowledge Quiz Bot
Verifies core functionality without requiring pytest
"""

import sys
import os
import traceback
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing module imports...")
    
    test_results = []
    
    modules_to_test = [
        ('streamlit', 'st'),
        ('knowledge_manager', 'KnowledgeManager'),
        ('quiz_bot', 'QuizBot'),  
        ('utils', 'format_score_display'),
        ('langchain_community.embeddings', 'HuggingFaceEmbeddings'),
        ('langchain_community.vectorstores', 'Chroma'),
    ]
    
    for module_name, item_name in modules_to_test:
        try:
            if '.' in module_name:
                module = __import__(module_name, fromlist=[item_name])
                getattr(module, item_name)
            else:
                module = __import__(module_name)
                if item_name != module_name:
                    getattr(module, item_name)
            
            print(f"  ✅ {module_name}.{item_name}")
            test_results.append(True)
        except ImportError as e:
            print(f"  ❌ {module_name}.{item_name} - Import Error: {e}")
            test_results.append(False)
        except AttributeError as e:
            print(f"  ❌ {module_name}.{item_name} - Attribute Error: {e}")
            test_results.append(False)
        except Exception as e:
            print(f"  ❌ {module_name}.{item_name} - Error: {e}")
            test_results.append(False)
    
    return test_results

def test_knowledge_manager():
    """Test KnowledgeManager basic functionality"""
    print("\n📚 Testing KnowledgeManager...")
    
    test_results = []
    
    try:
        from knowledge_manager import KnowledgeManager
        
        # Test initialization
        km = KnowledgeManager()
        assert km.documents == []
        assert km.vectorstore is None
        assert km.processed_files == set()
        print("  ✅ Initialization")
        test_results.append(True)
        
        # Test stats on empty knowledge base
        stats = km.get_stats()
        assert isinstance(stats, dict)
        assert stats['doc_count'] == 0
        assert stats['chunk_count'] == 0
        print("  ✅ Empty stats")
        test_results.append(True)
        
        # Test search on empty knowledge base
        results = km.search_knowledge_base("test query")
        assert results == []
        print("  ✅ Empty search")
        test_results.append(True)
        
        # Test file hash function
        from unittest.mock import Mock
        mock_file = Mock()
        mock_file.getbuffer.return_value = b'test content'
        hash1 = km._get_file_hash(mock_file)
        hash2 = km._get_file_hash(mock_file)
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hash
        print("  ✅ File hashing")
        test_results.append(True)
        
    except Exception as e:
        print(f"  ❌ KnowledgeManager test failed: {e}")
        test_results.append(False)
        traceback.print_exc()
    
    return test_results

def test_quiz_bot():
    """Test QuizBot basic functionality"""
    print("\n🧠 Testing QuizBot...")
    
    test_results = []
    
    try:
        from unittest.mock import Mock, patch
        from quiz_bot import QuizBot
        from knowledge_manager import KnowledgeManager
        
        # Create mock knowledge manager
        mock_km = Mock(spec=KnowledgeManager)
        
        # Test initialization with mocked dependencies
        with patch('quiz_bot.ChatOpenAI') as mock_llm:
            mock_llm.return_value = Mock()
            quiz_bot = QuizBot(mock_km)
            
            assert quiz_bot.knowledge_manager == mock_km
            print("  ✅ Initialization")
            test_results.append(True)
            
            # Test answer checking - multiple choice
            question_data = {
                'type': 'multiple_choice',
                'correct_answer': 'Option A',
                'options': ['Option A', 'Option B', 'Option C']
            }
            
            assert quiz_bot.check_answer('Option A', question_data) is True
            assert quiz_bot.check_answer('Option B', question_data) is False
            assert quiz_bot.check_answer('option a', question_data) is True  # Case insensitive
            print("  ✅ Multiple choice answers")
            test_results.append(True)
            
            # Test answer checking - true/false
            question_data = {
                'type': 'true_false',
                'correct_answer': 'True'
            }
            
            assert quiz_bot.check_answer('True', question_data) is True
            assert quiz_bot.check_answer('False', question_data) is False
            assert quiz_bot.check_answer('true', question_data) is True
            print("  ✅ True/False answers")
            test_results.append(True)
            
            # Test answer checking - short answer
            question_data = {
                'type': 'short_answer',
                'correct_answer': 'Machine Learning'
            }
            
            assert quiz_bot.check_answer('Machine Learning', question_data) is True
            assert quiz_bot.check_answer('machine learning', question_data) is True
            assert quiz_bot.check_answer('Deep Learning', question_data) is False
            print("  ✅ Short answers")
            test_results.append(True)
        
    except Exception as e:
        print(f"  ❌ QuizBot test failed: {e}")
        test_results.append(False)
        traceback.print_exc()
    
    return test_results

def test_utils():
    """Test utility functions"""
    print("\n🛠️ Testing Utility Functions...")
    
    test_results = []
    
    try:
        from utils import (
            format_score_display, get_grade_emoji, get_performance_message,
            validate_api_key, safe_divide, truncate_text, format_file_size
        )
        
        # Test score formatting
        assert format_score_display(0, 0) == "0/0 (0%)"
        assert format_score_display(5, 10) == "5/10 (50.0%)"
        assert format_score_display(10, 10) == "10/10 (100.0%)"
        print("  ✅ Score formatting")
        test_results.append(True)
        
        # Test grade emojis
        assert get_grade_emoji(98) == "🌟"
        assert get_grade_emoji(85) == "👏"
        assert get_grade_emoji(45) == "💪"
        print("  ✅ Grade emojis")
        test_results.append(True)
        
        # Test performance messages
        message, color = get_performance_message(95)
        assert "Outstanding" in message
        assert color == "success"
        print("  ✅ Performance messages")
        test_results.append(True)
        
        # Test API key validation
        valid, msg = validate_api_key("sk-1234567890abcdef1234567890abcdef12345678")
        assert valid is True
        
        valid, msg = validate_api_key("")
        assert valid is False
        print("  ✅ API key validation")
        test_results.append(True)
        
        # Test safe division
        assert safe_divide(10, 2) == 5.0
        assert safe_divide(10, 0) == 0.0
        print("  ✅ Safe division")
        test_results.append(True)
        
        # Test text truncation
        long_text = "This is a very long text that should be truncated"
        truncated = truncate_text(long_text, 20)
        assert len(truncated) == 20
        assert truncated.endswith("...")
        print("  ✅ Text truncation")
        test_results.append(True)
        
        # Test file size formatting
        assert format_file_size(0) == "0 B"
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1024 * 1024) == "1.0 MB"
        print("  ✅ File size formatting")
        test_results.append(True)
        
    except Exception as e:
        print(f"  ❌ Utils test failed: {e}")
        test_results.append(False)
        traceback.print_exc()
    
    return test_results

def test_file_operations():
    """Test file operations"""
    print("\n📁 Testing File Operations...")
    
    test_results = []
    
    try:
        import tempfile
        from knowledge_manager import KnowledgeManager
        
        km = KnowledgeManager()
        
        # Test unsupported file type
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as tmp_file:
            tmp_file.write(b"test content")
            tmp_file_path = tmp_file.name
        
        try:
            result = km._load_document(tmp_file_path, "test.xyz")
            assert result == []  # Should return empty list for unsupported types
            print("  ✅ Unsupported file handling")
            test_results.append(True)
        finally:
            os.unlink(tmp_file_path)
        
    except Exception as e:
        print(f"  ❌ File operations test failed: {e}")
        test_results.append(False)
        traceback.print_exc()
    
    return test_results

def test_configuration():
    """Test configuration files"""
    print("\n⚙️ Testing Configuration...")
    
    test_results = []
    
    try:
        # Check if config file exists
        config_path = ".streamlit/config.toml"
        if os.path.exists(config_path):
            print("  ✅ Streamlit config file exists")
            test_results.append(True)
            
            # Read and validate config
            with open(config_path, 'r') as f:
                config_content = f.read()
                if 'maxUploadSize' in config_content:
                    print("  ✅ Upload size configuration found")
                    test_results.append(True)
                else:
                    print("  ❌ Upload size configuration missing")
                    test_results.append(False)
        else:
            print("  ❌ Streamlit config file not found")
            test_results.append(False)
        
        # Check requirements file
        if os.path.exists("requirements.txt"):
            print("  ✅ Requirements file exists")
            test_results.append(True)
            
            with open("requirements.txt", 'r') as f:
                requirements = f.read()
                required_packages = ['streamlit', 'langchain', 'sentence-transformers', 'pypdf']
                for package in required_packages:
                    if package in requirements:
                        print(f"    ✅ {package} found in requirements")
                    else:
                        print(f"    ❌ {package} missing from requirements")
        else:
            print("  ❌ Requirements file not found")
            test_results.append(False)
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        test_results.append(False)
        traceback.print_exc()
    
    return test_results

def main():
    """Run all tests"""
    print("🚀 Knowledge Quiz Bot - Core Function Tests")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    all_results = []
    
    # Run all test suites
    test_suites = [
        ("Module Imports", test_imports),
        ("KnowledgeManager", test_knowledge_manager),
        ("QuizBot", test_quiz_bot),
        ("Utility Functions", test_utils),
        ("File Operations", test_file_operations),
        ("Configuration", test_configuration)
    ]
    
    for suite_name, test_function in test_suites:
        try:
            results = test_function()
            all_results.extend(results)
        except Exception as e:
            print(f"❌ Test suite '{suite_name}' failed: {e}")
            all_results.append(False)
    
    # Calculate summary
    total_tests = len(all_results)
    passed_tests = sum(all_results)
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 60)
    print(f"🔥 Total Tests Run: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"📈 Success Rate: {success_rate:.1f}%")
    print("=" * 60)
    
    if success_rate >= 90:
        print("🎉 EXCELLENT! Your core functions are working great!")
    elif success_rate >= 70:
        print("👍 GOOD! Most core functions are working properly.")
    elif success_rate >= 50:
        print("⚠️ WARNING! Some core functions need attention.")
    else:
        print("🚨 CRITICAL! Major issues detected with core functions.")
    
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return success_rate >= 70  # Return True if tests are mostly passing

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 