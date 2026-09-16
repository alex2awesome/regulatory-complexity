#!/usr/bin/env python3
"""Synthetic-worlds looseness instrument — CLI.

Offline (no API):
  sweep      — generate a latent-axis case sweep from a world spec
  measure    — reading-ensemble looseness + band mass from a readings file
  plant      — run the planted-world validation ladder (identifiability,
               codability profiles kappa(L) on threshold/conjunction/gestalt)
  screen     — static looseness screener over spans (heuristic lexicon)
  calibrate  — regress screener scores against instrument measurements

LLM stages (need ANTHROPIC_API_KEY):
  render     — realistic vignettes for a sweep (prompt 06)
  elicit     — reading-ensemble decisions over vignettes (prompt 07)
  screen-llm — typology classification of spans (prompt 08)
  tag        — LegalDiscourse span tagging of a statute (prompt 09)
  checklist  — normalize a city checklist (prompt 10)

Typical flow for pricing one word ("adequate sanitation"):
  python instrument.py sweep  --world ../worlds/ab2533_sanitation.json -n 40
  python instrument.py render --world ../worlds/ab2533_sanitation.json --sweep ../examples/ab2533_sanitation/sweep.json
  python instrument.py elicit --world ../worlds/ab2533_sanitation.json --vignettes ../examples/ab2533_sanitation/vignettes.json --n-readers 7
  python instrument.py measure --readings ../examples/ab2533_sanitation/readings.json --world ../worlds/ab2533_sanitation.json
"""

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import worlds as W
import looseness as L
from screener import screen, calibrate
import llm
from llm import llm_json
from common import load

# Personas approximate reading diversity; they are scripted, so the ensemble's
# coverage of REAL readings (city checklists, permit records) is the validity
# check, not an afterthought.
PERSONAS = [
    "a strict big-city building official who trained on the standard building code and holds every unit to it",
    "a county official in a rural jurisdiction who reads the amnesty statute's intent as legalizing every livable unit",
    "a health-department environmental officer whose career has been sanitation enforcement",
    "an official who follows the ABAG/MTC regional checklist template to the letter",
    "a recently hired official who applies the statutory text cautiously and literally, without local custom",
    "a veteran inspector who weighs whether they would let a family member live in the unit",
    "an official in a jurisdiction facing an HCD audit who wants defensible, conservative calls",
    "an official sympathetic to low-income homeowners who cites only conditions posing near-term danger",
]


def write_out(args, name, obj):
    world_id = getattr(args, "_world_id", None) or "instrument"
    out_dir = pathlib.Path(args.out_dir or (HERE.parent / "examples" / world_id))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    path.write_text(json.dumps(obj, indent=2))
    print(f"wrote {path}")
    return path


# ------------------------------------------------------------------ offline

def cmd_sweep(args):
    world = load(args.world)
    args._world_id = world["world_id"]
    cases = W.sweep(world, n=args.n, jitter=args.jitter, seed=args.seed)
    if args.template_render:
        for c in cases:
            c["vignette"] = W.template_render(world, c)
    write_out(args, "sweep.json", {"world_id": world["world_id"], "cases": cases})


def cmd_measure(args):
    data = load(args.readings)
    axis = args.axis
    if axis is None:
        first = data["responses"][0]["theta"]
        axis = sorted(first.keys())[0]
    by_reader = {}
    for r in data["responses"]:
        by_reader.setdefault(r["reader_id"], []).append((r["theta"][axis], bool(r["decision"])))
    summary = L.ensemble_looseness(by_reader)
    if args.world and "band_full" in summary:
        world = load(args.world)
        args._world_id = world["world_id"]
        pop = W.population_sample(world, n=5000, seed=1)
        summary["band_mass_full"] = round(L.band_mass(summary["band_full"], pop), 4)
        summary["band_mass_iqr"] = round(L.band_mass(summary["band_iqr"], pop), 4)
        summary["population_note"] = world.get("population", {}).get("note", "")
    args._world_id = getattr(args, "_world_id", data.get("world_id"))
    write_out(args, "looseness.json", summary)
    if "band_full" in summary:
        print(f"looseness: band={summary['band_full']} (IQR {summary['band_iqr']}), "
              f"sd={summary['cutoff_sd']}, median cutoff={summary['cutoff_median']}, "
              f"non-threshold readers={summary['n_nonthreshold_readers']}/{summary['n_readers']}")
        if "band_mass_full" in summary:
            print(f"discretion exposure: {summary['band_mass_full']:.1%} of population in full band "
                  f"({summary['band_mass_iqr']:.1%} in IQR band) — under a PLACEHOLDER population prior")
    else:
        print("fewer than 2 threshold-like readers; no band estimable")


