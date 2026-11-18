"""Burden-optimal VALID process design per town, before and after statute edits.

Combines validity.py (which designs are valid, per reading of the statute)
with a saved burden table (posterior interval of expected total days per
town and design, e.g. runs/.../W0/process_menu_burden.json). The choice uses
the POSTERIOR median only; truth columns, when present, are evaluation.

Answers the core-goal questions (docs/CORE_GOAL.md, guiding questions):
  1. under a decision model, which process is optimal among valid ones;
  2. which statute edits enlarge the valid set to include a better process.

  python -m pipeline.procbench.toy_statute.design_optimum --burden runs/toy_statute_20260926/W0/process_menu_burden.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import validity

# burden-table keys -> validity design ids
KEY = {**{s: s for s in ("S1", "S2", "S3", "S4", "S5", "S6")},
       **{f"{s}-concurrent": f"{s}c" for s in ("S2", "S3", "S4", "S5", "S6")}}


def optimum(burden: dict, tau: float = 1.0) -> dict:
    designs = {d.id: d for d in validity.all_designs()}
    scen = {"none": {}} | {e: f for e, (f, _) in validity.EDITS.items()}
    out = {}
    for sc, fixed in scen.items():
        pv = {k: validity.evaluate(designs[v], fixed=fixed)["p_valid"] for k, v in KEY.items()}
        out[sc] = {"p_valid": pv, "towns": {}}
        for town, tab in burden.items():
            ok = [k for k in KEY if k in tab and pv[k] >= tau - 1e-12]
            if not ok:
                out[sc]["towns"][town] = None
                continue
            best = min(ok, key=lambda k: tab[k]["post_days"][1])
            out[sc]["towns"][town] = {
                "design": KEY[best], "post_days": tab[best]["post_days"],
                "truth_days": tab[best].get("truth_days"), "admissible": [KEY[k] for k in ok]}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--burden", required=True)
    ap.add_argument("--tau", type=float, default=1.0,
                    help="minimum P(valid) for a design to be admissible (1.0 = valid under every remaining reading)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    res = optimum(json.loads(Path(a.burden).read_text()), a.tau)
    for sc, r in res.items():
        cells = []
        for t, v in r["towns"].items():
            cells.append(f"{t}: none" if v is None else
                         f"{t}: {v['design']} {v['post_days'][1]:.1f}d [{v['post_days'][0]:.1f},{v['post_days'][2]:.1f}]"
                         + (f" truth {v['truth_days']:.1f}" if v["truth_days"] is not None else ""))
        print(f"{sc:18s} " + " | ".join(cells))
    if a.out:
        Path(a.out).write_text(json.dumps({"tau": a.tau, "results": res}, indent=1))
    return res


if __name__ == "__main__":
    main()
