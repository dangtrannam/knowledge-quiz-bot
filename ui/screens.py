import streamlit as st
from constants import PROVIDER_OPTIONS, PROVIDER_DEFAULTS

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

def show_upload_prompt(initialize_agents, create_sample_content):
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

def show_navbar(
    st_session_state,
    initialize_agents,
    create_sample_content,
    get_knowledge_manager,
    get_preload_status,
    show_chat_interface,
    show_quiz_interface,
    handle_answer_submission,
    show_knowledge_base_info
):
    tabs = st.tabs(["📚 Knowledge Base", "🤖 LLM Settings", "💬 Chat", "🎯 Quiz"])

    # Knowledge Base Tab
    with tabs[0]:
        st.header("Knowledge Base")
        # --- Integrated Upload Section ---
        st.subheader("Upload Documents")
        uploaded_files = st.file_uploader(
            "Choose files to add to your knowledge base:",
            type=["pdf", "txt", "docx"],
            accept_multiple_files=True,
            key="file_uploader_main"
        )
        km = get_knowledge_manager()
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
                        initialize_agents(st_session_state, km)
                    st.rerun()
                else:
                    st.error(f"❌ {result.get('message', 'Failed to process documents')}")
        # --- End Upload Section ---
        show_knowledge_base_info(
            st_session_state,
            get_preload_status,
            get_knowledge_manager,
            {  # demo_content
                "ai_ml": "Demo content placeholder."
            }
        )

    # LLM Settings Tab
    with tabs[1]:
        st.header("LLM & API Settings")
        # API Key
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=st.session_state.get("openai_api_key", ""),
            help="Enter your OpenAI API key to power the AI features"
        )
        if api_key:
            st.session_state["openai_api_key"] = api_key

        st.markdown("---")
        st.subheader("Provider & Model")
        provider = st.selectbox(
            "Provider",
            PROVIDER_OPTIONS,
            index=PROVIDER_OPTIONS.index(st.session_state.get("llm_provider_choice", PROVIDER_OPTIONS[0])),
            key="llm_provider_choice",
            help="Choose your LLM provider. This will update model and base URL defaults."
        )
        defaults = PROVIDER_DEFAULTS.get(provider or "OpenAI", PROVIDER_DEFAULTS["OpenAI"])
        predefined_models = defaults["models"]

        base_url = st.text_input(
            "Base URL (Optional)",
            value=st.session_state.get("openai_base_url", defaults["base_url"]),
            placeholder=defaults["base_url"],
            help=f"Custom base URL for {provider} (leave empty for default)",
            key="llm_api_base"
        )

        model_input_type = st.radio(
            "Model Selection",
            options=["predefined", "custom"],
            format_func=lambda x: "📋 Select from List" if x == "predefined" else "✏️ Custom Model",
            horizontal=True,
            help="Choose to select from predefined models or enter a custom model name",
            key="llm_model_input_type"
        )

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
            
            initialize_agents(st.session_state, km)
        else:
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
                
                initialize_agents(st.session_state, km)
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

    # Chat Tab
    with tabs[2]:
        if st_session_state.chat_bot:
            show_chat_interface(st_session_state)
        else:
            st.info("Please upload documents and initialize the chat bot.")

    # Quiz Tab
    with tabs[3]:
        if st_session_state.quiz_bot:
            show_quiz_interface(
                st_session_state,
                handle_answer_submission
            )
        else:
            st.info("Please upload documents and initialize the quiz bot.") 