def cmd_plant(args):
    report = {
        "identifiability_curve": L.identifiability_curve(noise=args.noise),
        "codability_profiles": {
            "threshold_world (code must win)": L.codability_profile(L.threshold_world, noise=args.noise),
            "conjunction_world (code wins at L2)": L.codability_profile(L.conjunction_world, noise=args.noise),
            "gestalt_world (code must plateau)": L.codability_profile(L.gestalt_world, noise=args.noise),
        },
    }
    args._world_id = "planted"
    write_out(args, "planted_ladder.json", report)
    for name, prof in report["codability_profiles"].items():
        print(f"{name}: " + "  ".join(f"{k}={v}" for k, v in prof.items()))


def cmd_screen(args):
    if args.text:
        spans = [{"span_id": "s0", "text": args.text}]
    else:
        spans = load(args.spans)["spans"] if args.spans else []
    results = [dict(screen(s["text"]), span_id=s.get("span_id"), label=s.get("label"), cite=s.get("cite"))
               for s in spans]
    args._world_id = "screener"
    write_out(args, "screen.json", {"results": results})
    for r in sorted(results, key=lambda r: -r["looseness_hypothesis"]):
        print(f"{r['looseness_hypothesis']:.2f}  [{r['mechanism']:>12}]  {r['text'][:80]}")


def cmd_calibrate(args):
    pairs = load(args.pairs)  # [[screener_score, measured], ...]
    args._world_id = "screener"
    write_out(args, "calibration.json", calibrate([tuple(p) for p in pairs]))


# ---------------------------------------------------------------- LLM stages

def cmd_render(args):
    world = load(args.world)
    args._world_id = world["world_id"]
    sweep_data = load(args.sweep)
    out = []
    for case in sweep_data["cases"]:
        extra = f"case_id: {case['case_id']}\n" + W.render_prompt_extra(world, case)
        v = llm_json("06_render_vignette.md", "", None, args.model, extra=extra, max_tokens=1000)
        out.append({**case, "vignette": v["vignette"]})
        print(f"rendered {case['case_id']}")
    write_out(args, "vignettes.json", {"world_id": world["world_id"], "cases": out})


def cmd_elicit(args):
    import random as _random

    world = load(args.world)
    args._world_id = world["world_id"]
    vignettes = load(args.vignettes)["cases"]
    by_id = {c["case_id"]: c for c in vignettes}
    readers = [{"reader_id": f"llm_{i:02d}", "source": "llm",
                "detail": f"{llm.model_desc()} | {PERSONAS[i % len(PERSONAS)]}"}
               for i in range(args.n_readers)]
    responses = []
    for i, reader in enumerate(readers):
        persona = reader["detail"].split(" | ", 1)[1]
        header = (f"Your persona: {persona}\n"
                  f"Statutory predicate: \"{world['predicate']['text']}\" ({world['predicate']['cite']})")
        if args.batch:
            # One call per reader; vignettes shuffled per-reader so
            # presentation order cannot leak the latent axis. Batched
            # elicitation lets the reader self-calibrate across the caseload;
            # per-case mode (default) measures sequential application. The
            # protocol is recorded in the output so the two are never mixed.
            order = vignettes[:]
            _random.Random(1000 + i).shuffle(order)
            listing = "\n\n".join(f"[case_id: {c['case_id']}]\n{c['vignette']}" for c in order)
            out = llm_json("07b_reading_decision_batch.md", "", None, args.model,
                           extra=f"{header}\n\nVignettes ({len(order)}):\n\n{listing}",
                           max_tokens=16000)
            got = {d["case_id"]: d for d in out}
            missing = [c["case_id"] for c in order if c["case_id"] not in got]
            if missing:
                raise RuntimeError(f"{reader['reader_id']} missing decisions for {missing}")
            for c in order:
                d = got[c["case_id"]]
                responses.append({"reader_id": reader["reader_id"], "case_id": c["case_id"],
                                  "theta": c["theta"], "decision": bool(d["decision"]),
                                  "rationale": d.get("rationale", "")})
        else:
            for case in vignettes:
                extra = f"case_id: {case['case_id']}\n{header}\nVignette:\n{case['vignette']}"
                d = llm_json("07_reading_decision.md", "", None, args.model, extra=extra, max_tokens=500)
                responses.append({"reader_id": reader["reader_id"], "case_id": case["case_id"],
                                  "theta": case["theta"], "decision": bool(d["decision"]),
                                  "rationale": d.get("rationale", "")})
        print(f"elicited {reader['reader_id']}")
    write_out(args, "readings.json",
              {"world_id": world["world_id"], "predicate_text": world["predicate"]["text"],
               "elicitation": "batched" if args.batch else "per_case",
               "readers": readers, "responses": responses})


