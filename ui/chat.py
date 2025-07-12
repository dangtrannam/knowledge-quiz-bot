import streamlit as st
from ui.utils import get_available_documents, get_knowledge_manager

def show_chat_interface(session_state):
    # --- Document Selection Control ---
    km = get_knowledge_manager()
    available_docs = get_available_documents(km)
    doc_options = {doc['id']: doc['name'] for doc in available_docs}
    selected_docs = st.multiselect(
        "Select documents to chat with:",
        options=list(doc_options.keys()),
        default=session_state.get('selected_documents', ['all']),
        format_func=lambda x: doc_options.get(x, x)
    )
    if not selected_docs:
        selected_docs = ['all']
    session_state.selected_documents = selected_docs
    if 'all' in selected_docs:
        st.info("💬 Chatting with **All Documents**")
    else:
        selected_names = [doc_options[doc_id] for doc_id in selected_docs if doc_id in doc_options]
        st.info(f"💬 Chatting with: **{', '.join(selected_names)}**")
    # --- End Document Selection Control ---
    
    st.markdown("## 💬 Chat with Your Documents")
    if not session_state.chat_bot:
        st.error("Chat bot not initialized. Please upload documents first.")
        return
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
