import streamlit as st, os, json
from app.controllers.chat_controller import ChatController
from app.services.agreement_extractor import ensure_agreement_json
from app.utils.loader import load_corpus

st.set_page_config(page_title="Banking Co‑Pilot", page_icon="💳", layout="wide")

st.sidebar.title("💳 Banking Co‑Pilot")
st.sidebar.caption("Deterministic + Agreement‑first (FAISS, Pydantic)")

corpus = load_corpus("./data")
agreement = ensure_agreement_json()

if "controller" not in st.session_state:
    st.session_state.controller = ChatController(corpus=corpus, agreement=agreement)
ctrl = st.session_state.controller

st.markdown("## 🧠 Banking Co‑Pilot — deterministic answers")
st.caption("Ask about balances, statements, transactions, scheduled payments, interest, trailing interest…")

chips = [
    "what is the total interest",
    "what is the total interest this year",
    "what is the total interest this month",
    "are there any scheduled payments?",
    "when was my last payment?",
    "what is my current balance?",
    "why was I charged interest in March?",
    "what do I pay to avoid more interest?"
]
with st.expander("Sample questions"):
    st.write(",  ".join(f"`{c}`" for c in chips))

# History
for role, text, ev in ctrl.history:
    if role == "user":
        st.markdown(f"**🧑‍💻 {text}**")
    else:
        st.markdown(f"💡 {text}")
        if ev:
            with st.expander("Evidence"):
                for ln in ev:
                    st.markdown(f"- {ln}")

q = st.chat_input("Ask about balances, statements, transactions, payments, interest…")
if q:
    ctrl.add_user(q)
    result = ctrl.answer(q)
    ctrl.add_assistant(result["answer"], evidence=result.get("evidence_lines"))
    st.rerun()
