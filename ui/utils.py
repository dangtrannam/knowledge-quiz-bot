import streamlit as st
from typing import Optional

def setup_page_config():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title="Knowledge Quiz Bot",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/your-repo/knowledge-quiz-bot',
            'Report a bug': 'https://github.com/your-repo/knowledge-quiz-bot/issues',
            'About': "# Knowledge Quiz Bot\nYour AI-powered learning companion inspired by NotebookLM!"
        }
    )

def load_css():
    """Load custom CSS styling"""
    st.markdown("""
    <style>
    .main {
        padding-top: 1rem;
    }
    .stButton > button {
        width: 100%;
        border-radius: 20px;
        border: none;
        padding: 0.5rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 10px rgba(0,0,0,0.2);
    }
    .quiz-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .success-message {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .error-message {
        background: linear-gradient(135deg, #f44336 0%, #da190b 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    .progress-bar {
        background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%);
        height: 10px;
        border-radius: 5px;
    }
    .question-container {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 15px;
        border-left: 5px solid #667eea;
        margin: 1rem 0;
    }
    .explanation-box {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

def show_info_box(title: str, content: str, box_type: str = "info"):
    """Show an information box with title and content"""
    icon_map = {
        "info": "ℹ️",
        "success": "✅", 
        "warning": "⚠️",
        "error": "❌"
    }
    icon = icon_map.get(box_type, "ℹ️")
    st.markdown(f"""
    <div class="{box_type}-message">
        <h4>{icon} {title}</h4>
        <p>{content}</p>
    </div>
    """, unsafe_allow_html=True)

def display_progress_bar(current: int, total: int, label: str = "Progress"):
    """Display a custom progress bar"""
    if total > 0:
        progress = current / total
        percentage = int(progress * 100)
        st.markdown(f"""
        <div style="margin: 1rem 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span><strong>{label}</strong></span>
                <span>{current}/{total} ({percentage}%)</span>
            </div>
            <div style="background: #e0e0e0; border-radius: 10px; height: 20px; overflow: hidden;">
                <div class="progress-bar" style="width: {percentage}%; height: 100%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True) 