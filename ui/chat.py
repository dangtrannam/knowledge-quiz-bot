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
            processed_files = session_state.knowledge_manager.get_processed_files_details()
            for doc_id in session_state.selected_documents:
                for file_info in processed_files:
                    if file_info['file_hash'] == doc_id:
                        doc_names.append(file_info['filename'])
                        break
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
    with st.sidebar:
        st.markdown("---")
        st.subheader("💬 Chat Controls")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 New Chat"):
                session_state.chat_history = []
                st.rerun()
        with col2:
            if st.button("📊 Back to Overview"):
                session_state.chat_active = False
                st.rerun()
        if session_state.chat_history:
            st.markdown("### 📈 Chat Stats")
            user_messages = len([m for m in session_state.chat_history if m['role'] == 'user'])
            assistant_messages = len([m for m in session_state.chat_history if m['role'] == 'assistant'])
            st.metric("Messages", f"{user_messages + assistant_messages}")
            st.metric("Questions Asked", user_messages) 