def cmd_screen_llm(args):
    spans = load(args.spans)["spans"]
    results = []
    for s in spans:
        if args.labels and s.get("label") not in args.labels:
            continue
        extra = f"span_id: {s.get('span_id')}\nSpan ({s.get('label')}, {s.get('cite', '?')}): \"{s['text']}\""
        results.append(llm_json("08_screen_span.md", "", None, args.model, extra=extra, max_tokens=1500))
        print(f"screened {s.get('span_id')}")
    args._world_id = "screener"
    write_out(args, "screen_llm.json", {"results": results})


def cmd_tag(args):
    text = "\n\n".join(pathlib.Path(p).read_text() for p in args.statute)
    out = llm_json("09_tag_discourse.md", text, "discourse.schema.json", args.model,
                   extra=f"source_cite: {args.cite}")
    args._world_id = args.rule_id
    write_out(args, "discourse.json", out)
    from collections import Counter
    print(dict(Counter(s["label"] for s in out["spans"])))


def cmd_checklist(args):
    text = pathlib.Path(args.file).read_text()
    out = llm_json("10_normalize_checklist.md", text, None, args.model,
                   extra=f"jurisdiction: {args.jurisdiction}")
    args._world_id = "checklists"
    write_out(args, f"{args.jurisdiction.lower().replace(' ', '_')}.json", out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backend", choices=["codex", "glm", "anthropic"], default=None,
                    help="LLM backend (default: env RC_LLM_BACKEND, else codex — keyless via the Codex CLI's ChatGPT login)")
    ap.add_argument("--model", default=None, help="model override for the chosen backend")
    ap.add_argument("--out-dir", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("sweep")
    p.add_argument("--world", required=True)
    p.add_argument("-n", type=int, default=40)
    p.add_argument("--jitter", type=float, default=0.0)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--template-render", action="store_true", help="attach crude offline vignettes")

    p = sub.add_parser("measure")
    p.add_argument("--readings", required=True)
    p.add_argument("--world", help="world spec, to weight band mass by the population prior")
    p.add_argument("--axis", help="latent axis name (default: first)")

    p = sub.add_parser("plant")
    p.add_argument("--noise", type=float, default=0.05)

    p = sub.add_parser("screen")
    p.add_argument("--spans", help="discourse.json from `tag`")
    p.add_argument("--text", help="screen a single span inline")

    p = sub.add_parser("calibrate")
    p.add_argument("--pairs", required=True, help="JSON [[screener_score, measured], ...]")

    p = sub.add_parser("render")
    p.add_argument("--world", required=True)
    p.add_argument("--sweep", required=True)

    p = sub.add_parser("elicit")
    p.add_argument("--world", required=True)
    p.add_argument("--vignettes", required=True)
    p.add_argument("--n-readers", type=int, default=7)
    p.add_argument("--batch", action="store_true",
                   help="one call per reader over shuffled vignettes (fast pilot protocol) instead of one call per (reader, case)")

    p = sub.add_parser("screen-llm")
    p.add_argument("--spans", required=True)
    p.add_argument("--labels", nargs="*", default=["TEST", "EXCEPTION", "DEFINITION"])

    p = sub.add_parser("tag")
    p.add_argument("--statute", nargs="+", required=True)
    p.add_argument("--cite", required=True)
    p.add_argument("--rule-id", default="tagged")

    p = sub.add_parser("checklist")
    p.add_argument("--file", required=True)
    p.add_argument("--jurisdiction", required=True)

    args = ap.parse_args()
    llm.set_backend(args.backend, args.model)
    {"sweep": cmd_sweep, "measure": cmd_measure, "plant": cmd_plant, "screen": cmd_screen,
     "calibrate": cmd_calibrate, "render": cmd_render, "elicit": cmd_elicit,
     "screen-llm": cmd_screen_llm, "tag": cmd_tag, "checklist": cmd_checklist}[args.cmd](args)


if __name__ == "__main__":
    main()
