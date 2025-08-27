# Banking Co-Pilot — Agreement-first (Prod)
Built: 2025-08-22T20:23:22.692155Z

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export OPENAI_API_KEY=sk-...            # required
# optional if using a different endpoint or model:
# export OPENAI_BASE_URL=https://your-endpoint/v1
# export MODEL=llama-3.1-70b-instruct

streamlit run app.py
```

## Notes
- Put your card agreement at `data/agreement.pdf` (your Apple agreement is copied if provided).
- The app will parse the PDF and cache `data/agreement.json`. It recomputes only when the PDF changes.
- For monthly interest math, the LLM will include a `calc_request` and the app computes deterministically via ADB.