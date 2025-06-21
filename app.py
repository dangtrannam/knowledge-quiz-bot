import streamlit as st
import os
import json
from datetime import datetime
from quiz_bot import QuizBot
from chat_bot import ChatBot
from knowledge_manager import KnowledgeManager
from utils import setup_page_config, load_css

def main():
    setup_page_config()
    load_css()
    
    # Initialize session state
    if 'quiz_bot' not in st.session_state:
        st.session_state.quiz_bot = None
    if 'chat_bot' not in st.session_state:
        st.session_state.chat_bot = None
    if 'knowledge_manager' not in st.session_state:
        st.session_state.knowledge_manager = KnowledgeManager()
    if 'quiz_active' not in st.session_state:
        st.session_state.quiz_active = False
    if 'chat_active' not in st.session_state:
        st.session_state.chat_active = False
    if 'current_question' not in st.session_state:
        st.session_state.current_question = None
    if 'score' not in st.session_state:
        st.session_state.score = {'correct': 0, 'total': 0}
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'selected_documents' not in st.session_state:
        st.session_state.selected_documents = ['all']
    
    # Header
    st.title("🧠 Knowledge Quiz Bot")
    st.subheader("Your AI-powered learning companion, inspired by NotebookLM")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("📚 Knowledge Base")
        
        # Show preload status
        if st.session_state.knowledge_manager:
            preload_status = st.session_state.knowledge_manager.get_preload_status()
            if preload_status['is_preloaded']:
                st.success("🚀 Preloaded from previous session")
                st.caption(f"📁 {preload_status['processed_files_count']} files ready")
                # Initialize bots if not already done
                if not st.session_state.quiz_bot and preload_status['vectorstore_available']:
                    st.session_state.quiz_bot = QuizBot(st.session_state.knowledge_manager)
                if not st.session_state.chat_bot and preload_status['vectorstore_available']:
                    st.session_state.chat_bot = ChatBot(st.session_state.knowledge_manager)
            elif preload_status['processed_files_count'] > 0:
                st.info("📚 Knowledge base available")
                # Initialize bots if not already done
                if not st.session_state.quiz_bot and preload_status['vectorstore_available']:
                    st.session_state.quiz_bot = QuizBot(st.session_state.knowledge_manager)
                if not st.session_state.chat_bot and preload_status['vectorstore_available']:
                    st.session_state.chat_bot = ChatBot(st.session_state.knowledge_manager)
        
        # API Key input
        api_key = st.text_input(
            "OpenAI API Key", 
            type="password",
            help="Enter your OpenAI API key to power the quiz generation"
        )
        
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            
            # File upload section
            st.subheader("Upload Documents")
            uploaded_files = st.file_uploader(
                "Choose files to build your knowledge base",
                accept_multiple_files=True,
                type=['pdf', 'txt', 'docx'],
                help="Upload PDFs, text files, or Word documents (max 200MB per file)",
                key="file_uploader"
            )
            
            if uploaded_files:
                # Check file sizes and duplicates
                large_files = []
                duplicate_files = []
                new_files = []
                
                for file in uploaded_files:
                    file_size_mb = len(file.getvalue()) / (1024 * 1024)
                    if file_size_mb > 200:
                        large_files.append(f"{file.name} ({file_size_mb:.1f}MB)")
                    
                    # Check for duplicates
                    if st.session_state.knowledge_manager.is_file_already_processed(file):
                        duplicate_files.append(file.name)
                    else:
                        new_files.append(file.name)
                
                if large_files:
                    st.warning(f"⚠️ The following files exceed 200MB limit: {', '.join(large_files)}")
                    st.info("Please use smaller files or split large documents into chunks.")
                else:
                    # Show file info with duplicate detection
                    with st.expander("📁 Selected Files"):
                        if new_files:
                            st.success(f"**New files to process ({len(new_files)}):**")
                            for file_name in new_files:
                                file_size_mb = len([f for f in uploaded_files if f.name == file_name][0].getvalue()) / (1024 * 1024)
                                st.write(f"✅ {file_name} ({file_size_mb:.1f}MB)")
                        
                        if duplicate_files:
                            st.info(f"**Already processed ({len(duplicate_files)}):**")
                            for file_name in duplicate_files:
                                st.write(f"🔄 {file_name} (will be skipped)")
                    
                    if st.button("📖 Build Knowledge Base", type="primary"):
                        with st.spinner("Processing documents..."):
                            try:
                                result = st.session_state.knowledge_manager.process_documents(uploaded_files)
                                
                                if result['success']:
                                    st.session_state.quiz_bot = QuizBot(st.session_state.knowledge_manager)
                                    st.session_state.chat_bot = ChatBot(st.session_state.knowledge_manager)
                                    
                                    # Show detailed results
                                    if result['new_files'] > 0:
                                        st.success(f"✅ {result['message']}")
                                    
                                    if result['skipped_files'] > 0:
                                        st.info(f"ℹ️ Skipped {result['skipped_files']} already processed files: {', '.join(result['skipped_list'])}")
                                    
                                    if result['new_files'] == 0 and result['skipped_files'] > 0:
                                        st.info("All selected files were already in your knowledge base!")
                                        
                                else:
                                    st.error(f"❌ {result['message']}")
                                    if 'error' in result:
                                        st.error(f"Details: {result['error']}")
                                        
                            except Exception as e:
                                st.error(f"Error processing documents: {str(e)}")
                                st.info("💡 Try uploading one file at a time or check if the file is corrupted.")
            
            # Mode selection
            if st.session_state.quiz_bot or st.session_state.chat_bot:
                st.subheader("🎮 Choose Your Mode")
                
                mode = st.radio(
                    "What would you like to do?",
                    ["💬 Chat with Documents", "🎯 Take a Quiz"],
                    horizontal=True
                )
                
                if mode == "💬 Chat with Documents":
                    # Chat configuration
                    st.subheader("💬 Chat Settings")
                    
                    # Document selection
                    if st.session_state.chat_bot:
                        available_docs = st.session_state.chat_bot.get_available_documents()
                        
                        if available_docs:
                            doc_options = {doc['name']: doc['id'] for doc in available_docs}
                            
                            selected_doc_names = st.multiselect(
                                "Select documents to chat with:",
                                options=list(doc_options.keys()),
                                default=[available_docs[0]['name']],  # Default to "All Documents"
                                help="Choose specific documents or select 'All Documents' to chat with everything"
                            )
                            
                            if selected_doc_names:
                                st.session_state.selected_documents = [doc_options[name] for name in selected_doc_names]
                                
                                # Show selected documents info
                                with st.expander("📋 Selected Documents Details"):
                                    for doc in available_docs:
                                        if doc['id'] in st.session_state.selected_documents:
                                            st.write(f"**{doc['name']}**")
                                            st.caption(doc['description'])
                    
                    # Chat controls
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💬 Start Chat", type="primary"):
                            st.session_state.chat_active = True
                            st.session_state.quiz_active = False
                            st.rerun()
                    
                    with col2:
                        if st.button("🔄 Clear Chat History"):
                            st.session_state.chat_history = []
                            st.session_state.chat_active = False
                            st.rerun()
                
                else:  # Quiz mode
                    # Quiz configuration
                    st.subheader("🎯 Quiz Settings")
                    
                    quiz_type = st.selectbox(
                        "Quiz Type",
                        ["Multiple Choice", "True/False", "Short Answer", "Mixed"]
                    )
                    
                    difficulty = st.selectbox(
                        "Difficulty Level",
                        ["Easy", "Medium", "Hard", "Adaptive"]
                    )
                    
                    num_questions = st.slider(
                        "Number of Questions",
                        min_value=5,
                        max_value=50,
                        value=10
                    )
                    
                    # Quiz controls
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🚀 Start Quiz", type="primary"):
                            st.session_state.quiz_active = True
                            st.session_state.chat_active = False
                            st.session_state.score = {'correct': 0, 'total': 0}
                            st.rerun()
                    
                    with col2:
                        if st.button("🔄 Reset Quiz"):
                            st.session_state.quiz_active = False
                            st.session_state.current_question = None
                            st.session_state.score = {'correct': 0, 'total': 0}
                            st.rerun()
        
        else:
            st.warning("⚠️ Please enter your OpenAI API key to get started")
    
    # Main content area
    if not api_key:
        show_welcome_screen()
    elif not st.session_state.quiz_bot and not st.session_state.chat_bot:
        show_upload_prompt()
    elif st.session_state.chat_active:
        show_chat_interface()
    elif st.session_state.quiz_active:
        show_quiz_interface(quiz_type, difficulty, num_questions)
    else:
        show_knowledge_base_info()

