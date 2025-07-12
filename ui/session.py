import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

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
        'selected_documents': [],
        'openai_base_url': "",
        'selected_model': "gpt-4o-mini",
        'model_input_type': "predefined",
        'custom_model': ""
    }
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and "openai_api_key" not in st.session_state:
        st.session_state["openai_api_key"] = api_key
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value 