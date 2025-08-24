
import os, json
from typing import Optional
from app.core.schemas import DataBundle, AccountSummary, Transaction, Statement, Payment
from app.core.schemas_agreement import Agreement

class LocalJSONDataSource:
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.getenv("DATA_DIR","./data")
    def load(self) -> DataBundle:
        def read(name): return json.load(open(f"{self.data_dir}/{name}.json"))
        return DataBundle(
            account_summary=[AccountSummary(**o) for o in read("account_summary")],
            transactions=[Transaction(**o) for o in read("transactions")],
            statements=[Statement(**o) for o in read("statements")],
            payments=[Payment(**o) for o in read("payments")]
        )

class MCPDataSource:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("MCP_BASE","http://127.0.0.1:8765")
    def load(self) -> DataBundle:
        import urllib.request, json as _json
        def _get(path):
            with urllib.request.urlopen(self.base_url+path) as r:
                return _json.loads(r.read().decode())
        return DataBundle(
            account_summary=[AccountSummary(**o) for o in _get("/api/account-summary")],
            transactions=[Transaction(**o) for o in _get("/api/transactions")],
            statements=[Statement(**o) for o in _get("/api/statements")],
            payments=[Payment(**o) for o in _get("/api/payments")]
        )

class AgreementSource:
    def __init__(self, path: str = "./data/agreement.json"):
        self.path = path
    def load_if_exists(self) -> Optional[Agreement]:
        if not os.path.exists(self.path):
            return None
        return Agreement(**json.load(open(self.path)))