def show_welcome_screen():
    st.markdown("""
    ## Welcome to Knowledge Quiz Bot! 🎉
    
    This AI-powered platform works just like Google's NotebookLM, offering both interactive chat and knowledge testing features.
    
    ### How it works:
    1. **📁 Upload your documents** - PDFs, text files, or Word docs
    2. **🧠 AI analyzes the content** - Extracts key concepts and facts
    3. **💬 Chat or Quiz** - Choose your learning mode
    4. **🎯 Get smart responses** - AI answers based on your documents
    5. **📊 Track your progress** - Monitor your learning journey
    
    ### Features:
    
    #### 💬 **Chat Mode**
    - **Interactive conversations** with your documents
    - **Document selection** - Chat with specific files or all documents
    - **Contextual responses** - AI answers based only on your content
    - **Source citations** - See exactly where information comes from
    
    #### 🎯 **Quiz Mode**
    - **Multiple question types** (Multiple choice, True/False, Short answer)
    - **Adaptive difficulty** - Adjusts based on your performance
    - **Detailed explanations** - Learn from both correct and incorrect answers  
    - **Progress tracking** - Monitor your learning journey
    
    **Get started by entering your OpenAI API key in the sidebar!**
    """)

def show_upload_prompt():
    st.markdown("""
    ## 📚 Ready to Build Your Knowledge Base!
    
    Upload some documents to get started. The bot will analyze them and create personalized quiz questions.
    
    ### Supported formats:
    - 📄 **PDF files** - Academic papers, textbooks, reports
    - 📝 **Text files** - Notes, articles, documentation  
    - 📋 **Word documents** - Essays, research, summaries
    
    ### Tips for best results:
    - Upload focused, high-quality content
    - Include diverse topics for varied questions
    - Ensure text is clear and well-formatted
    """)
    
    # Show example/demo content
    with st.expander("🎮 Try with Sample Content"):
        if st.button("Load Demo: AI & Machine Learning"):
            # Create sample content
            sample_content = create_sample_content()
            st.session_state.knowledge_manager.process_text_content(sample_content)
            st.session_state.quiz_bot = QuizBot(st.session_state.knowledge_manager)
            st.session_state.chat_bot = ChatBot(st.session_state.knowledge_manager)
            st.success("Demo content loaded! Ready to chat or quiz!")
            st.rerun()

