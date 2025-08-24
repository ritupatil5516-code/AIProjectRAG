
import os, json, streamlit as st
from calendar import monthrange
from datetime import datetime, timezone

from app.services.data_source import LocalJSONDataSource, MCPDataSource
from app.services.llm_service import LLMService
from app.controllers.chat_controller import ChatController, SYSTEM
from app.services.agreement_extractor import ensure_agreement_json
from app.services.interest_calc import build_daily_balances, monthly_interest_from_adb

st.set_page_config(page_title="Banking Co-Pilot (Agreement-first)", layout="wide")
st.title("💳 Banking Co-Pilot — Agreement-first · Semantic RAG · Pydantic")

use_mcp = st.sidebar.toggle("Use MCP mock API", False)
top_k = st.sidebar.slider("Top-K retrieval", 4, 16, 8)
open_evidence = st.sidebar.toggle("Open evidence by default", False)
st.sidebar.caption("Set OPENAI_API_KEY (and OPENAI_BASE_URL/MODEL). Place your agreement PDF at data/agreement.pdf.")

def load_card(path: str) -> str:
    try: return open(path, "r", encoding="utf-8").read().strip()
    except Exception: return ""

if "controller" not in st.session_state or st.session_state.get("rebuild_controller"):
    source = MCPDataSource() if use_mcp else LocalJSONDataSource()
    bundle = source.load()
    glossary = load_card("./context/glossary.md")
    rules = load_card("./context/rules.md")
    formulas = load_card("./context/formulas.md")
    st.session_state.controller = ChatController(bundle, glossary, rules, formulas)
    st.session_state.bundle = bundle
    st.session_state.rebuild_controller = False

controller: ChatController = st.session_state.controller
bundle = st.session_state.bundle

agreement = ensure_agreement_json()

if "msgs" not in st.session_state: st.session_state.msgs = []
for msg in st.session_state.msgs:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            with st.expander("📂 Evidence", expanded=open_evidence):
                if msg.get("used_fields"):
                    st.markdown("**Used fields (model-reported):**")
                    st.code("\n".join(msg.get("used_fields") or []), language="text")
                if msg.get("notes"):
                    st.markdown("**Notes:**")
                    st.code(msg.get("notes",""), language="text")
                if msg.get("snippets"):
                    st.markdown("**Top‑K snippets provided to the model:**")
                    for i, snip in enumerate(msg.get("snippets"), 1):
                        st.code(f"[{i}] {snip}", language="json")

q = st.chat_input("Ask about balances, interest (Mar/Apr), trailing interest, payments, etc.")
if q:
    st.session_state.msgs.append({"role":"user","content":q})
    with st.chat_message("user"): st.markdown(q)

    snippets = controller.retrieve(q, k=top_k)
    prelude = controller.prelude(q, snippets)
    result = LLMService().ask(SYSTEM, prelude)

    calc = result.get("calc_request")
    final = None
    if calc and agreement:
        try:
            if calc.get("type") == "interest_month":
                period = calc.get("period")  # "YYYY-MM"
                year, month = map(int, period.split("-"))
                start = datetime(year, month, 1, tzinfo=timezone.utc)
                from calendar import monthrange
                end = datetime(year, month, monthrange(year, month)[1], tzinfo=timezone.utc)
                txs = [t.model_dump() for t in bundle.transactions]
                daily = build_daily_balances(txs, start, end)
                apr = agreement.purchaseApr or (bundle.account_summary[0].purchaseApr if bundle.account_summary and bundle.account_summary[0].purchaseApr else None)
                if daily and apr is not None:
                    amt = monthly_interest_from_adb(apr, agreement.apr_basis, daily)
                    final = f"Interest for {period}: ${amt:.2f} (ADB, APR {apr:.2f}% / {agreement.apr_basis})."
        except Exception:
            final = None

    if not final:
        final = result.get("answer") or "No matching data found."

    with st.chat_message("assistant"):
        st.markdown(final)
        with st.expander("📂 Evidence", expanded=open_evidence):
            if result.get("used_fields"):
                st.markdown("**Used fields (model-reported):**")
                st.code("\n".join(result.get("used_fields") or []), language="text")
            if result.get("notes"):
                st.markdown("**Notes:**")
                st.code(result.get("notes",""), language="text")
            st.markdown("**Top‑K snippets provided to the model:**")
            for i, snip in enumerate(snippets, 1):
                st.code(f"[{i}] {snip}", language="json")

    st.session_state.msgs.append({
        "role":"assistant",
        "content":final,
        "used_fields":result.get("used_fields") or [],
        "notes":result.get("notes") or "",
        "snippets":snippets
    })
    st.rerun()

st.caption("Agreement-first: parses data/agreement.pdf → agreement.json automatically; falls back to rules/formulas if needed.")
