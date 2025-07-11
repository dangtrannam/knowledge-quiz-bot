# Refactor Plan: Modular Folder Structure for RAG-AI Application

## 1. Current State Analysis

### Main Responsibilities by File:
- **app.py**: Streamlit UI, session state, user interaction, orchestrates bots and knowledge manager.
- **knowledge_manager.py**: Handles document ingestion, splitting, embedding, vector store management, and metadata.
- **quiz_bot.py**: Quiz logic, question generation, uses LLMs and knowledge manager.
- **chat_bot.py**: Handles chat-based Q&A, context retrieval, LLM prompt construction.
- **utils.py**: Page config, CSS, and other helpers.
- **demo.py, start.py**: Likely entry/demo scripts.
- **test_core_functions.py, run_tests.py**: Testing.

---

## 2. Target Modular Folder Structure

Following RAG best practices, refactor into:

```
knowledge-quiz-chatbot/
  app.py
  start.py
  demo.py
  requirements.txt
  README.md
  .env
  loaders/
    __init__.py
    document_loader.py
  embeddings/
    __init__.py
    embedding_model.py
  vectorstores/
    __init__.py
    chroma_store.py
  retrievers/
    __init__.py
    vector_retriever.py
  chains/
    __init__.py
    retrieval_qa_chain.py
    conversational_chain.py
  agents/
    __init__.py
    quiz_agent.py
    chat_agent.py
  llm/
    __init__.py
    base.py
    openai_llm.py
    gemini_llm.py
    tts.py
    stt.py
    embedding.py
    utils.py
  ui/
    __init__.py
    streamlit_ui.py
    utils.py
  prompts/
    __init__.py
    chat_prompt.py
    quiz_prompt.py
  tests/
    test_core_functions.py
    run_tests.py
  knowledge_manager.py  # (can be split/moved into loaders/, embeddings/, vectorstores/)
  quiz_bot.py           # (move logic to agents/quiz_agent.py)
  chat_bot.py           # (move logic to agents/chat_agent.py)
  chroma_db/            # (vector store data)
```

---

## 3. Refactor Plan

### Step 1: Create Folders and Move Code
- Create the folders: `loaders/`, `embeddings/`, `vectorstores/`, `retrievers/`, `chains/`, `agents/`, `llm/`, `ui/`, `prompts/`, `tests/`.
- Move and split code:
  - **Document loading/splitting** → `loaders/document_loader.py`
  - **Embedding logic** → `embeddings/embedding_model.py`
  - **Vector store management** → `vectorstores/chroma_store.py`
  - **Retriever logic** → `retrievers/vector_retriever.py`
  - **Quiz and chat agent logic** → `agents/quiz_agent.py`, `agents/chat_agent.py`
  - **Prompt templates** → `prompts/` (centralize all prompt templates here)
  - **LLM, embedding, TTS, STT providers** → `llm/` (abstract all model/provider logic here)
  - **UI helpers** → `ui/`
  - **Tests** → `tests/`

### Step 2: Refactor Classes and Imports
- Refactor `KnowledgeManager` into smaller, single-responsibility classes (Loader, Embedder, VectorStoreManager).
- Refactor `QuizBot` and `ChatBot` into agent classes in `agents/`.
- Update all imports in `app.py` and other scripts to use the new structure.

### Step 3: Centralize Configuration
- Move config (paths, model names, etc.) to `.env` or a config file.
- Use `python-dotenv` and `pydantic` for validation.

### Step 4: Centralize Prompts
- Move all prompt templates to `prompts/` and use `ChatPromptTemplate` or similar pattern.
- Refactor all agent, chain, and UI code to import and use prompt templates from the `prompts/` folder, not inline or hardcoded strings.

### Step 5: Add LLM Module for Model Abstraction
- Create an `llm/` module with the following structure:
  - `base.py`: Abstract base classes/interfaces for LLM, embedding, TTS, STT providers.
  - `openai_llm.py`, `gemini_llm.py`: Provider-specific implementations.
  - `embedding.py`: Embedding model abstraction.
  - `tts.py`, `stt.py`: Text-to-speech and speech-to-text abstraction.
  - `utils.py`: Shared utilities.
- Refactor agent and chain code to use the `llm/` module for all LLM, embedding, TTS, and STT calls.
- Centralize API key/config management in this module.

### Step 6: Testing and Validation
- Move and update tests to `tests/`.
- Ensure all tests pass after refactor.

---

## 4. Benefits

- **Separation of concerns**: Each module/folder has a clear responsibility.
- **Scalability**: Easy to add new retrievers, agents, or chains.
- **Maintainability**: Easier to test, debug, and extend.
- **Best practices**: Aligns with modern RAG and LangChain project structure.

---

## 5. Next Steps

- Break down each module into more granular tasks as needed.
- Begin with folder creation and incremental migration of logic.
- Refactor prompt template usage to the `prompts/` folder.
- Add and integrate the `llm/` module for model abstraction.
- Test after each major refactor step.
- Update documentation and diagrams as you go. 