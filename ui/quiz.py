import streamlit as st

def show_quiz_interface(session_state, quiz_type, difficulty, num_questions, handle_answer_submission):
    progress = session_state.score['total'] / num_questions if num_questions > 0 else 0
    st.progress(progress)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Question", f"{session_state.score['total'] + 1}/{num_questions}")
    with col2:
        st.metric("Correct", session_state.score['correct'])
    with col3:
        accuracy = (session_state.score['correct'] / session_state.score['total'] * 100) if session_state.score['total'] > 0 else 0
        st.metric("Accuracy", f"{accuracy:.1f}%")
    if session_state.score['total'] >= num_questions:
        show_quiz_results(session_state)
        return
    if not session_state.current_question:
        with st.spinner("Generating question..."):
            session_state.current_question = session_state.quiz_bot.generate_question(
                question_type=quiz_type,
                difficulty=difficulty
            )
    if session_state.current_question:
        question_data = session_state.current_question
        st.markdown(f"### Question {session_state.score['total'] + 1}")
        st.markdown(f"**{question_data['question']}**")
        if question_data['type'] == 'multiple_choice':
            answer = st.radio(
                "Choose your answer:",
                question_data['options'],
                key=f"q_{session_state.score['total']}"
            )
            if st.button("Submit Answer", type="primary"):
                handle_answer_submission(session_state, answer, question_data)
        elif question_data['type'] == 'true_false':
            answer = st.radio(
                "Choose your answer:",
                ["True", "False"],
                key=f"q_{session_state.score['total']}"
            )
            if st.button("Submit Answer", type="primary"):
                handle_answer_submission(session_state, answer, question_data)
        elif question_data['type'] == 'short_answer':
            answer = st.text_input(
                "Your answer:",
                key=f"q_{session_state.score['total']}"
            )
            if st.button("Submit Answer", type="primary") and answer:
                handle_answer_submission(session_state, answer, question_data)

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