import streamlit as st
import os
import json
from datetime import datetime
from knowledge_manager import KnowledgeManager
from agents.quiz_agent import QuizAgent
from agents.chat_agent import ChatAgent
from ui.utils import setup_page_config, load_css
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more detail
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

load_dotenv()

# Helper to get preload status from KnowledgeManager
# (add this method to KnowledgeManager if not present)
def get_preload_status(km):
    return {
        'is_preloaded': getattr(km, 'is_preloaded', False),
        'processed_files_count': len(getattr(km, 'processed_files', {})),
        'processed_files': list(getattr(km, 'processed_files', {}).keys()),
        'vectorstore_available': getattr(km, 'vectorstore', None) is not None,
        'embeddings_ready': getattr(getattr(km, 'embedder', None), 'get', lambda: None)() is not None
    }

def get_knowledge_manager():
    """Safely get knowledge manager with error handling"""
    km = st.session_state.get('knowledge_manager')
    if km is None:
        st.error("❌ Knowledge Manager not available. Please refresh the page.")
        st.stop()
    return km

# Demo content for testing
demo_content = {
    "ai_ml": """
    # Introduction to Artificial Intelligence and Machine Learning

    Artificial Intelligence (AI) is a broad field of computer science that aims to create intelligent machines capable of performing tasks that typically require human intelligence. These tasks include visual perception, speech recognition, decision-making, and language translation.

    ## Machine Learning Fundamentals

    Machine Learning (ML) is a subset of artificial intelligence that focuses on the development of algorithms and statistical models that enable computer systems to improve their performance on a specific task through experience, without being explicitly programmed.

    ### Types of Machine Learning

    1. **Supervised Learning**: Uses labeled training data to learn a mapping function from inputs to outputs. Examples include classification and regression tasks.

    2. **Unsupervised Learning**: Finds hidden patterns or intrinsic structures in input data without labeled examples. Common techniques include clustering and dimensionality reduction.

    3. **Reinforcement Learning**: An agent learns to make decisions by taking actions in an environment to maximize cumulative reward.

    ### Key Concepts

    **Training Data**: The dataset used to teach machine learning algorithms. Quality and quantity of training data significantly impact model performance.

    **Features**: Individual measurable properties of observed phenomena. Feature selection and engineering are crucial for model success.

    **Model**: The mathematical representation of a real-world process. Models are trained on data and used to make predictions or decisions.

    **Overfitting**: When a model learns the training data too well, including noise, resulting in poor generalization to new data.

    **Cross-validation**: A technique for assessing how well a model will generalize to an independent dataset.

    ## Deep Learning

    Deep Learning is a subset of machine learning based on artificial neural networks with multiple layers. These networks can automatically discover representations from data, making them particularly effective for complex tasks like image recognition and natural language processing.

    ### Neural Networks

    Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes (neurons) organized in layers:

    - **Input Layer**: Receives the initial data
    - **Hidden Layers**: Process the data through weighted connections
    - **Output Layer**: Produces the final result

    ### Common Applications

    - **Computer Vision**: Image classification, object detection, facial recognition
    - **Natural Language Processing**: Language translation, sentiment analysis, chatbots
    - **Speech Recognition**: Converting speech to text, voice assistants
    - **Recommendation Systems**: Personalized content suggestions
    - **Autonomous Vehicles**: Self-driving car navigation and decision-making

    ## Getting Started with Machine Learning

    1. **Learn the Fundamentals**: Understand statistics, linear algebra, and programming
    2. **Choose Tools**: Popular options include Python (scikit-learn, TensorFlow, PyTorch) and R
    3. **Practice with Datasets**: Work with real data to build practical experience
    4. **Join Communities**: Participate in forums, competitions, and open-source projects
    5. **Stay Updated**: Follow research papers, blogs, and industry developments

    Machine learning is rapidly evolving, with new techniques and applications emerging regularly. Success requires continuous learning and adaptation to new methodologies and technologies.
    """
}

