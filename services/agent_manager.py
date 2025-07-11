import logging
from llm.litellm_provider import LiteLLMProvider
from agents.quiz_agent import QuizAgent
from agents.chat_agent import ChatAgent


def initialize_llm_provider(session_state):
    """
    Initialize and return a LiteLLMProvider based on session state config.
    """
    provider = session_state.get("llm_provider_choice", "openai")
    model = session_state.get("selected_model", "gpt-3.5-turbo")
    api_key = session_state.get("openai_api_key", "")
    base_url = session_state.get("openai_base_url", "")
    model_with_prefix = f"{provider.lower()}/{model}"
    return LiteLLMProvider(api_key=api_key, api_base=base_url, model=model_with_prefix)


def initialize_agents(session_state, km):
    """
    Initialize QuizAgent and ChatAgent using the retriever from KnowledgeManager and the LLM provider.
    Updates session_state with llm_provider_obj, quiz_bot, and chat_bot.
    """
    try:
        llm_provider = initialize_llm_provider(session_state)
        session_state.llm_provider_obj = llm_provider
        if km.retriever:
            session_state.quiz_bot = QuizAgent(km.retriever, llm_provider)
            session_state.chat_bot = ChatAgent(km.retriever, llm_provider)
        else:
            logging.warning("KnowledgeManager retriever is not available. Agents not initialized.")
    except Exception as e:
        logging.error(f"Failed to initialize agents: {e}")
        session_state.quiz_bot = None
        session_state.chat_bot = None
        session_state.llm_provider_obj = None 