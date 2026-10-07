import os
import streamlit as st
from quiz import read_file, chunk_text, embed_chunks, select_chunks, generate_quiz

st.set_page_config(page_title="Quiz Generator", page_icon="📝")
st.title("📝 Study Notes Quiz Generator")

try:
    API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    API_KEY = os.environ.get("GROQ_API_KEY")
if not API_KEY:
    st.error("GROQ_API_KEY is missing. Add it in Streamlit Secrets.")
    st.stop()

st.session_state.setdefault("chunks", [])
st.session_state.setdefault("vectors", None)
st.session_state.setdefault("quiz", None)
st.session_state.setdefault("quiz_id", 0)

# Step 1: upload notes
files = st.file_uploader("Upload your notes (PDF or TXT)", type=["pdf", "txt"], accept_multiple_files=True)
if st.button("Process notes") and files:
    with st.spinner("Reading notes..."):
        text = "\n".join(read_file(f, f.name) for f in files)
        chunks = chunk_text(text)
        if not chunks:
            st.error("No readable text found (scanned PDFs aren't supported).")
        else:
            st.session_state.chunks = chunks
            st.session_state.vectors = embed_chunks(chunks)
            st.session_state.quiz = None
            st.success(f"Notes ready ({len(chunks)} chunks).")

# Step 2: quiz settings
if st.session_state.vectors is not None:
    topic = st.text_input("Topic (optional)", placeholder="e.g. Calvin cycle. Leave blank for the whole notes.")
    c1, c2 = st.columns(2)
    n = c1.slider("Number of questions", 3, 10, 5)
    difficulty = c2.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1)

    if st.button("Generate quiz", type="primary"):
        with st.spinner("Writing questions..."):
            try:
                selected = select_chunks(topic, st.session_state.chunks, st.session_state.vectors)
                st.session_state.quiz = generate_quiz(selected, n, difficulty, API_KEY)
                st.session_state.quiz_id += 1
            except Exception as e:
                st.error(f"Quiz generation failed: {e}. Try again.")

# Step 3: take the quiz
quiz = st.session_state.quiz
if quiz:
    qid = st.session_state.quiz_id
    with st.form("quiz_form"):
        for i, q in enumerate(quiz):
            st.markdown(f"**Q{i+1}. {q['question']}**")
            st.radio("Choose one", q["options"], index=None,
                     key=f"q{qid}_{i}", label_visibility="collapsed")
        submitted = st.form_submit_button("Submit answers")

    if submitted:
        score = 0
        for i, q in enumerate(quiz):
            picked = st.session_state.get(f"q{qid}_{i}")
            correct = q["options"][q["answer_index"]]
            if picked == correct:
                score += 1
                st.success(f"Q{i+1}: Correct ✅ {q['explanation']}")
            else:
                st.error(f"Q{i+1}: {'Not answered' if picked is None else 'Wrong'} ❌ Correct answer: {correct}. {q['explanation']}")
        st.subheader(f"Score: {score} / {len(quiz)}")
