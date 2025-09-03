import os, json
from typing import Dict, Any
from openai import OpenAI

class LLMService:
    def __init__(self):
        self.client = OpenAI(base_url=os.getenv("OPENAI_BASE_URL"))
        self.model = os.getenv("MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
        self.seed = int(os.getenv("LLM_SEED","42"))

    def ask(self, system: str, prelude: str) -> Dict[str, Any]:
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=0.0,
                top_p=1.0,
                presence_penalty=0,
                frequency_penalty=0,
                seed=self.seed,
                response_format={"type":"json_object"},
                messages=[{"role":"system","content":system},
                          {"role":"user","content":prelude}],
            )
            txt = resp.choices[0].message.content
        except Exception as e:
            # Endpoint not available or API key missing
            return {"answer":"No matching data found.","used_fields":[],"notes":f"LLM unavailable: {e}"}
        try:
            return json.loads(txt)
        except Exception:
            s, e = txt.find("{"), txt.rfind("}")
            if s != -1 and e != -1 and e > s:
                try: return json.loads(txt[s:e+1])
                except Exception: pass
            return {"answer":"No matching data found.","used_fields":[],"notes":"LLM returned non‑JSON."}
