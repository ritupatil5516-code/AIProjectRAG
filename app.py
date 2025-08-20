# app.py — minimal change: keep all Q&A in the chat window

import os
import json
import streamlit as st

# project imports (your existing modules)
from app.services.data_source import LocalJSONDataSource, MCPDataSource
from app.services.llm_service import LLMService
from app.controllers.chat_controller import ChatController, SYSTEM

# ---------- Page ----------
st.set_page_config(page_title="Agent desktop Co-Pilot", layout="wide")
st.title("💳 Agent desktop Co-Pilot")

# ---------- Sidebar controls (same as before) ----------
use_mcp = st.sidebar.toggle("Use MCP mock API", False)
top_k = st.sidebar.slider("Top-K retrieval", 4, 16, 8)
st.sidebar.caption("Set OPENAI_API_KEY (and OPENAI_BASE_URL/MODEL for Llama-70B if using a compatible endpoint).")

# ---------- Build controller once ----------
def load_card(path: str) -> str:
    try:
        return open(path, "r", encoding="utf-8").read().strip()
    except Exception:
        return ""

if "controller" not in st.session_state:
    source = MCPDataSource() if use_mcp else LocalJSONDataSource()
    data = source.load()
    glossary = load_card("./context/glossary.md")
    rules = load_card("./context/rules.md")
    formulas = load_card("./context/formulas.md")
    st.session_state.controller = ChatController(data, glossary, rules, formulas)

controller: ChatController = st.session_state.controller

# ---------- Chat history (NEW) ----------
# store a list of (role, content) tuples so previous Q&A persist
if "msgs" not in st.session_state:
    st.session_state.msgs = []

# render previous messages
for role, content in st.session_state.msgs:
    with st.chat_message(role):
        st.markdown(content)

# ---------- Input + answer ----------
q = st.chat_input("Ask about balances, statements, transactions, payments, interest…")
if q:
    # 1) add/show user message
    st.session_state.msgs.append(("user", q))
    with st.chat_message("user"):
        st.markdown(q)

    # 2) retrieve + ask LLM (your existing flow)
    snippets = controller.retrieve(q, k=top_k)
    prelude = controller.prelude(q, snippets)
    result = LLMService().ask(SYSTEM, prelude)
    final = result.get("answer") or "No matching data found."

    # 3) add/show assistant message
    with st.chat_message("assistant"):
        st.markdown(final)
    st.session_state.msgs.append(("assistant", final))

    # 4) re-render so the full thread persists
    st.rerun()

# ---------- Footer ----------
st.caption("Semantic RAG: FAISS cosine on normalized embeddings · Pydantic models · Temperature=0 for deterministic responses.")