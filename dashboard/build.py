#!/usr/bin/env python3
"""Build the inspection dashboard ("Pricing 'Adequate'") from pipeline artifacts.

Usage:
  python3 dashboard/build.py                      # defaults below
  python3 dashboard/build.py --compilations examples/ab2533_v2  # after a re-run

Output: dashboard/out/pricing_adequate.html — publish it as the artifact
(same file path / URL each time). The template is dashboard/template.html;
data is injected at the __DATA_JSON__ placeholder.
"""

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from common import load, fuzz_panel  # noqa: E402
from metrics import static_metrics, behavioral_metrics  # noqa: E402

VARIANT_LABELS = {"v1": "compiled in document order",
                  "v2": "compiled outcomes-backward",
                  "v3": "compiled in official's-eye order"}


def compstats(trees, priors):
    """Per-compilation stats computed fresh from the data (was hardcoded in the
    template — a refactor debt paid 2026-09-01)."""
    out = []
    for i, t in enumerate(trees, 1):
        s = static_metrics(t)
        b = behavioral_metrics(t, fuzz_panel(t["input_schema"]["fields"], n=200, seed=i), priors)
        variant = ((t.get("compiler") or {}).get("prompt_variant") or "").split(":")[-1]
        out.append({
            "n_preds": s["n_predicates"],
            "judgment_mass": s["judgment_mass"],
            "pd": b["p_discretion_exposed"],
            "burden": f"{b['mean_burden']['hours']:.1f} h / ${b['mean_burden']['dollars']:.0f}",
            "flags": " · ".join(f"{v} {k}" for k, v in sorted(s["flags"].items(), key=lambda kv: -kv[1])) or "none",
            "approach": VARIANT_LABELS.get(variant, variant or "unknown variant"),
        })
    return out


def statute(path, secnum, title):
    raw = pathlib.Path(path).read_text()
    m = re.search(rf"^{re.escape(secnum)}\.\s*$", raw, re.M)
    crumbs, text = (raw[: m.start()], raw[m.start():]) if m else ("", raw)
    return {"title": title, "crumbs": re.sub(r"\s*\n\s*", " · ", crumbs.strip()),
            "text": text.strip()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--compilations", default="examples/ab2533",
                    help="directory with compilation_*.json")
    ap.add_argument("--instrument", default="examples/ab2533_sanitation",
                    help="directory with looseness/vignettes/readings JSON")
    ap.add_argument("--world", default="worlds/ab2533_sanitation.json")
    ap.add_argument("--out", default="dashboard/out/pricing_adequate.html")
    args = ap.parse_args()

    comp_dir = ROOT / args.compilations
    inst_dir = ROOT / args.instrument
    comp_files = sorted(comp_dir.glob("compilation_*.json"))
    if not comp_files:
        sys.exit(f"no compilation_*.json in {comp_dir}")

    trees = [load(p) for p in comp_files]
    priors = load(ROOT / "pipeline" / "burden_priors.json")
    data = {
        "world": load(ROOT / args.world),
        "looseness": load(inst_dir / "looseness.json"),
        "vignettes": load(inst_dir / "vignettes.json"),
        "readings": load(inst_dir / "readings.json"),
        "compilations": trees,
        "compstats": compstats(trees, priors),
        "priors": priors,
        "statutes": [
            statute(ROOT / "corpus/ab2533/gov-66311.7.txt", "66311.7",
                    "Cal. Gov. Code § 66311.7 — unpermitted ADU legalization (AB 2533)"),
            statute(ROOT / "corpus/ab2533/hsc-17920.3.txt", "17920.3",
                    "Cal. Health & Safety Code § 17920.3 — “substandard building”"),
        ],
    }
    blob = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    tpl = (ROOT / "dashboard" / "template.html").read_text()
    assert "__DATA_JSON__" in tpl, "template placeholder missing"
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(tpl.replace("__DATA_JSON__", blob))
    print(f"built {out} ({out.stat().st_size / 1024:.0f} KB) "
          f"from {len(comp_files)} compilations in {comp_dir.name}")


if __name__ == "__main__":
    main()
