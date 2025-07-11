import streamlit as st
import json
from datetime import datetime
from agents.quiz_agent import QuizAgent
from agents.chat_agent import ChatAgent

def show_knowledge_base_info(session_state, get_preload_status, get_knowledge_manager, demo_content):
    st.markdown("## 📚 Knowledge Base Overview")
    if session_state.knowledge_manager:
        preload_status = get_preload_status(session_state.knowledge_manager)
        if preload_status['is_preloaded']:
            st.success("🚀 Knowledge base preloaded from previous session!")
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
        try:
            km = get_knowledge_manager()
            processed_files = km.get_processed_files_details()
        except:
            processed_files = []
        if processed_files:
            st.subheader("📄 Processed Documents")
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
                        session_state.quiz_bot = None
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
        st.markdown("### Ready to start your quiz! 🎯")
        st.markdown("Configure your quiz settings in the sidebar and click **Start Quiz** when ready.")
        with st.expander("🔍 Preview Sample Questions"):
            if st.button("Generate Preview"):
                if session_state.quiz_bot:
                    sample_q = session_state.quiz_bot.generate_question(
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
        with col3:
            if st.button("🎮 Try Demo", help="Load sample content to test the application"):
                with st.spinner("Loading demo content..."):
                    try:
                        sample_content = demo_content["ai_ml"]
                        km = get_knowledge_manager()
                        km.process_text_content(sample_content)
                        if km.retriever:
                            session_state.quiz_bot = QuizAgent(km.retriever, session_state.llm_provider_obj)
                            session_state.chat_bot = ChatAgent(km.retriever, session_state.llm_provider_obj)
                            st.success("✅ Demo content loaded successfully!")
                        else:
                            st.error("Failed to create retriever from demo content")
                    except Exception as e:
                        st.error(f"Failed to load demo content: {str(e)}")
    else:
        st.info("No knowledge base loaded yet.") 