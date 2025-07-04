from langchain.prompts import ChatPromptTemplate

quiz_prompt = ChatPromptTemplate.from_messages([
    ("system", "Based on the following text, create a {difficulty} level multiple choice question.\nContext: {context}\nRequirements:\n- Create 1 clear, specific question\n- Provide exactly 4 answer options (A, B, C, D)\n- Only 1 option should be correct\n- Make incorrect options plausible but clearly wrong\n- Include a brief explanation for the correct answer\n- Cite the source information when possible\nFormat your response as JSON:\n{{\n    \"type\": \"multiple_choice\",\n    \"question\": \"Your question here\",\n    \"options\": [\"A) Option 1\", \"B) Option 2\", \"C) Option 3\", \"D) Option 4\"],\n    \"correct_answer\": \"A) Correct option\",\n    \"explanation\": \"Why this answer is correct and others are wrong\",\n    \"source\": \"Relevant excerpt from context\",\n    \"difficulty\": \"{difficulty}\"\n}}"),
    ("user", "{user_message}")
]) 