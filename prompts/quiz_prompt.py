from langchain.prompts import ChatPromptTemplate

quiz_prompt = ChatPromptTemplate.from_messages([
    ("system", """
Based on the following text, create {num_questions} {difficulty} level {question_type} questions.
Context: {context}
Requirements:
- Each question should be clear and specific.
- For multiple choice, provide exactly 4 answer options (A, B, C, D), only 1 correct.
- For true/false, provide a statement and the correct answer.
- For short answer, provide a question and the correct answer.
- Include a brief explanation and cite the source if possible.
Format for each question (as JSON object):
{{
    \"type\": \"{question_type}\",
    \"question\": \"Your question here\",
    \"options\": [\"A) Option 1\", \"B) Option 2\", \"C) Option 3\", \"D) Option 4\"],
    \"correct_answer\": \"A) Correct option\",
    \"explanation\": \"Why this answer is correct and others are wrong\",
    \"source\": \"Relevant excerpt from context\",
    \"difficulty\": \"{difficulty}\"
}}
Return the result as a JSON list, where each item is a question object as above.
"""),
    ("user", "{user_message}")
]) 