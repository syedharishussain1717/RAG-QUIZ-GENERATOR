import json
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from groq import Groq

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "openai/gpt-oss-120b"

_embedder = None


def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBED_MODEL)
    return _embedder


def read_file(file, name):
    if name.lower().endswith(".pdf"):
        reader = PdfReader(file)
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    return file.read().decode("utf-8", errors="ignore")


def chunk_text(text, size=1000, overlap=150):
    text = " ".join(text.split())
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks


def embed_chunks(chunks):
    v = get_embedder().encode(chunks, normalize_embeddings=True, show_progress_bar=False)
    return np.array(v, dtype="float32")


def select_chunks(topic, chunks, vectors, k=6):
    """Topic given -> retrieve closest chunks. No topic -> sample evenly across the notes."""
    k = min(k, len(chunks))
    if topic.strip():
        q = get_embedder().encode([topic], normalize_embeddings=True)[0]
        ids = np.argsort(vectors @ q)[::-1][:k]
        ids = sorted(ids)
    else:
        ids = np.linspace(0, len(chunks) - 1, num=k, dtype=int)
    return [chunks[i] for i in ids]


def _parse_quiz(raw):
    start, end = raw.find("["), raw.rfind("]")
    data = json.loads(raw[start:end + 1])
    quiz = []
    for q in data:
        opts = q["options"]
        ans = int(q["answer_index"])
        if len(opts) == 4 and 0 <= ans < 4:
            quiz.append({
                "question": q["question"],
                "options": opts,
                "answer_index": ans,
                "explanation": q.get("explanation", ""),
            })
    if not quiz:
        raise ValueError("No valid questions parsed")
    return quiz


def generate_quiz(context_chunks, n, difficulty, api_key):
    context = "\n\n---\n\n".join(context_chunks)
    prompt = f"""Create {n} multiple-choice questions ({difficulty} difficulty) using ONLY the study notes below.

Rules:
- Each question has exactly 4 options, only one correct.
- Options must NOT start with letters like "A)" or "1.".
- Make wrong options plausible, and vary the position of the correct answer.
- Add a one-sentence explanation based on the notes.
- Output ONLY a valid JSON array, no extra text, in this format:
[{{"question": "...", "options": ["...", "...", "...", "..."], "answer_index": 0, "explanation": "..."}}]

Study notes:
{context}"""
    client = Groq(api_key=api_key)
    last_err = None
    for _ in range(2):  # retry once if JSON is malformed
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=4000,
        )
        try:
            return _parse_quiz(resp.choices[0].message.content)
        except Exception as e:
            last_err = e
    raise RuntimeError(f"Could not generate a valid quiz: {last_err}")
