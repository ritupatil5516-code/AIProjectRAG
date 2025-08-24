
import os, json, hashlib, re
from typing import Optional
from app.core.schemas_agreement import Agreement

PDF_PATH = "./data/agreement.pdf"
JSON_PATH = "./data/agreement.json"
META_PATH = "./data/agreement.meta.json"

def _pdf_text(path: str) -> str:
    from PyPDF2 import PdfReader
    reader = PdfReader(path)
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)

def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def _clean_pct(s: str) -> float:
    return float(s.strip().replace("%",""))

def _parse_aprs(txt: str) -> dict:
    """Return dict with potential fields: purchaseApr, cashAdvanceApr, balanceTransferApr, penaltyApr."""
    out = {"purchaseApr": None, "cashAdvanceApr": None, "balanceTransferApr": None, "penaltyApr": None}
    t = txt

    # Explicit "Purchase APR ... X.XX%"
    m = re.search(r"(?:Purchase\s+APR[^0-9]{0,40}?)(\d{1,2}\.\d{2})\s*%", t, re.IGNORECASE)
    if m:
        out["purchaseApr"] = _clean_pct(m.group(1))

    # Cash Advance APR
    m = re.search(r"(?:Cash\s+Advance\s+APR[^0-9]{0,40}?)(\d{1,2}\.\d{2})\s*%", t, re.IGNORECASE)
    if m:
        out["cashAdvanceApr"] = _clean_pct(m.group(1))

    # Balance Transfer APR
    m = re.search(r"(?:Balance\s+Transfer\s+APR[^0-9]{0,40}?)(\d{1,2}\.\d{2})\s*%", t, re.IGNORECASE)
    if m:
        out["balanceTransferApr"] = _clean_pct(m.group(1))

    # Penalty APR
    m = re.search(r"(?:Penalty\s+APR[^0-9]{0,40}?)(\d{1,2}\.\d{2})\s*%", t, re.IGNORECASE)
    if m:
        out["penaltyApr"] = _clean_pct(m.group(1))

    # Range capture (for meta only)
    rng = re.search(r"(?:APRs?|Purchase APRs?).{0,40}range\s+from\s+(\d{1,2}\.\d{2})\s*%\s+to\s+(\d{1,2}\.\d{2})\s*%", t, re.IGNORECASE)

    return out, (rng.group(1), rng.group(2)) if rng else None

def _infer_defaults_from_text(txt: str) -> Agreement:
    apr_basis = 365
    if re.search(r"DPR\s*=\s*APR\s*/\s*365", txt, re.I):
        apr_basis = 365
    method = "ADB_including_new" if re.search(r"daily balance method\s*\(including new", txt, re.I) else "ADB_including_new"

    aprs, rng = _parse_aprs(txt)

    ag = Agreement(
        purchaseApr=aprs.get("purchaseApr"),
        cashAdvanceApr=aprs.get("cashAdvanceApr"),
        balanceTransferApr=aprs.get("balanceTransferApr"),
        penaltyApr=aprs.get("penaltyApr"),
        apr_basis=apr_basis,
        interest_method=method,
        hasGracePeriod=True,
        graceCondition="prior statement paid in full by due date",
        compounding="daily",
        postingDay="statement_close",
        minFixedFloor=25.0,
        minPercentOfBalance=0.01,
        rounding="to_cent",
        trailingInterest=True
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
        try:
            meta = json.load(open(META_PATH))
        except Exception:
            meta = {}

    needs_extract = (meta.get("pdf_sha256") != pdf_hash) or (not os.path.exists(JSON_PATH))
    if needs_extract:
        txt = _pdf_text(PDF_PATH)
        agreement = _infer_defaults_from_text(txt)
        with open(JSON_PATH, "w") as f:
            json.dump(agreement.model_dump(), f, indent=2)
        meta = {"pdf_sha256": pdf_hash}
        rng = agreement.__dict__.get("_apr_range_detected")
        if rng:
            meta["purchaseAprRange"] = {"low": float(rng[0]), "high": float(rng[1])}
        with open(META_PATH, "w") as f:
            json.dump(meta, f, indent=2)
        return agreement
    return Agreement(**json.load(open(JSON_PATH)))
