import os, json, hashlib, re
from typing import Optional
from PyPDF2 import PdfReader
from app.core.schemas import Agreement

PDF_PATH = "./data/agreement.pdf"
JSON_PATH = "./data/agreement.json"
META_PATH = "./data/agreement.meta.json"

def _pdf_text(path: str) -> str:
    reader = PdfReader(path)
    return "\n".join((p.extract_text() or "") for p in reader.pages)

def _sha256(path: str) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def _clean_pct(s: str) -> float:
    return float(s.strip().replace("%",""))

def _parse_aprs(txt: str):
    out = {"purchaseApr": None, "cashAdvanceApr": None, "balanceTransferApr": None, "penaltyApr": None}
    m = re.search(r"(?:Purchase\s+APR[^0-9]{0,40}?)(\d{1,2}\.\d{2})\s*%", txt, re.I)
    if m: out["purchaseApr"] = _clean_pct(m.group(1))
    m = re.search(r"(?:Cash\s+Advance\s+APR[^0-9]{0,40}?)(\d{1,2}\.\d{2})\s*%", txt, re.I)
    if m: out["cashAdvanceApr"] = _clean_pct(m.group(1))
    m = re.search(r"(?:Balance\s+Transfer\s+APR[^0-9]{0,40}?)(\d{1,2}\.\d{2})\s*%", txt, re.I)
    if m: out["balanceTransferApr"] = _clean_pct(m.group(1))
    m = re.search(r"(?:Penalty\s+APR[^0-9]{0,40}?)(\d{1,2}\.\d{2})\s*%", txt, re.I)
    if m: out["penaltyApr"] = _clean_pct(m.group(1))
    rng = re.search(r"(?:APRs?|Purchase APRs?).{0,40}range\s+from\s+(\d{1,2}\.\d{2})\s*%\s+to\s+(\d{1,2}\.\d{2})\s*%", txt, re.I)
    return out, (rng.group(1), rng.group(2)) if rng else None

def _infer_defaults_from_text(txt: str) -> Agreement:
    aprs, rng = _parse_aprs(txt)
    ag = Agreement(
        purchaseApr=aprs.get("purchaseApr"),
        cashAdvanceApr=aprs.get("cashAdvanceApr"),
        balanceTransferApr=aprs.get("balanceTransferApr"),
        penaltyApr=aprs.get("penaltyApr"),
        apr_basis=365,  # default unless PDF states otherwise
        interest_method="ADB_including_new",
        hasGracePeriod=True,
        compounding="daily",
        rounding="sum_then_round",
        tz="America/New_York",
    )
    ag.__dict__["_apr_range_detected"] = rng
    return ag

def ensure_agreement_json() -> Optional[Agreement]:
    if not os.path.exists(PDF_PATH):
        if os.path.exists(JSON_PATH):
            return Agreement(**json.load(open(JSON_PATH)))
        return None
    pdf_hash = _sha256(PDF_PATH)
    meta = {}
    if os.path.exists(META_PATH):
        try: meta = json.load(open(META_PATH))
        except Exception: meta = {}
    needs = (meta.get("pdf_sha256") != pdf_hash) or (not os.path.exists(JSON_PATH))
    if needs:
        txt = _pdf_text(PDF_PATH)
        ag = _infer_defaults_from_text(txt)
        with open(JSON_PATH, "w") as f: json.dump(ag.model_dump(), f, indent=2)
        m = {"pdf_sha256": pdf_hash}
        rng = ag.__dict__.get("_apr_range_detected")
        if rng: m["purchaseAprRange"] = {"low": float(rng[0]), "high": float(rng[1])}
        with open(META_PATH, "w") as f: json.dump(m, f, indent=2)
        return ag
    return Agreement(**json.load(open(JSON_PATH)))