def show_quiz_interface(quiz_type, difficulty, num_questions):
    # Progress bar
    progress = st.session_state.score['total'] / num_questions if num_questions > 0 else 0
    st.progress(progress)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Question", f"{st.session_state.score['total'] + 1}/{num_questions}")
    with col2:
        st.metric("Correct", st.session_state.score['correct'])
    with col3:
        accuracy = (st.session_state.score['correct'] / st.session_state.score['total'] * 100) if st.session_state.score['total'] > 0 else 0
        st.metric("Accuracy", f"{accuracy:.1f}%")
    
    # Check if quiz is complete
    if st.session_state.score['total'] >= num_questions:
        show_quiz_results()
        return
    
    # Generate or show current question
    if not st.session_state.current_question:
        with st.spinner("Generating question..."):
            st.session_state.current_question = st.session_state.quiz_bot.generate_question(
                question_type=quiz_type.lower().replace(' ', '_'),
                difficulty=difficulty.lower()
            )
    
    if st.session_state.current_question:
        question_data = st.session_state.current_question
        
        st.markdown(f"### Question {st.session_state.score['total'] + 1}")
        st.markdown(f"**{question_data['question']}**")
        
        # Handle different question types
        if question_data['type'] == 'multiple_choice':
            answer = st.radio(
                "Choose your answer:",
                question_data['options'],
                key=f"q_{st.session_state.score['total']}"
            )
            
            if st.button("Submit Answer", type="primary"):
                handle_answer_submission(answer, question_data)
        
        elif question_data['type'] == 'true_false':
            answer = st.radio(
                "Choose your answer:",
                ["True", "False"],
                key=f"q_{st.session_state.score['total']}"
            )
            
            if st.button("Submit Answer", type="primary"):
                handle_answer_submission(answer, question_data)
        
        elif question_data['type'] == 'short_answer':
            answer = st.text_input(
                "Your answer:",
                key=f"q_{st.session_state.score['total']}"
            )
            
            if st.button("Submit Answer", type="primary") and answer:
                handle_answer_submission(answer, question_data)

