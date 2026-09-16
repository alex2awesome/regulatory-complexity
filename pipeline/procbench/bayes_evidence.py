"""Public-evidence adapters for the Bayesian process pilot. No truth/spec imports.

The cached extractor is deliberately kept separate from inference. Enrichment is
limited to literal quotes and explicit fields; it does not consult a solved model.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import pathlib
import re

STOP = set("a an the to of for by at in on and or with from this that is be it its as "
           "your you their our will shall must may required application permit program "
           "submittal staff city department division".split())
ALIASES = {"submit": "file", "submission": "file", "filing": "file", "filed": "file",
           "pay": "payment", "paid": "payment", "grant": "issue", "issuance": "issue",
           "issuing": "issue", "reviewing": "review", "inspection": "inspect",
           "inspector": "inspect", "inspectors": "inspect", "documents": "document",
           "records": "record", "requests": "request", "hearing": "hearing"}


def norm(text):
    return " ".join(re.findall(r"[a-z0-9]+", str(text).lower()))


def tokens(text):
    canonical = (ALIASES.get(w, w) for w in norm(text).split())
    return sorted({w for w in canonical if w not in STOP}) or ["activity"]


def actor_name(value):
    """Only obvious aliases; generic 'staff' is NOT an identified organization."""
    s = norm(value or "")
    if s in {"", "staff", "agency", "city", "the city", "local authority", "the agency",
             "the local authority", "the cashier", "cashier", "the lady at the counter"}:
        return None
    if s in {"you", "applicant", "vendor", "the vendor", "the applicant", "permit applicant"}:
        return "applicant"
    if s.startswith("the "):
        s = s[4:]
    return s


def duration_claim(timing, doc, field="elapsed_days"):
    if not isinstance(timing, dict):
        return None
    kind = timing.get("kind") or ("median" if "median_days" in timing else "reported")
    value = timing.get("value_days", timing.get("median_days", timing.get("value")))
    claim = {"kind": kind, "value": value, "field": field,
             "quote": timing.get("quote", ""), "source": doc["source_family"],
             "doc_id": doc["id"], "source_kind": doc["kind"],
             "n": timing.get("n"), "scope": timing.get("scope", "step"),
             "units": timing.get("units", "hours" if field.endswith("hours") else "calendar_days")}
    bounds = timing.get("range_days") or timing.get("range")
    # Recover explicit rounding intervals, not vague language such as 'a while'.
    if not bounds and field == "elapsed_days":
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:to|[-–])\s*(\d+(?:\.\d+)?)\s*"
                          r"(days?|weeks?|months?)", str(claim["quote"]), re.I)
        if match:
            factor = 7 if match[3].lower().startswith("week") else 30 if match[3].lower().startswith("month") else 1
            bounds = [float(match[1]) * factor, float(match[2]) * factor]
    if bounds and len(bounds) == 2 and all(isinstance(v, (int, float)) for v in bounds):
        claim["interval"] = list(bounds)
    # Business and calendar days cannot silently be equated.
    if "business day" in str(claim["quote"]).lower() and "calendar" not in str(claim["quote"]).lower():
        claim["units"] = "business_days"
    if kind in {"statutory_cap", "target", "deadline"}:
        claim["usable"] = False
        claim["excluded_reason"] = "normative target, not realized duration"
    elif claim["units"] == "business_days":
        claim["usable"] = False
        claim["excluded_reason"] = "business/calendar conversion requires a calendar"
    else:
        claim["usable"] = isinstance(value, (int, float)) and math.isfinite(value) and value >= 0
    return claim


def load_cached(candidate_dir, artifacts=None):
    cd = pathlib.Path(candidate_dir)
    index = json.loads((cd / "index.json").read_text())
    documents, missing = [], []
    for row in index:
        path = cd / f"cand_{row['i']:02d}.json"
        if not path.exists():
            missing.append(str(path)); continue
        extraction = json.loads(path.read_text())
        doc = {**row, "source_family": row.get("source_family") or row["id"],
               "claims": [], "extraction_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        if artifacts:
            source = pathlib.Path(artifacts) / f"{row['id']}.md"
            if source.exists():
                txt = source.read_text()
                doc["source_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
                for key in ("date", "jur", "url"):
                    match = re.search(rf"^{key}:\s*(.+)$", txt, re.M)
                    if match:
                        doc[key] = match[1].strip()
        for pos, raw in enumerate(extraction.get("steps", [])):
            c = copy.deepcopy(raw)
            c.update({"claim_id": f"{doc['id']}:{pos}", "doc_id": doc["id"],
                      "source_family": doc["source_family"], "source_kind": doc["kind"],
                      "actor_original": c.get("actor"), "actor": actor_name(c.get("actor")),
                      "words": tokens(c.get("name", ""))})
            c["measurements"] = []
            for key in ("timing", "applicant_hours", "agency_hours"):
                t = c.get(key)
                if isinstance(t, (float, int)):
                    t = {"value": t, "kind": "observed"}
                measurement = duration_claim(t, doc, "elapsed_days" if key == "timing" else key)
                if measurement:
                    c["measurements"].append(measurement)
            doc["claims"].append(c)
        documents.append(doc)
    if missing:
        raise ValueError("Missing extraction files: " + ", ".join(missing))
    return {"schema": "process-evidence/1", "documents": documents,
            "provenance": {"adapter": "cached-document-extractions", "candidate_dir": str(cd),
                           "hidden_truth_read": False,
                           "limitations": ["legacy extractor omits process-level timing and case IDs",
                                           "no manually audited extraction error calibration"]}}


def flatten(evidence):
    """Stable ordering and exact source-family deduplication (not guessed lineage)."""
    documents = sorted(evidence["documents"], key=lambda d: d["id"])
    claims, seen = [], set()
    for doc in documents:
        family = doc.get("source_family") or doc["id"]
        for raw in sorted(doc.get("claims", []), key=lambda c: c["claim_id"]):
            c = copy.deepcopy(raw)
            c.setdefault("doc_id", doc["id"])
            c.setdefault("source_kind", doc["kind"])
            c.setdefault("source_family", family)
            c.setdefault("words", tokens(c["name"]))
            content = {k: c.get(k) for k in ("actor", "timing", "fee")}
            content["measurements"] = [{k: v for k, v in m.items() if k not in {"doc_id", "source"}}
                                       for m in c.get("measurements", [])]
            signature = (family, norm(c["name"]), json.dumps(content, sort_keys=True))
            if signature in seen:
                continue
            seen.add(signature); claims.append(c)
    return documents, claims
