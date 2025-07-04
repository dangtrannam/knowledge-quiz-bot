from langchain.prompts import ChatPromptTemplate

chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant that answers questions based on provided documents.\n\nThe user is asking about content from: {doc_context}\n\nRules:\n1. Answer based ONLY on the provided context from the documents\n2. If the context doesn't contain enough information to answer the question, say so\n3. Be specific and cite which document your information comes from when possible\n4. Maintain conversational tone while being informative\n5. If asked about something not in the documents, politely redirect to document content\n\nAvailable context from documents:\n{context}"),
    ("system", "Recent conversation context:\n{history_context}"),
    ("user", "{user_message}")
]) 