def handle_answer_submission(user_answer, question_data):
    is_correct = st.session_state.quiz_bot.check_answer(user_answer, question_data)
    
    # Update score
    st.session_state.score['total'] += 1
    if is_correct:
        st.session_state.score['correct'] += 1
    
    # Show feedback
    if is_correct:
        st.success("✅ Correct!")
    else:
        st.error("❌ Incorrect")
        st.info(f"**Correct answer:** {question_data['correct_answer']}")
    
    # Show explanation
    if 'explanation' in question_data:
        with st.expander("💡 Explanation"):
            st.markdown(question_data['explanation'])
            if 'source' in question_data:
                st.caption(f"Source: {question_data['source']}")
    
    # Reset for next question
    st.session_state.current_question = None
    
    # Show balloons for correct answers
    if is_correct:
        st.balloons()
    
    if st.button("Next Question →"):
        st.rerun()

def show_quiz_results():
    st.markdown("## 🎉 Quiz Complete!")
    
    score = st.session_state.score
    percentage = (score['correct'] / score['total']) * 100
    
    # Results display
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Final Score", f"{score['correct']}/{score['total']}")
    with col2:
        st.metric("Percentage", f"{percentage:.1f}%")
    with col3:
        if percentage >= 90:
            grade = "A+"
            emoji = "🌟"
        elif percentage >= 80:
            grade = "A"
            emoji = "🎯"
        elif percentage >= 70:
            grade = "B"
            emoji = "👏"
        elif percentage >= 60:
            grade = "C"
            emoji = "👍"
        else:
            grade = "D"
            emoji = "💪"
        st.metric("Grade", f"{grade} {emoji}")
    
    # Performance feedback
    if percentage >= 90:
        st.success("🌟 Outstanding! You've mastered this material!")
    elif percentage >= 70:
        st.info("🎯 Great job! You have a solid understanding.")
    elif percentage >= 50:
        st.warning("📚 Good effort! Consider reviewing the material again.")
    else:
        st.error("💪 Keep studying! Practice makes perfect.")
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Take Another Quiz", type="primary"):
            st.session_state.quiz_active = True
            st.session_state.score = {'correct': 0, 'total': 0}
            st.session_state.current_question = None
            st.rerun()
    
    with col2:
        if st.button("📊 View Knowledge Base"):
            st.session_state.quiz_active = False
            st.rerun()

