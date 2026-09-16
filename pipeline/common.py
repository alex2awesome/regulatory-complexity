"""Shared helpers for the pipeline CLIs (run.py, instrument.py, dashboard/build.py)."""

import json
import pathlib
import random


def load(p):
    return json.loads(pathlib.Path(p).read_text())


def read_statutes(paths):
    return "\n\n".join(
        f"===== SOURCE: {pathlib.Path(p).name} =====\n{pathlib.Path(p).read_text()}"
        for p in paths
    )


def fuzz_panel(fields, n=200, seed=0, panel_id=None):
    """Random case panel from an input-field list (coverage fuzzing, no API)."""
    rng = random.Random(seed)
    cases = []
    for i in range(n):
        facts = {}
        for f in fields:
            t = f["type"]
            if t == "boolean":
                facts[f["name"]] = rng.random() < 0.5
            elif t == "number":
                lo, hi = f.get("range", [0, 100])
                facts[f["name"]] = round(rng.uniform(lo, hi), 2)
            elif t == "date":
                facts[f["name"]] = f"{rng.randint(1960, 2026)}-{rng.randint(1, 12):02d}-01"
            elif t == "enum":
                facts[f["name"]] = rng.choice(f.get("enum_values", ["unknown"]))
            else:
                facts[f["name"]] = "fuzz"
        cases.append({"case_id": f"fuzz_{i:04d}", "facts": facts})
    return {"panel_id": panel_id or f"fuzz_{seed}",
            "generation": {"mode": "fuzz", "detail": f"seed={seed}"},
            "cases": cases}


def union_fields(trees):
    """Union of input schemas across compilations (field-name keyed; first
    definition wins). NOTE: without a semantic crosswalk, same-named fields are
    assumed to denote the same latent fact and differently-named fields get
    independent values — cross-tree comparisons on a union panel are only as
    coherent as the shared vocabulary."""
    seen, out = set(), []
    for t in trees:
        for f in t["input_schema"]["fields"]:
            if f["name"] not in seen:
                seen.add(f["name"])
                out.append(f)
    return out
