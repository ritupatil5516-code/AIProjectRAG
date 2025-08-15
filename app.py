
import os, json, streamlit as st
from app.services.data_source import LocalJSONDataSource, MCPDataSource
from app.services.llm_service import LLMService
from app.controllers.chat_controller import ChatController, SYSTEM

st.set_page_config(page_title="Banking Co-Pilot (FAISS + Pydantic)", layout="wide")
st.title("💳 Banking Co-Pilot — FAISS RAG + Pydantic Models")

use_mcp = st.sidebar.toggle("Use MCP mock API", False)
top_k = st.sidebar.slider("Top-K", 4, 16, 8)
show_evidence_by_default = st.sidebar.toggle("Open evidence by default", False)
st.sidebar.caption("Set OPENAI_API_KEY (and OPENAI_EMBED_MODEL or local sentence-transformers).")

source = MCPDataSource() if use_mcp else LocalJSONDataSource()
data = source.load()

def load_card(path):
    try: return open(path, "r", encoding="utf-8").read().strip()
    except Exception: return ""
glossary = load_card("./context/glossary.md")
rules = load_card("./context/rules.md")
formulas = load_card("./context/formulas.md")

if "controller" not in st.session_state:
    st.session_state.controller = ChatController(data, glossary, rules, formulas)
controller = st.session_state.controller

if "msgs" not in st.session_state: st.session_state.msgs = []
for role, content in st.session_state.msgs:
    with st.chat_message(role): st.markdown(content)

q = st.chat_input("Ask about balances, statements, transactions, payments, interest…")
if q:
    st.session_state.msgs.append(("user", q))
    with st.chat_message("user"): st.markdown(q)

    snippets = controller.retrieve(q, k=top_k)
    prelude = controller.prelude(q, snippets)
    result = LLMService().ask(SYSTEM, prelude)

    final = result.get("answer") or "No matching data found."
    used_fields = result.get("used_fields") or []
    notes = result.get("notes") or ""

    with st.chat_message("assistant"):
        st.markdown(final)
        with st.expander("Evidence", expanded=show_evidence_by_default):
            st.markdown("**Used fields (model-reported):**")
            if used_fields: st.code("\n".join(used_fields), language="text")
            else: st.write("—")
            if notes:
                st.markdown("**Notes:**"); st.code(notes, language="text")
            st.markdown("**Top‑K snippets provided to the model:**")
            for i, snip in enumerate(snippets, 1):
                st.code(f"[{i}] {snip}", language="json")

st.caption("This root app.py is non-empty and runnable. 'app/' is a package (has __init__.py).")