def show_knowledge_base_info():
    st.markdown("## 📚 Knowledge Base Overview")
    
    if st.session_state.knowledge_manager:
        # Check preload status
        preload_status = st.session_state.knowledge_manager.get_preload_status()
        
        if preload_status['is_preloaded']:
            st.success("🚀 Knowledge base preloaded from previous session!")
        
        stats = st.session_state.knowledge_manager.get_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Documents", stats['doc_count'])
        with col2:
            st.metric("Text Chunks", stats['chunk_count'])
        with col3:
            st.metric("Total Characters", f"{stats['total_chars']:,}")
        with col4:
            st.metric("Avg Chunk Size", stats['avg_chunk_size'])
        
        # Processed files management
        processed_files = st.session_state.knowledge_manager.get_processed_files_details()
        if processed_files:
            st.subheader("📄 Processed Documents")
            
            # Show files in a nice table format
            for file_info in processed_files:
                with st.expander(f"📁 {file_info['filename']} ({file_info['file_size_mb']} MB)"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**File Type:** {file_info['file_type'].upper()}")
                        st.write(f"**Processed:** {file_info['processed_date'][:19]}")
                        st.write(f"**Size:** {file_info['file_size_mb']} MB")
                    with col2:
                        st.write(f"**Chunks:** {file_info['chunk_count']}")
                        st.write(f"**Hash:** {file_info['file_hash'][:12]}...")
                        
                        # Remove file button
                        if st.button(f"🗑️ Remove", key=f"remove_{file_info['file_hash']}", help="Remove this file from knowledge base"):
                            if st.session_state.knowledge_manager.remove_processed_file(file_info['file_hash']):
                                st.success(f"Removed {file_info['filename']}")
                                st.rerun()
                            else:
                                st.error("Failed to remove file")
        
        # Management actions
        st.subheader("🔧 Management Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Rebuild Vector Database"):
                with st.spinner("Rebuilding..."):
                    if st.session_state.knowledge_manager.rebuild_vectorstore():
                        st.success("Vector database rebuilt successfully!")
                    else:
                        st.error("Failed to rebuild vector database")
        
        with col2:
            if st.button("🗑️ Clear All Data"):
                if st.checkbox("I understand this will delete all processed documents", key="confirm_clear"):
                    st.session_state.knowledge_manager.clear_knowledge_base()
                    st.session_state.quiz_bot = None
                    st.success("Knowledge base cleared!")
                    st.rerun()
        
        with col3:
            if st.button("📊 Export Data"):
                export_data = st.session_state.knowledge_manager.export_knowledge_base()
                st.download_button(
                    "💾 Download Export",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"knowledge_base_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        # Ready to quiz section
        st.markdown("### Ready to start your quiz! 🎯")
        st.markdown("Configure your quiz settings in the sidebar and click **Start Quiz** when ready.")
        
        # Show sample questions preview
        with st.expander("🔍 Preview Sample Questions"):
            if st.button("Generate Preview"):
                sample_q = st.session_state.quiz_bot.generate_question("multiple_choice", "medium")
                if sample_q:
                    st.markdown(f"**Sample Question:** {sample_q['question']}")
                    for i, option in enumerate(sample_q.get('options', []), 1):
                        st.markdown(f"{i}. {option}")
    
    else:
        st.info("No knowledge base loaded yet.")

def show_chat_interface():
    st.markdown("## 💬 Chat with Your Documents")
    
    if not st.session_state.chat_bot:
        st.error("Chat bot not initialized. Please upload documents first.")
        return
    
    # Show selected documents info
    if st.session_state.selected_documents:
        if 'all' in st.session_state.selected_documents:
            st.info("💬 Chatting with **All Documents**")
        else:
            doc_names = []
            processed_files = st.session_state.knowledge_manager.get_processed_files_details()
            for doc_id in st.session_state.selected_documents:
                for file_info in processed_files:
                    if file_info['file_hash'] == doc_id:
                        doc_names.append(file_info['filename'])
                        break
            if doc_names:
                st.info(f"💬 Chatting with: **{', '.join(doc_names)}**")
    
    # Chat history display
    chat_container = st.container()
    
    with chat_container:
        if st.session_state.chat_history:
            for i, message in enumerate(st.session_state.chat_history):
                if message['role'] == 'user':
                    with st.chat_message("user"):
                        st.markdown(message['content'])
                else:
                    with st.chat_message("assistant"):
                        st.markdown(message['content'])
                        
                        # Show sources if available
                        if 'sources' in message and message['sources']:
                            with st.expander("📚 Sources"):
                                for source in message['sources']:
                                    st.caption(f"• {source}")
        else:
            # Show conversation starters
            st.markdown("### 🚀 Get Started")
            st.markdown("Ask me anything about your documents! Here are some suggestions:")
            
            starters = st.session_state.chat_bot.get_conversation_starters(st.session_state.selected_documents)
            
            cols = st.columns(2)
            for i, starter in enumerate(starters):
                with cols[i % 2]:
                    if st.button(starter, key=f"starter_{i}", use_container_width=True):
                        # Add user message to history
                        st.session_state.chat_history.append({
                            'role': 'user',
                            'content': starter
                        })
                        
                        # Generate response
                        with st.spinner("Thinking..."):
                            result = st.session_state.chat_bot.generate_response(
                                starter, 
                                st.session_state.selected_documents,
                                st.session_state.chat_history[:-1]  # Exclude the just-added message
                            )
                            
                            if result['success']:
                                # Add assistant response to history
                                response_data = {
                                    'role': 'assistant',
                                    'content': result['response']
                                }
                                if 'sources' in result:
                                    response_data['sources'] = result['sources']
                                
                                st.session_state.chat_history.append(response_data)
                            else:
                                st.session_state.chat_history.append({
                                    'role': 'assistant',
                                    'content': f"❌ {result['error']}"
                                })
                        
                        st.rerun()
    
    # Chat input
    user_input = st.chat_input("Ask me anything about your documents...")
    
    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })
        
        # Generate response
        with st.spinner("Thinking..."):
            result = st.session_state.chat_bot.generate_response(
                user_input, 
                st.session_state.selected_documents,
                st.session_state.chat_history[:-1]  # Exclude the just-added message
            )
            
            if result['success']:
                # Add assistant response to history
                response_data = {
                    'role': 'assistant',
                    'content': result['response']
                }
                if 'sources' in result:
                    response_data['sources'] = result['sources']
                
                st.session_state.chat_history.append(response_data)
            else:
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': f"❌ {result['error']}"
                })
        
        st.rerun()
    
    # Chat controls in sidebar
    with st.sidebar:
        st.markdown("---")
        st.subheader("💬 Chat Controls")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 New Chat"):
                st.session_state.chat_history = []
                st.rerun()
        
        with col2:
            if st.button("📊 Back to Overview"):
                st.session_state.chat_active = False
                st.rerun()
        
        # Show chat stats
        if st.session_state.chat_history:
            st.markdown("### 📈 Chat Stats")
            user_messages = len([m for m in st.session_state.chat_history if m['role'] == 'user'])
            assistant_messages = len([m for m in st.session_state.chat_history if m['role'] == 'assistant'])
            st.metric("Messages", f"{user_messages + assistant_messages}")
            st.metric("Questions Asked", user_messages)

def create_sample_content():
    return """
    Artificial Intelligence and Machine Learning
    
    Artificial Intelligence (AI) is a broad field of computer science focused on creating systems capable of performing tasks that typically require human intelligence. These tasks include learning, reasoning, problem-solving, perception, and language understanding.
    
    Machine Learning (ML) is a subset of AI that enables computers to learn and improve from experience without being explicitly programmed. Instead of following pre-programmed instructions, ML algorithms build mathematical models based on training data to make predictions or decisions.
    
    Types of Machine Learning:
    1. Supervised Learning: Uses labeled training data to learn a mapping from inputs to outputs
    2. Unsupervised Learning: Finds hidden patterns in data without labeled examples  
    3. Reinforcement Learning: Learns through interaction with an environment using rewards and penalties
    
    Deep Learning is a subset of machine learning based on artificial neural networks with multiple layers. It has been particularly successful in areas like image recognition, natural language processing, and game playing.
    
    Applications of AI include autonomous vehicles, medical diagnosis, fraud detection, recommendation systems, virtual assistants, and many more domains that continue to expand as the technology advances.
    """

if __name__ == "__main__":
    main() 