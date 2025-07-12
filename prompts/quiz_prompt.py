from langchain.prompts import ChatPromptTemplate

quiz_prompt = ChatPromptTemplate.from_messages([
    ("system", """
Based on the following text, create {num_questions} {difficulty} level {question_type} questions.
Context: {context}
Requirements:
- Generate ONLY questions of type: {question_type}. Do not mix question types in the output.
- Each question must be based on the context above.
- For multiple choice, provide exactly 4 answer options (A, B, C, D), only 1 correct answer (e.g., \"A) ...\").
- For true/false, provide a statement and the correct answer (as a JSON boolean: true or false, not quoted).
- For short answer, provide a question and the correct answer.
- Include a brief explanation and cite the source if possible.
- Your output must be strictly valid JSON: no trailing commas, use double quotes for all strings, use JSON booleans (true/false, not quoted), and do not output any text outside the JSON list.
- All required fields must be present for each question type.
- Return ONLY valid JSON, and nothing else. Surround your JSON output with <result> and </result> tags.

Few-shot examples:
<result>
[
  {{
    "type": "multiple_choice",
    "question": "What is the primary function of Pinecone's upsert operation?",
    "options": ["A) To store vectors", "B) To retrieve documents", "C) To process text", "D) To index data"],
    "correct_answer": "A) To store vectors",
    "explanation": "The upsert operation in Pinecone is used to store vectors in the index.",
    "source": "Introduction to Pinecone",
    "difficulty": "medium"
  }},
  {{
    "type": "true_false",
    "question": "Pinecone can be used for vector indexing.",
    "correct_answer": true,
    "explanation": "Pinecone is a vector database designed for indexing and querying vectors.",
    "source": "Pinecone Documentation",
    "difficulty": "easy"
  }},
  {{
    "type": "short_answer",
    "question": "What is the purpose of a query in Pinecone?",
    "correct_answer": "To retrieve similar documents based on the user's context.",
    "explanation": "Queries in Pinecone are used to find documents that are most similar to a given vector.",
    "source": "Chapter 2 - Pinecone Vector Manipulation in Python Fetching",
    "difficulty": "medium"
  }}
]
</result>

Now, generate your output below using the same format and requirements.
"""),
    ("user", "{user_message}")
]) 