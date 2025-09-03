# Banking Co‑Pilot — Deterministic, Agreement‑first (FAISS + LLamaIndex‑style RAG)

**What you get**
- Deterministic totals for *total interest* (all / this month / this year) — bypasses the LLM.
- Agreement PDF → `agreement.json` parser (APR, basis, rounding defaults).
- TZ‑aware daily balance builder + rounding policies for exact interest cents.
- FAISS semantic retrieval with local embeddings (MiniLM) for speed.
- Stable LLM decoding (temperature=0, top_p=1, JSON fallback/repair).
- Chat UI that keeps prior answers + expandable “Evidence”.

## Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# LLM (OpenAI-compatible). For OpenAI:
export OPENAI_API_KEY=sk-...

# Optional if using a local Llama endpoint:
# export OPENAI_BASE_URL=http://localhost:11434/v1
# export MODEL=llama-3.1-8b-instruct

# (Optional) freeze now for stable "this month/year" answers
export NOW_UTC="2025-08-31T12:00:00Z"

streamlit run app.py
```

**Data** lives under `/data`. Sample JSONs are included. Drop your agreement PDF at `data/agreement.pdf`.
On start, the app creates `data/agreement.json` + `data/agreement.meta.json` if missing or the PDF changed.
