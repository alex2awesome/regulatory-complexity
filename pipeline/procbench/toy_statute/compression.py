"""Exact multiplicities for exchangeable whole administrative records.

Never independently histogram milestones of the same project. Unknown metadata,
source and cohort fields remain in the key. Source rows are not modified.
"""
from datetime import date
import json


def multiplicity(row):
    n = row.get("multiplicity", 1)
    if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
        raise ValueError("administrative multiplicity must be a positive integer")
    return n


def compress_admin(rows):
    grouped = {}
    for row in rows:
        start = date.fromisoformat(row["submitted"])
        key = {k: v for k, v in row.items()
               if k not in ("record_id", "case_id", "id", "submitted", "decided", "milestones", "multiplicity")}
        key["elapsed_days"] = (date.fromisoformat(row["decided"]) - start).days
        if "milestones" in row:
            key["milestone_days"] = {k: (date.fromisoformat(v) - start).days
                                     for k, v in row["milestones"].items()}
        signature = json.dumps(key, sort_keys=True, allow_nan=False)
        if signature not in grouped:
            grouped[signature] = dict(row, multiplicity=0)
        grouped[signature]["multiplicity"] += multiplicity(row)
    return list(grouped.values())