# Helper to get available documents from KnowledgeManager
# (add this method to ChatAgent if not present)
def get_available_documents(km):
    processed_files = getattr(km, 'processed_files', {})
    documents = []
    documents.append({
        'id': 'all',
        'name': '📚 All Documents',
        'description': f'Chat with all {len(processed_files)} documents'
    })
    for file_hash, metadata in processed_files.items():
        documents.append({
            'id': file_hash,
            'name': f"📄 {metadata.get('filename', 'Unknown')}",
            'description': f"{metadata.get('file_type', '').upper()} • {metadata.get('chunk_count', 0)} chunks • {round(metadata.get('file_size', 0) / (1024 * 1024), 2)} MB"
        })
    return documents

def main():
    setup_page_config()
    load_css()
    
    # Initialize session state
    if 'quiz_bot' not in st.session_state:
        st.session_state.quiz_bot = None
    if 'chat_bot' not in st.session_state:
        st.session_state.chat_bot = None
    if 'knowledge_manager' not in st.session_state:
        try:
            st.session_state.knowledge_manager = KnowledgeManager()
            # Check if embeddings are working
            if hasattr(st.session_state.knowledge_manager, 'embedder'):
                if not st.session_state.knowledge_manager.embedder.is_ready():
                    st.warning("⚠️ Embedding model failed to initialize. Some features may not work properly.")
                    st.info("💡 Try refreshing the page or check your system's torch/CUDA installation.")
        except Exception as e:
            st.error(f"❌ Failed to initialize Knowledge Manager: {str(e)}")
            st.info("💡 Try refreshing the page. If the problem persists, check system requirements.")
            # Initialize with a placeholder to prevent repeated errors
            st.session_state.knowledge_manager = None
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
    if 'openai_base_url' not in st.session_state:
        st.session_state.openai_base_url = "https://aiportalapi.stu-platform.live/jpe"
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = "GPT-4o-mini"
    if 'model_input_type' not in st.session_state:
        st.session_state.model_input_type = "predefined"
    if 'custom_model' not in st.session_state:
        st.session_state.custom_model = ""
    
    # Header
    st.title("🧠 Knowledge Quiz Bot")
    st.subheader("Your AI-powered learning companion, inspired by NotebookLM")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("📚 Knowledge Base")
        
        # Show preload status
        if st.session_state.knowledge_manager:
            preload_status = get_preload_status(st.session_state.knowledge_manager)
            if preload_status['is_preloaded']:
                st.success("🚀 Preloaded from previous session")
                st.caption(f"📁 {preload_status['processed_files_count']} files ready")
                # Initialize agents with credentials
                try:
                    km = get_knowledge_manager()
                    if km.retriever:
                        st.session_state.quiz_bot = QuizAgent(km.retriever)
                        st.session_state.chat_bot = ChatAgent(km.retriever)
                        # Don't automatically activate modes - let user choose
                    else:
                        st.warning("⚠️ No documents loaded. Please upload and process documents first.")
                except Exception as e:
                    st.error(f"Failed to initialize agents: {e}")
            elif preload_status['processed_files_count'] > 0:
                st.info("📚 Knowledge base available")
                # Initialize agents for demo mode
                try:
                    km = get_knowledge_manager()
                    if km.retriever:
                        st.session_state.quiz_bot = QuizAgent(km.retriever)
                        st.session_state.chat_bot = ChatAgent(km.retriever)
                        # Don't automatically activate modes - let user choose
                    else:
                        st.warning("⚠️ No documents loaded. Please upload and process documents first.")
                except Exception as e:
                    st.error(f"Failed to initialize agents: {e}")
        
        # API Configuration
        st.subheader("🔧 API Configuration")
        
        api_key = st.text_input(
            "OpenAI API Key", 
            type="password",
            help="Enter your OpenAI API key to power the AI features"
        )
        
        # Advanced API settings in an expander
        with st.expander("⚙️ Advanced Settings"):
            base_url = st.text_input(
                "Base URL (Optional)",
                value=st.session_state.openai_base_url,
                placeholder="https://aiportalapi.stu-platform.live/jpe",
                help="Custom base URL for OpenAI-compatible APIs (leave empty for default)",
            )
            
            # Model selection type
            model_input_type = st.radio(
                "Model Selection",
                options=["predefined", "custom"],
                format_func=lambda x: "📋 Select from List" if x == "predefined" else "✏️ Custom Model",
                horizontal=True,
                help="Choose to select from predefined models or enter a custom model name"
            )
            
            # Model selection based on type
            if model_input_type == "predefined":
                predefined_models = [
                    'GPT-4o-mini',
                    "gpt-3.5-turbo",
                    "gpt-4o",
                    "gpt-4o-mini",
                ]
                
                # Ensure current model is in the list or default to first option
                current_model_index = 0
                if st.session_state.selected_model in predefined_models:
                    current_model_index = predefined_models.index(st.session_state.selected_model)
                
                selected_model = st.selectbox(
                    "AI Model",
                    options=predefined_models,
                    index=current_model_index,
                    help="Choose the AI model to use for generation"
                )
                
                # Update session state
                st.session_state.selected_model = selected_model
                st.session_state.custom_model = ""
                
            else:  # custom model
                custom_model = st.text_input(
                    "Custom Model Name",
                    value=st.session_state.custom_model,
                    placeholder="e.g., gpt-4-1106-preview, claude-3-opus, custom-model-name",
                    help="Enter the exact model name as expected by your API"
                )
                
                # Show helpful examples
                st.info("""
                💡 **Custom Model Examples:**
                
                **OpenAI Models:**
                • `gpt-4-1106-preview` (Latest GPT-4 Turbo)
                • `gpt-4-vision-preview` (GPT-4 with vision)
                • `gpt-3.5-turbo-1106` (Latest GPT-3.5)
                
                **Other APIs (with custom base URL):**
                • `claude-3-opus-20240229` (Anthropic)
                • `claude-3-sonnet-20240229` (Anthropic)
                • `mistral-large-latest` (Mistral AI)
                • `llama-2-70b-chat` (Local/Ollama)
                
                **Note:** Make sure your API endpoint supports the model you specify.
                """)
                
                if custom_model and custom_model.strip():
                    selected_model = custom_model.strip()
                    st.session_state.selected_model = selected_model
                    st.session_state.custom_model = custom_model.strip()
                    
                    # Basic validation and warnings
                    if ' ' in selected_model:
                        st.warning("⚠️ Model names usually don't contain spaces. Please check your model name.")
                    elif selected_model.startswith('gpt') and not any(x in selected_model for x in ['3.5', '4']):
                        st.info("ℹ️ Make sure this is a valid GPT model variant.")
                    elif len(selected_model) < 3:
                        st.warning("⚠️ Model name seems too short. Please verify it's correct.")
                else:
                    # Fallback to default if custom model is empty
                    selected_model = "gpt-3.5-turbo"
                    st.session_state.selected_model = selected_model
                    if not custom_model:  # Only clear if completely empty
                        st.session_state.custom_model = ""
            
            # Update session state
            st.session_state.openai_base_url = base_url
            st.session_state.model_input_type = model_input_type
            
            # Show current settings
            st.caption(f"**Current Model:** {selected_model}")
            if model_input_type == "custom" and selected_model:
                if selected_model in ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini"]:
                    st.caption("ℹ️ This looks like a standard model - you could use the predefined list")
                else:
                    st.caption("✏️ Using custom model")
            
            if base_url:
                st.caption(f"**Base URL:** {base_url}")
            else:
                st.caption("**Base URL:** Default (OpenAI)")
            
            # Reset configuration button
            if st.button("🔄 Reset AI Configuration", help="Clear cached clients and reinitialize with new settings"):
                # Clear cached clients by resetting bot instances
                if st.session_state.chat_bot:
                    st.session_state.chat_bot.client = None
                    st.session_state.chat_bot._last_config = None
                if st.session_state.quiz_bot:
                    st.session_state.quiz_bot.llm = None
                    st.session_state.quiz_bot._last_config = None
                # Reset model configuration to defaults
                st.session_state.model_input_type = "predefined"
                st.session_state.selected_model = "GPT-4o-mini"
                st.session_state.custom_model = ""
                st.session_state.openai_base_url = ""
                st.success("🔄 AI configuration reset to defaults! Changes will take effect on next use.")
                st.rerun()
            
            # Debug section for troubleshooting
            st.markdown("**🔧 Debug & Troubleshooting**")
            col_debug1, col_debug2 = st.columns(2)
            
            with col_debug1:
                if st.button("🗑️ Clear Vector Store", help="Clear all vector store data to resolve source reference issues"):
                    try:
                        km = get_knowledge_manager()
                        km.clear_knowledge_base()
                        st.session_state.quiz_bot = None
                        st.session_state.chat_bot = None
                        st.session_state.chat_active = False
                        st.session_state.quiz_active = False
                        st.success("✅ Vector store cleared! Please re-upload your documents.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error clearing vector store: {e}")
            
            with col_debug2:
                if st.button("📋 Show Vector Store Info", help="Debug what documents are in the vector store"):
                    try:
                        km = get_knowledge_manager()
                        stats = km.get_stats()
                        sources = km.get_sources() if hasattr(km, 'get_sources') else []
                        st.write("**Current Vector Store:**")
                        st.write(f"Documents: {stats.get('doc_count', 0)}")
                        st.write(f"Chunks: {stats.get('chunk_count', 0)}")
                        st.write(f"Sources: {sources}")
                    except Exception as e:
                        st.error(f"Error getting vector store info: {e}")
        
        if api_key:
            st.session_state["openai_api_key"] = api_key
            
            # Upload section
            st.subheader("📄 Upload Documents")
            uploaded_files = st.file_uploader("Choose files", type=['pdf', 'txt', 'docx'], accept_multiple_files=True, key="file_uploader")
            
            km = st.session_state.knowledge_manager
            if km is None:
                st.error("❌ Knowledge Manager not available. Please refresh the page.")
                st.stop()
            
            if uploaded_files:
                new_files = []
                for uploaded_file in uploaded_files:
                    if not km.is_file_already_processed(uploaded_file):
                        new_files.append(uploaded_file)
                
                if new_files:
                    st.info(f"📝 {len(new_files)} new file(s) ready to process")
                else:
                    st.success("✅ All uploaded files have already been processed")
            
            if st.button("📖 Build Knowledge Base", disabled=not uploaded_files):
                with st.spinner("Processing documents..."):
                    result = km.process_documents(uploaded_files)
                    if result['success']:
                        st.success(f"✅ {result['message']}")
                        if km.retriever:
                            st.session_state.chat_bot = ChatAgent(km.retriever)
            
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
                        available_docs = get_available_documents(st.session_state.knowledge_manager)
                        
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
                            st.session_state.quiz_type = quiz_type
                            st.session_state.difficulty = difficulty
                            st.session_state.num_questions = num_questions
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
        show_quiz_interface(
            st.session_state.get("quiz_type", "Multiple Choice"),
            st.session_state.get("difficulty", "Easy"),
            st.session_state.get("num_questions", 10)
        )
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
            st.session_state.quiz_bot = QuizAgent(st.session_state.knowledge_manager.retriever)
            st.session_state.chat_bot = ChatAgent(st.session_state.knowledge_manager.retriever)
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
                api_key=st.session_state.get('openai_api_key', ''),
                model=st.session_state.get('selected_model', 'gpt-3.5-turbo'),
                base_url=st.session_state.get('openai_base_url', None),
                question_type=quiz_type,
                difficulty=difficulty
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
        preload_status = get_preload_status(st.session_state.knowledge_manager)
        
        if preload_status['is_preloaded']:
            st.success("🚀 Knowledge base preloaded from previous session!")
        
        # Knowledge Base Status
        st.subheader("📊 Knowledge Base Status")
        try:
            km = get_knowledge_manager() 
            stats = km.get_stats()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📄 Documents", stats['doc_count'])
            with col2:
                st.metric("🧩 Chunks", stats['chunk_count'])
            with col3:
                st.metric("📝 Characters", f"{stats['total_chars']:,}")
            with col4:
                avg_size = stats.get('avg_chunk_size', 0)
                st.metric("📏 Avg Chunk Size", f"{avg_size}")
        except Exception as e:
            st.warning(f"Could not load knowledge base status: {e}")
        
        # Processed files management
        try:
            km = get_knowledge_manager()
            processed_files = km.get_processed_files_details()
        except:
            processed_files = []
            
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
                            try:
                                km = get_knowledge_manager()
                                if km.remove_processed_file(file_info['file_hash']):
                                    st.success(f"Removed {file_info['filename']}")
                                    st.rerun()
                                else:
                                    st.error("Failed to remove file")
                            except Exception as e:
                                st.error(f"Error removing file: {e}")
        
        # Management actions
        st.subheader("🔧 Management Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Rebuild Vector Database"):
                with st.spinner("Rebuilding..."):
                    try:
                        km = get_knowledge_manager()
                        if km.rebuild_vectorstore():
                            st.success("Vector database rebuilt successfully!")
                        else:
                            st.error("Failed to rebuild vector database")
                    except Exception as e:
                        st.error(f"Error rebuilding: {e}")
        
        with col2:
            if st.button("🗑️ Clear All Data"):
                if st.checkbox("I understand this will delete all processed documents", key="confirm_clear"):
                    try:
                        km = get_knowledge_manager()
                        km.clear_knowledge_base()
                        st.session_state.quiz_bot = None
                        st.success("Knowledge base cleared!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error clearing data: {e}")
        
        with col3:
            if st.button("📊 Export Data"):
                try:
                    km = get_knowledge_manager()
                    export_data = km.export_knowledge_base()
                    st.download_button(
                        "💾 Download Export",
                        data=json.dumps(export_data, indent=2),
                        file_name=f"knowledge_base_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                except Exception as e:
                    st.error(f"Error exporting data: {e}")
        
        # Ready to quiz section
        st.markdown("### Ready to start your quiz! 🎯")
        st.markdown("Configure your quiz settings in the sidebar and click **Start Quiz** when ready.")
        
        # Show sample questions preview
        with st.expander("🔍 Preview Sample Questions"):
            if st.button("Generate Preview"):
                if st.session_state.quiz_bot:
                    sample_q = st.session_state.quiz_bot.generate_question(
                        api_key=st.session_state.get('openai_api_key', ''),
                        model=st.session_state.get('selected_model', 'gpt-3.5-turbo'),
                        base_url=st.session_state.get('openai_base_url', None),
                        question_type="multiple_choice",
                        difficulty="medium"
                    )
                    if sample_q:
                        st.markdown(f"**Sample Question:** {sample_q['question']}")
                        for i, option in enumerate(sample_q.get('options', []), 1):
                            st.markdown(f"{i}. {option}")
                    else:
                        st.warning("Could not generate sample question")
                else:
                    st.warning("Quiz bot not available. Please ensure documents are loaded and API key is set.")
        
        # Demo button
        with col3:
            if st.button("🎮 Try Demo", help="Load sample content to test the application"):
                with st.spinner("Loading demo content..."):
                    try:
                        sample_content = demo_content["ai_ml"]
                        km = get_knowledge_manager()
                        km.process_text_content(sample_content)
                        if km.retriever:
                            st.session_state.quiz_bot = QuizAgent(km.retriever)
                            st.session_state.chat_bot = ChatAgent(km.retriever)
                            st.success("✅ Demo content loaded successfully!")
                        else:
                            st.error("Failed to create retriever from demo content")
                    except Exception as e:
                        st.error(f"Failed to load demo content: {str(e)}")
    
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
                                st.session_state.chat_history[:-1],  # Exclude the just-added message
                                api_key=st.session_state.get("openai_api_key", ""),
                                base_url=st.session_state.get("openai_base_url", ""),
                                model=st.session_state.get("selected_model", "GPT-4o-mini")
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
                st.session_state.chat_history[:-1],  # Exclude the just-added message
                api_key=st.session_state.get("openai_api_key", ""),
                base_url=st.session_state.get("openai_base_url", ""),
                model=st.session_state.get("selected_model", "gpt-3.5-turbo")
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