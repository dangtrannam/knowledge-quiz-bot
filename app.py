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
from llm.litellm_provider import LiteLLMProvider
from services.agent_manager import initialize_agents, initialize_llm_provider
from ui.knowledge_base import show_knowledge_base_info
from ui.chat import show_chat_interface
from ui.quiz import show_quiz_interface, handle_answer_submission
from constants import PROVIDER_OPTIONS, PROVIDER_DEFAULTS, DEFAULT_BASE_URL, DEFAULT_MODEL, DEFAULT_MODEL_INPUT_TYPE
import sys

logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG for more detail
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

def initialize_session_state():
    defaults = {
        'quiz_bot': None,
        'chat_bot': None,
        'knowledge_manager': None,
        'quiz_active': False,
        'chat_active': False,
        'current_question': None,
        'score': {'correct': 0, 'total': 0},
        'chat_history': [],
        'selected_documents': ['all'],
        'openai_base_url': "https://aiportalapi.stu-platform.live/jpe",
        'selected_model': "GPT-4o-mini",
        'model_input_type': "predefined",
        'custom_model': ""
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def main():
    setup_page_config()
    load_css()
    initialize_session_state()
    # --- KnowledgeManager initialization with debug ---
    if "knowledge_manager" not in st.session_state or st.session_state.knowledge_manager is None:
        logging.debug("[DEBUG] Initializing KnowledgeManager and assigning to st.session_state.knowledge_manager")
        import traceback
        try:
            st.session_state.knowledge_manager = KnowledgeManager()
            logging.debug("[DEBUG] KnowledgeManager initialized successfully")
        except Exception as e:
            logging.error(f"[ERROR] Failed to initialize KnowledgeManager: {e}", exc_info=True)
            traceback.print_exc()
            st.session_state.knowledge_manager = None
    
    # Header
    st.title("🧠 Knowledge Quiz Bot")
    st.subheader("Your AI-powered learning companion, inspired by NotebookLM")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("📚 Knowledge Base")
        # API Configuration
        st.subheader("🔧 API Configuration")
        
        api_key = st.text_input(
            "OpenAI API Key", 
            type="password",
            help="Enter your OpenAI API key to power the AI features"
        )
        
        # Advanced API settings in an expander
        with st.expander("⚙️ Advanced Settings"):
            # Provider selection
            provider = st.selectbox(
                "Provider",
                PROVIDER_OPTIONS,
                index=PROVIDER_OPTIONS.index(st.session_state["llm_provider_choice"]) if "llm_provider_choice" in st.session_state else 0,
                key="llm_provider_choice",
                help="Choose your LLM provider. This will update model and base URL defaults."
            )
            defaults = PROVIDER_DEFAULTS.get(provider or "OpenAI", PROVIDER_DEFAULTS["OpenAI"])
            predefined_models = defaults["models"]

            # Base URL
            base_url = st.text_input(
                "Base URL (Optional)",
                value=st.session_state["openai_base_url"] if "openai_base_url" in st.session_state else defaults["base_url"],
                placeholder=defaults["base_url"],
                help=f"Custom base URL for {provider} (leave empty for default)",
                key="llm_api_base"
            )

            # Model selection type
            model_input_type = st.radio(
                "Model Selection",
                options=["predefined", "custom"],
                format_func=lambda x: "📋 Select from List" if x == "predefined" else "✏️ Custom Model",
                horizontal=True,
                help="Choose to select from predefined models or enter a custom model name",
                key="llm_model_input_type"
            )

            # Model selection based on type
            if model_input_type == "predefined":
                current_model_index = 0
                if st.session_state.get("selected_model", predefined_models[0]) in predefined_models:
                    current_model_index = predefined_models.index(st.session_state.get("selected_model", predefined_models[0]))
                selected_model = st.selectbox(
                    "AI Model",
                    options=predefined_models,
                    index=current_model_index,
                    help=f"Choose the {provider} model to use for generation",
                    key="llm_model"
                )
                st.session_state.selected_model = selected_model
                st.session_state.custom_model = ""
            else:  # custom model
                custom_model = st.text_input(
                    "Custom Model Name",
                    value=st.session_state.get("custom_model", ""),
                    placeholder="e.g., gpt-4-1106-preview, claude-3-opus, custom-model-name",
                    help="Enter the exact model name as expected by your API",
                    key="llm_custom_model"
                )
                st.info(f"\n💡 **Custom Model Examples for {provider}:**\n" + "\n".join(f"• {m}" for m in defaults["models"]))
                if custom_model and custom_model.strip():
                    selected_model = custom_model.strip()
                    st.session_state.selected_model = selected_model
                    st.session_state.custom_model = custom_model.strip()
                    if ' ' in selected_model:
                        st.warning("⚠️ Model names usually don't contain spaces. Please check your model name.")
                    elif len(selected_model) < 3:
                        st.warning("⚠️ Model name seems too short. Please verify it's correct.")
                else:
                    selected_model = predefined_models[0]
                    st.session_state.selected_model = selected_model
                    if not custom_model:
                        st.session_state.custom_model = ""

            st.session_state.openai_base_url = base_url
            st.session_state.model_input_type = model_input_type

            st.caption(f"**Current Provider:** {provider}")
            st.caption(f"**Current Model:** {selected_model}")
            st.caption(f"**Base URL:** {base_url if base_url else defaults['base_url']}")

            if st.button("🔄 Reset AI Configuration", help="Clear cached LLM providers and reinitialize with new settings"):
                if st.session_state.chat_bot is not None:
                    st.session_state.chat_bot.llm_provider = None
                if st.session_state.quiz_bot is not None:
                    st.session_state.quiz_bot.llm_provider = None
                st.session_state.model_input_type = "predefined"
                st.session_state.selected_model = defaults["models"][0]
                st.session_state.custom_model = ""
                st.session_state.openai_base_url = defaults["base_url"]
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
                            initialize_agents(st.session_state, km)
            
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
        
        # --- Preload status and agent initialization ---
        logging.debug("[DEBUG] Preload status and agent initialization: start")
        if st.session_state.knowledge_manager:
            logging.debug("[DEBUG] st.session_state.knowledge_manager exists")
            try:
                preload_status = get_preload_status(st.session_state.knowledge_manager)
                logging.debug(f"[DEBUG] Preload status: {preload_status}")
            except Exception as e:
                logging.error(f"[ERROR] Exception in get_preload_status: {e}", exc_info=True)
                st.error(f"❌ Exception in get_preload_status: {e}")
                st.session_state.knowledge_manager = None
                return
            if preload_status['is_preloaded']:
                st.success("🚀 Preloaded from previous session")
                st.caption(f"📁 {preload_status['processed_files_count']} files ready")
                # Initialize agents with LiteLLMProvider using all selected settings
                try:
                    logging.debug("[DEBUG] About to call get_knowledge_manager() in is_preloaded block")
                    km = get_knowledge_manager()
                    logging.debug(f"[DEBUG] get_knowledge_manager() returned: {km}")
                    logging.debug("[DEBUG] About to call initialize_agents() in is_preloaded block")
                    initialize_agents(st.session_state, km)
                    logging.debug("[DEBUG] initialize_agents() completed in is_preloaded block")
                    # Don't automatically activate modes - let user choose
                except Exception as e:
                    logging.error(f"KnowledgeManager initialization error in is_preloaded block: {e}", exc_info=True)
                    with open("km_init_error.log", "a") as f:
                        f.write(f"KnowledgeManager initialization error in is_preloaded block: {e}\n")
                    st.error(f"❌ Failed to initialize Knowledge Manager: {str(e)}")
                    st.info("💡 Try refreshing the page. If the problem persists, check system requirements.")
                    st.session_state.knowledge_manager = None
            elif preload_status['processed_files_count'] > 0:
                st.info("📚 Knowledge base available")
                # Initialize agents for demo mode
                try:
                    logging.debug("[DEBUG] About to call get_knowledge_manager() in processed_files_count > 0 block")
                    km = get_knowledge_manager()
                    logging.debug(f"[DEBUG] get_knowledge_manager() returned: {km}")
                    logging.debug("[DEBUG] About to call initialize_agents() in processed_files_count > 0 block")
                    initialize_agents(st.session_state, km)
                    logging.debug("[DEBUG] initialize_agents() completed in processed_files_count > 0 block")
                    # Don't automatically activate modes - let user choose
                except Exception as e:
                    logging.error(f"Failed to initialize agents in processed_files_count > 0 block: {e}", exc_info=True)
                    with open("km_init_error.log", "a") as f:
                        f.write(f"Failed to initialize agents in processed_files_count > 0 block: {e}\n")
                    st.error(f"Failed to initialize agents: {e}")
        else:
            logging.debug("[DEBUG] st.session_state.knowledge_manager is None")
            st.warning("⚠️ Please enter your OpenAI API key to get started")
    
    # Main content area
    if not api_key:
        show_welcome_screen()
    elif not st.session_state.quiz_bot and not st.session_state.chat_bot:
        show_upload_prompt()
    elif st.session_state.chat_active:
        show_chat_interface(st.session_state)
    elif st.session_state.quiz_active:
        show_quiz_interface(
            st.session_state,
            st.session_state.get("quiz_type", "Multiple Choice"),
            st.session_state.get("difficulty", "Easy"),
            st.session_state.get("num_questions", 5),
            handle_answer_submission
        )
    else:
        show_knowledge_base_info(
            st.session_state,
            get_preload_status,
            get_knowledge_manager,
            demo_content
        )

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
            initialize_agents(st.session_state, st.session_state.knowledge_manager)
            st.success("Demo content loaded! Ready to chat or quiz!")
            st.rerun()

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