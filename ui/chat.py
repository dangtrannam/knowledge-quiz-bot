import streamlit as st

def show_chat_interface(session_state):
    st.markdown("## 💬 Chat with Your Documents")
    if not session_state.chat_bot:
        st.error("Chat bot not initialized. Please upload documents first.")
        return
    if session_state.selected_documents:
        if 'all' in session_state.selected_documents:
            st.info("💬 Chatting with **All Documents**")
        else:
            doc_names = []
            # Group documents by file_hash and extract filenames from chunk metadata
            from collections import defaultdict
            file_groups = defaultdict(list)
            for doc in getattr(session_state.knowledge_manager, 'documents', []):
                meta = getattr(doc, 'metadata', {})
                file_id = meta.get('file_hash') or meta.get('source_file') or meta.get('original_filename') or 'Unknown'
                file_groups[file_id].append(doc)
            for doc_id in session_state.selected_documents:
                docs = file_groups.get(doc_id, [])
                if docs:
                    meta = docs[0].metadata
                    filename = meta.get('source_file') or meta.get('original_filename') or 'Unknown'
                    doc_names.append(filename)
            if doc_names:
                st.info(f"💬 Chatting with: **{', '.join(doc_names)}**")
    chat_container = st.container()
    with chat_container:
        if session_state.chat_history:
            for i, message in enumerate(session_state.chat_history):
                if message['role'] == 'user':
                    with st.chat_message("user"):
                        st.markdown(message['content'])
                else:
                    with st.chat_message("assistant"):
                        st.markdown(message['content'])
                        if 'sources' in message and message['sources']:
                            with st.expander("📚 Sources"):
                                for source in message['sources']:
                                    st.caption(f"• {source}")
        else:
            st.markdown("### 🚀 Get Started")
            st.markdown("Ask me anything about your documents! Here are some suggestions:")
            starters = session_state.chat_bot.get_conversation_starters(session_state.selected_documents)
            cols = st.columns(2)
            for i, starter in enumerate(starters):
                with cols[i % 2]:
                    if st.button(starter, key=f"starter_{i}", use_container_width=True):
                        session_state.chat_history.append({
                            'role': 'user',
                            'content': starter
                        })
                        with st.spinner("Thinking..."):
                            result = session_state.chat_bot.generate_response(
                                starter, 
                                session_state.selected_documents,
                                session_state.chat_history[:-1],
                            )
                            if result['success']:
                                response_data = {
                                    'role': 'assistant',
                                    'content': result['response']
                                }
                                if 'sources' in result:
                                    response_data['sources'] = result['sources']
                                session_state.chat_history.append(response_data)
                            else:
                                session_state.chat_history.append({
                                    'role': 'assistant',
                                    'content': f"❌ {result['error']}"
                                })
                        st.rerun()
    user_input = st.chat_input("Ask me anything about your documents...")
    if user_input:
        session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })
        with st.spinner("Thinking..."):
            result = session_state.chat_bot.generate_response(
                user_input, 
                session_state.selected_documents,
                session_state.chat_history[:-1],
            )
            if result['success']:
                response_data = {
                    'role': 'assistant',
                    'content': result['response']
                }
                if 'sources' in result:
                    response_data['sources'] = result['sources']
                session_state.chat_history.append(response_data)
            else:
                session_state.chat_history.append({
                    'role': 'assistant',
                    'content': f"❌ {result['error']}"
                })
        st.rerun()
