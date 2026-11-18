"""Shared readers for the solar process-structure leg.

Every reader returns rows carrying their own provenance: the file they came
from, its SHA256, and a locator inside it. Nothing here reads benchmark truth,
generator specs, ceilings or scores.

The SolarTRACE requirements matrix is a survey response. "NA" in it is a missing
answer and therefore NO reading opportunity. It is never a "No". That
distinction is the whole point of the occupancy design and is enforced here
rather than left to the caller.
"""
from __future__ import annotations

import csv
import hashlib
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
PANEL = ROOT / "runs/solar_panel_20260920/panel_v1.csv"
FORUM = ROOT / "runs/solar_panel_20260920/forum_v1.json"
LEDGER = ROOT / "runs/rw_parse_20260918/solar_permit/evidence.json"
AHJ_REQS = ROOT / "runs/rw_parse_20260918/solar_permit/source/solartrace_dataset_2025-09-09__ahj_permits_reqs.csv"

MISSING = {"", "na", "n/a", "nan", "none", "null", "unknown"}


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def ref(path: pathlib.Path, locator: str) -> dict:
    return {"path": str(path.relative_to(ROOT)), "sha256": sha256(path), "locator": locator}


def present_flag(raw):
    """Map a requirements-matrix cell to True, False or None.

    None means the survey did not answer. It is not a No. Anything that is not
    recognisably yes or no also returns None rather than being coerced.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if text.lower() in MISSING:
        return None
    low = text.lower()
    if low.startswith("yes") or low in {"1", "true", "instant", "required"}:
        return True
    if low.startswith("no") or low in {"0", "false", "not required"}:
        return False
    return None


def count_value(raw):
    if raw is None:
        return None
    text = str(raw).strip()
    if text.lower() in MISSING:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    return value if value == value else None


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower()).strip("_")


def read_requirements():
    """CA rows of the AHJ requirements matrix, keyed by authority slug."""
    out = {}
    with AHJ_REQS.open(encoding="utf-8", errors="replace", newline="") as handle:
        for index, row in enumerate(csv.DictReader(handle), start=2):
            if (row.get("state") or "").strip().upper() != "CA":
                continue
            key = slug(row.get("ahj"))
            if not key:
                continue
            row["__line__"] = index
            out.setdefault(key, row)
    return out


def read_panel():
    with PANEL.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
