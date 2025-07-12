import logging
from llm.litellm_provider import LiteLLMProvider
from agents.quiz_agent import QuizAgent
from agents.chat_agent import ChatAgent


def initialize_llm_provider(session_state):
    """
    Initialize and return a LiteLLMProvider based on session state config.
    """
    provider = session_state.get("llm_provider_choice", "openai")
    model = session_state.get("selected_model", "gpt-4o-mini")
    api_key = session_state.get("openai_api_key", "")
    base_url = session_state.get("openai_base_url", "")
    model_with_prefix = f"{provider.lower()}/{model}"
    return LiteLLMProvider(api_key=api_key, api_base=base_url, model=model_with_prefix)


def initialize_agents(session_state, km):
    """
    Initialize QuizAgent and ChatAgent using the retriever from KnowledgeManager and the LLM provider.
    Updates session_state with llm_provider_obj, quiz_bot, and chat_bot.
    Only reinitializes if LLM config or retriever has changed.
    """
    import logging  # Ensure logging is imported
    try:
        # Gather current config
        provider = session_state.get("llm_provider_choice", "openai")
        model = session_state.get("selected_model", "gpt-4o-mini")
        api_key = session_state.get("openai_api_key", "")
        base_url = session_state.get("openai_base_url", "")
        retriever_id = id(km.retriever) if km and km.retriever else None
        current_config = {
            "provider": provider,
            "model": model,
            "api_key": api_key,
            "base_url": base_url,
            "retriever_id": retriever_id
        }
        last_config = getattr(session_state, "_last_agent_config", None)
        if last_config == current_config and session_state.get("quiz_bot") and session_state.get("chat_bot"):
            # No change, skip reinitialization
            logging.info("Agent config unchanged, skipping reinitialization.")
            return
        # Save new config
        session_state._last_agent_config = current_config
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