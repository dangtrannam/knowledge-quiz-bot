#!/usr/bin/env python3
"""
Demo script for Knowledge Quiz Bot
This script demonstrates how to use the bot programmatically for testing
"""

import os
import sys
from knowledge_manager import KnowledgeManager
from quiz_bot import QuizBot

def create_sample_documents():
    """Create sample educational content for testing"""
    
    # AI & Machine Learning content
    ai_content = """
    Artificial Intelligence and Machine Learning
    
    Artificial Intelligence (AI) is a broad field of computer science focused on creating systems capable of performing tasks that typically require human intelligence. These tasks include learning, reasoning, problem-solving, perception, and language understanding.
    
    Machine Learning (ML) is a subset of AI that enables computers to learn and improve from experience without being explicitly programmed. Instead of following pre-programmed instructions, ML algorithms build mathematical models based on training data to make predictions or decisions.
    
    Types of Machine Learning:
    1. Supervised Learning: Uses labeled training data to learn a mapping from inputs to outputs. Examples include classification and regression tasks.
    2. Unsupervised Learning: Finds hidden patterns in data without labeled examples. Examples include clustering and dimensionality reduction.
    3. Reinforcement Learning: Learns through interaction with an environment using rewards and penalties. Examples include game playing and robotics.
    
    Deep Learning is a subset of machine learning based on artificial neural networks with multiple layers. It has been particularly successful in areas like image recognition, natural language processing, and game playing.
    
    Neural networks are inspired by the human brain and consist of interconnected nodes (neurons) that process information. Each connection has a weight that determines the strength of the signal passed between neurons.
    
    Applications of AI include autonomous vehicles, medical diagnosis, fraud detection, recommendation systems, virtual assistants, and many more domains that continue to expand as the technology advances.
    """
    
    # Python Programming content
    python_content = """
    Python Programming Fundamentals
    
    Python is a high-level, interpreted programming language known for its simplicity and readability. It was created by Guido van Rossum and first released in 1991.
    
    Key Features of Python:
    1. Easy to Learn: Python has a simple syntax that resembles natural language
    2. Interpreted: Code is executed line by line, making debugging easier
    3. Object-Oriented: Supports object-oriented programming paradigms
    4. Cross-Platform: Runs on Windows, macOS, Linux, and other operating systems
    5. Extensive Libraries: Rich standard library and third-party packages
    
    Data Types in Python:
    - Integers: Whole numbers (int)
    - Floats: Decimal numbers (float)
    - Strings: Text data (str)
    - Booleans: True/False values (bool)
    - Lists: Ordered, mutable collections
    - Tuples: Ordered, immutable collections
    - Dictionaries: Key-value pairs
    - Sets: Unordered collections of unique elements
    
    Control Structures:
    - if/elif/else statements for conditional execution
    - for loops for iterating over sequences
    - while loops for repeated execution based on conditions
    - try/except blocks for error handling
    
    Functions are reusable blocks of code that perform specific tasks. They are defined using the 'def' keyword and can accept parameters and return values.
    
    Python is widely used in web development, data science, artificial intelligence, automation, and scientific computing.
    """
    
    return {
        "AI_and_ML.txt": ai_content,
        "Python_Basics.txt": python_content
    }

def test_knowledge_manager():
    """Test the KnowledgeManager functionality"""
    print("🧪 Testing Knowledge Manager...")
    
    # Create knowledge manager
    km = KnowledgeManager()
    
    # Create sample content
    documents = create_sample_documents()
    
    # Process AI content
    print("📚 Processing AI & ML content...")
    km.process_text_content(documents["AI_and_ML.txt"], "AI & Machine Learning")
    
    # Get stats
    stats = km.get_stats()
    print(f"✅ Processed {stats['chunk_count']} text chunks from {stats['doc_count']} document(s)")
    
    # Test search functionality
    print("🔍 Testing search functionality...")
    results = km.search_knowledge_base("machine learning types", k=3)
    if results:
        print(f"Found {len(results)} relevant chunks for 'machine learning types'")
        print(f"Top result: {results[0]['content'][:100]}...")
    
    return km

def test_quiz_bot(knowledge_manager):
    """Test the QuizBot functionality"""
    print("\n🎯 Testing Quiz Bot...")
    
    # Create quiz bot
    qb = QuizBot(knowledge_manager)
    
    # Test different question types
    question_types = ["multiple_choice", "true_false", "short_answer"]
    
    for q_type in question_types:
        print(f"\n📝 Generating {q_type.replace('_', ' ').title()} question...")
        
        try:
            question = qb.generate_question(question_type=q_type, difficulty="medium")
            
            print(f"Question: {question['question']}")
            print(f"Type: {question['type']}")
            print(f"Difficulty: {question.get('difficulty', 'N/A')}")
            
            if question['type'] == 'multiple_choice':
                print("Options:")
                for option in question.get('options', []):
                    print(f"  {option}")
            
            print(f"Correct Answer: {question['correct_answer']}")
            print(f"Explanation: {question.get('explanation', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Error generating {q_type} question: {str(e)}")
    
    return qb

def test_answer_checking(quiz_bot):
    """Test answer checking functionality"""
    print("\n✅ Testing Answer Checking...")
    
    # Create a test question
    test_question = {
        "type": "multiple_choice",
        "question": "What is Machine Learning?",
        "options": ["A) A subset of AI", "B) A type of hardware", "C) A programming language", "D) A database"],
        "correct_answer": "A) A subset of AI",
        "explanation": "Machine Learning is indeed a subset of Artificial Intelligence."
    }
    
    # Test correct answer
    correct_result = quiz_bot.check_answer("A) A subset of AI", test_question)
    print(f"Correct answer test: {'✅ PASS' if correct_result else '❌ FAIL'}")
    
    # Test incorrect answer
    incorrect_result = quiz_bot.check_answer("B) A type of hardware", test_question)
    print(f"Incorrect answer test: {'✅ PASS' if not incorrect_result else '❌ FAIL'}")

def main():
    """Main demo function"""
    print("🧠 Knowledge Quiz Bot Demo")
    print("=" * 50)
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not found in environment variables")
        print("   The bot will not be able to generate questions without an API key")
        print("   Set your API key: export OPENAI_API_KEY='your-key-here'")
        return
    
    try:
        # Test Knowledge Manager
        km = test_knowledge_manager()
        
        # Test Quiz Bot
        qb = test_quiz_bot(km)
        
        # Test Answer Checking
        test_answer_checking(qb)
        
        print("\n🎉 Demo completed successfully!")
        print("\nNext steps:")
        print("1. Run 'streamlit run app.py' to start the web interface")
        print("2. Upload your own documents to create custom quizzes")
        print("3. Try different question types and difficulty levels")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        print("Make sure you have:")
        print("1. Installed all requirements: pip install -r requirements.txt")
        print("2. Set your OpenAI API key: export OPENAI_API_KEY='your-key'")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 