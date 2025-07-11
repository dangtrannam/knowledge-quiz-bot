import streamlit as st
from ui.utils import get_available_documents, get_knowledge_manager

def show_quiz_interface(session_state, handle_answer_submission):
    # --- Document Selection Control ---
    km = get_knowledge_manager()
    available_docs = get_available_documents(km)
    doc_options = {doc['id']: doc['name'] for doc in available_docs}
    selected_docs = st.multiselect(
        "Select documents for quiz questions:",
        options=list(doc_options.keys()),
        default=session_state.get('selected_documents', ['all']),
        format_func=lambda x: doc_options.get(x, x)
    )
    if not selected_docs:
        selected_docs = ['all']
    session_state.selected_documents = selected_docs
    if 'all' in selected_docs:
        st.info("📝 Generating quiz from **All Documents**")
    else:
        selected_names = [doc_options[doc_id] for doc_id in selected_docs if doc_id in doc_options]
        st.info(f"📝 Generating quiz from: **{', '.join(selected_names)}**")
    # --- End Document Selection Control ---

    # --- Quiz Configuration Controls ---
    quiz_type = st.selectbox(
        "Quiz Type",
        ["multiple_choice", "true_false", "short_answer", "mixed"],
        index=["multiple_choice", "true_false", "short_answer", "mixed"].index(session_state.get("quiz_type", "multiple_choice")),
        help="Choose the type of questions for your quiz."
    )
    session_state.quiz_type = quiz_type

    difficulty = st.selectbox(
        "Difficulty",
        ["easy", "medium", "hard", "adaptive"],
        index=["easy", "medium", "hard", "adaptive"].index(session_state.get("difficulty", "medium")),
        help="Select the difficulty level for your quiz."
    )
    session_state.difficulty = difficulty

    num_questions = st.slider(
        "Number of Questions",
        min_value=1,
        max_value=50,
        value=session_state.get("num_questions", 5),
        help="Set the number of questions for your quiz."
    )
    session_state.num_questions = num_questions
    # --- End Quiz Configuration Controls ---

    # --- Batch Quiz Generation ---
    start_clicked = st.button('🚀 Start Quiz', type='primary')
    quiz_ready = 'quiz_questions' in session_state and session_state.quiz_questions
    if start_clicked:
        # Generate all questions in a batch
        session_state.quiz_questions = []
        import random
        # Get aggregated context from all selected documents
        aggregated_context = session_state.quiz_bot.get_aggregated_context(session_state.selected_documents)
        questions = session_state.quiz_bot.generate_questions_batch_from_context(
            context=aggregated_context,
            num_questions=num_questions,
            question_type=quiz_type,
            difficulty=difficulty
        )
        for q in questions:
            session_state.quiz_questions.append(q)
        # Filter out fallback questions
        session_state.quiz_questions = [q for q in session_state.quiz_questions if not (q.get('question', '').startswith('No context available'))]
        session_state.current_question_index = 0
        session_state.score = {'correct': 0, 'total': 0}
        session_state.current_question = None
        quiz_ready = bool(session_state.quiz_questions)

    # Only show quiz UI if valid questions are generated and available
    if quiz_ready:
        questions = session_state.get('quiz_questions', [])
        idx = session_state.get('current_question_index', 0)
        if questions and idx < len(questions):
            session_state.current_question = questions[idx]
            progress = (idx) / num_questions if num_questions > 0 else 0
            st.progress(progress)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Question", f"{idx + 1}/{num_questions}")
            with col2:
                st.metric("Correct", session_state.score['correct'])
            with col3:
                accuracy = (session_state.score['correct'] / session_state.score['total'] * 100) if session_state.score['total'] > 0 else 0
                st.metric("Accuracy", f"{accuracy:.1f}%")
            if idx >= num_questions:
                show_quiz_results(session_state)
                return
            question_data = session_state.current_question
            st.markdown(f"### Question {idx + 1}")
            st.markdown(f"**{question_data['question']}**")
            if question_data['type'] == 'multiple_choice':
                answer = st.radio(
                    "Choose your answer:",
                    question_data['options'],
                    key=f"q_{idx}"
                )
                if st.button("Submit Answer", type="primary"):
                    handle_answer_submission(session_state, answer, question_data)
            elif question_data['type'] == 'true_false':
                answer = st.radio(
                    "Choose your answer:",
                    ["True", "False"],
                    key=f"q_{idx}"
                )
                if st.button("Submit Answer", type="primary"):
                    handle_answer_submission(session_state, answer, question_data)
            elif question_data['type'] == 'short_answer':
                answer = st.text_input(
                    "Your answer:",
                    key=f"q_{idx}"
                )
                if st.button("Submit Answer", type="primary") and answer:
                    handle_answer_submission(session_state, answer, question_data)
        elif questions and idx >= len(questions):
            show_quiz_results(session_state)
    else:
        st.info("Click 'Start Quiz' to begin!")


def handle_answer_submission(session_state, user_answer, question_data):
    is_correct = session_state.quiz_bot.check_answer(user_answer, question_data)
    session_state.score['total'] += 1
    if is_correct:
        session_state.score['correct'] += 1
    if is_correct:
        st.success("✅ Correct!")
    else:
        st.error("❌ Incorrect")
        st.info(f"**Correct answer:** {question_data['correct_answer']}")
    if 'explanation' in question_data:
        with st.expander("💡 Explanation"):
            st.markdown(question_data['explanation'])
            if 'source' in question_data:
                st.caption(f"Source: {question_data['source']}")
    session_state.current_question = None
    session_state.current_question_index = session_state.get('current_question_index', 0) + 1
    if is_correct:
        st.balloons()
    if st.button("Next Question →"):
        st.rerun()

def show_quiz_results(session_state):
    st.markdown("## 🎉 Quiz Complete!")
    score = session_state.score
    percentage = (score['correct'] / score['total']) * 100
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Final Score", f"{score['correct']}/{score['total']}")
    with col2:
        st.metric("Percentage", f"{percentage:.1f}%")
    with col3:
        if percentage >= 90:
            grade = "A+"
            emoji = "🌟"
        elif percentage >= 80:
            grade = "A"
            emoji = "🎯"
        elif percentage >= 70:
            grade = "B"
            emoji = "👏"
        elif percentage >= 60:
            grade = "C"
            emoji = "👍"
        else:
            grade = "D"
            emoji = "💪"
        st.metric("Grade", f"{grade} {emoji}")
    if percentage >= 90:
        st.success("🌟 Outstanding! You've mastered this material!")
    elif percentage >= 70:
        st.info("🎯 Great job! You have a solid understanding.")
    elif percentage >= 50:
        st.warning("📚 Good effort! Consider reviewing the material again.")
    else:
        st.error("💪 Keep studying! Practice makes perfect.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Take Another Quiz", type="primary"):
            session_state.quiz_active = True
            session_state.score = {'correct': 0, 'total': 0}
            session_state.current_question = None
            st.rerun()
    with col2:
        if st.button("📊 View Knowledge Base"):
            session_state.quiz_active = False
            st.rerun() 