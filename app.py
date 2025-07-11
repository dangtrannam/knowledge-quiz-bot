import streamlit as st
from knowledge_manager import KnowledgeManager
from ui.utils import setup_page_config, load_css, get_preload_status, get_knowledge_manager
from dotenv import load_dotenv
import logging
from services.agent_manager import initialize_agents
from ui.knowledge_base import show_knowledge_base_info
from ui.chat import show_chat_interface
from ui.quiz import show_quiz_interface, handle_answer_submission
from ui.screens import create_sample_content, show_navbar
from ui.session import initialize_session_state

logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more detail
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

load_dotenv()

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

def main():
    setup_page_config()
    load_css()
    initialize_session_state()
    # --- KnowledgeManager initialization with debug ---
    if "knowledge_manager" not in st.session_state or st.session_state.knowledge_manager is None:
        import traceback
        try:
            st.session_state.knowledge_manager = KnowledgeManager()
        except Exception as e:
            traceback.print_exc()
            st.session_state.knowledge_manager = None

    # Navbar-based UI
    km = st.session_state.knowledge_manager
    if km and km.retriever and (st.session_state.chat_bot is None or st.session_state.quiz_bot is None):
        initialize_agents(st.session_state, km)
    show_navbar(
        st.session_state,
        initialize_agents,
        create_sample_content,
        get_knowledge_manager,
        get_preload_status,
        show_chat_interface,
        show_quiz_interface,
        handle_answer_submission,
        show_knowledge_base_info
    )

if __name__ == "__main__":
    main() 