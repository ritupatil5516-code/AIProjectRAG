
import os, json
from typing import Dict, Any

class LLMService:
    def __init__(self):
        from openai import OpenAI  # type: ignore
        self.client = OpenAI(base_url=os.getenv("OPENAI_BASE_URL"))
        self.model = os.getenv("MODEL", os.getenv("OPENAI_MODEL","gpt-4o-mini"))
    def ask(self, system: str, prelude: str) -> Dict[str, Any]:
        resp = self.client.chat.completions.create(
            model=self.model, temperature=0.0,
            response_format={"type":"json_object"},
            messages=[{"role":"system","content":system},
                      {"role":"user","content":prelude}]
        )
        try:
            return json.loads(resp.choices[0].message.content)
        except Exception:
            return {"answer":"No matching data found.","used_fields":[]}
