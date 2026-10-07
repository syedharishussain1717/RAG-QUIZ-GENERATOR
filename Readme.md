# 📝 Study Notes Quiz Generator

A simple RAG app that turns your study notes into an interactive multiple-choice quiz. Upload PDF or TXT notes, optionally enter a topic, and get questions with scoring and explanations.

## Tech Stack
- **LLM:** Groq API (`openai/gpt-oss-120b`)
- **Embeddings:** Hugging Face `all-MiniLM-L6-v2` (runs locally)
- **Retrieval:** NumPy cosine similarity (no vector DB needed)
- **Frontend:** Streamlit

## How It Works
1. Notes are split into overlapping chunks and embedded.
2. If you enter a topic, the chunks closest to it are retrieved. If you leave it blank, chunks are sampled evenly across the whole document.
3. The selected chunks are sent to Groq, which writes MCQs using only that text.
4. You answer the quiz, submit, and see your score with explanations.

## Project Structure
```
quiz-generator/
├── app.py             # Streamlit UI
├── quiz.py            # Chunking, retrieval, quiz generation
├── requirements.txt
└── .gitignore
```

## Run Locally
```bash
git clone https://github.com/<your-username>/quiz-generator.git
cd quiz-generator
pip install -r requirements.txt
export GROQ_API_KEY="your_key_here"   # Windows: set GROQ_API_KEY=your_key_here
streamlit run app.py
```
Get a free API key at https://console.groq.com.

## Deploy on Streamlit Community Cloud
1. Push this repo to GitHub.
2. Go to https://share.streamlit.io and click **Create app**.
3. Select your repo, branch `main`, main file `app.py`.
4. Under **Advanced settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "your_key_here"
   ```
5. Click **Deploy**.

## Usage
1. Upload your notes (PDF or TXT) and click **Process notes**.
2. Optionally enter a topic, and choose the number of questions and difficulty.
3. Click **Generate quiz**, answer the questions, then **Submit answers**.

## Notes
- Scanned (image-only) PDFs are not supported, only text-based PDFs.
- If quiz generation fails, click **Generate quiz** again. The LLM occasionally returns malformed JSON.
- If you get a `model_not_found` error, Groq may have changed its models. Update `LLM_MODEL` in `quiz.py` to one available to your key:
  ```python
  from groq import Groq
  print([m.id for m in Groq(api_key="your_key").models.list().data])
  ```
- Never commit your API key. Use Streamlit Secrets or environment variables.

## License
MIT