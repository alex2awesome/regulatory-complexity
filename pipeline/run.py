#!/usr/bin/env python3
"""Pipeline runner.

LLM stages (need ANTHROPIC_API_KEY):
  intake   — six-question structured intake of a rule
  compile  — k independent decision-tree compilations (the divergence samples)
  burden   — standalone burden audit (every input the text demands, categorized)
  cases    — LLM-generated case panel (coverage or adversarial mode)

Offline stages (no API, no LLM anywhere in the trust chain):
  fuzz     — random case panel from a compilation's input schema
  analyze  — static + behavioral metrics, monotonicity checks, k-way divergence

Examples:
  python run.py intake  --statute ../corpus/ab2533/gov-66311.7.txt ../corpus/ab2533/hsc-17920.3.txt --rule-id ab2533
  python run.py compile --statute ../corpus/ab2533/gov-66311.7.txt ../corpus/ab2533/hsc-17920.3.txt --rule-id ab2533 -k 3
  python run.py burden  --statute ../corpus/ab2533/gov-66311.7.txt ../corpus/ab2533/hsc-17920.3.txt --rule-id ab2533
  python run.py fuzz    --tree ../examples/ab2533/compilation_1.json -n 200
  python run.py analyze --trees ../examples/ab2533 --panel ../examples/ab2533/panel_fuzz.json
"""

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import llm
from llm import llm_json
from common import load, read_statutes, fuzz_panel


def cmd_intake(args):
    out = llm_json("01_intake.md", read_statutes(args.statute), "intake.schema.json", args.model,
                   extra=f"rule_id: {args.rule_id}")
    write_out(args, "intake.json", out)


def cmd_compile(args):
    text = read_statutes(args.statute)
    for i in range(args.start, args.k + 1):
        # Variant framings encourage independent decompositions without
        # changing the task. Divergence between them is the signal, not noise.
        variant = [
            "Work through the source text in document order.",
            "Start from the outcomes and work backwards to the conditions that produce them.",
            "Start from the perspective of the official processing an application, in the order they would encounter questions.",
        ][(i - 1) % 3]
        out = llm_json("02_compile.md", text, "decision_tree.schema.json", args.model,
                       extra=f"rule_id: {args.rule_id}\nDecomposition approach: {variant}\n"
                             f"Set compiler.prompt_variant to 'v{i}' and compiler.model to '{llm.model_desc()}'.")
        write_out(args, f"compilation_{i}.json", out)


def cmd_burden(args):
    out = llm_json("03_burden.md", read_statutes(args.statute), "burden_audit.schema.json", args.model,
                   extra=f"rule_id: {args.rule_id}")
    write_out(args, "burden_audit.json", out)


def cmd_cases(args):
    tree = load(args.tree)
    extra = f"Input schema of the compiled rule:\n```json\n{json.dumps(tree['input_schema'], indent=1)}\n```\nGenerate {args.n} cases."
    if args.adversarial:
        other = load(args.adversarial)
        extra += ("\nADVERSARIAL MODE: here is a second compilation of the same rule. Generate cases "
                  "likely to receive different outcomes under the two trees.\n"
                  f"```json\n{json.dumps({'nodes': other['nodes'], 'root': other['root']}, indent=1)}\n```")
    out = llm_json("04_cases.md", "", "case.schema.json", args.model, extra=extra)
    write_out(args, "panel_llm.json", out)


def cmd_fuzz(args):
    tree = load(args.tree)
    panel = fuzz_panel(tree["input_schema"]["fields"], n=args.n, seed=args.seed)
    write_out(args, "panel_fuzz.json", panel)


def cmd_validate(args):
    """Ground-truth-free reconstruction check: the compiled tree must reproduce
    what a DIRECT reading of the full statute says about each case.

    The direct reader (prompt 11) sees only statute text + case facts — never
    the tree. Agreement semantics use identified sets: if the tree is
    determinate, the direct outcome must match it; if the tree leaves the case
    open, the direct outcome must lie inside the reachable set (or itself be
    'indeterminate'). Disagreements localize compilation errors without any
    gold labels."""
    sys.path.insert(0, str(HERE))
    from executor import reachable_outcomes

    tree = load(args.tree)
    statute_text = read_statutes(args.statute)
    panel = load(args.panel)
    results = []
    for case in panel["cases"][: args.n]:
        facts = "\n".join(f"- {k.replace('_',' ')}: {v}" for k, v in sorted(case["facts"].items()))
        d = llm_json("11_direct_read.md", statute_text, None, args.model,
                     extra=f"case_id: {case['case_id']}\nCASE FACTS:\n{facts}", max_tokens=1200)
        run = reachable_outcomes(tree, case["facts"])
        reach = sorted(run.outcomes)
        direct = d.get("outcome")
        if run.determinate:
            verdict = "match" if direct == reach[0] else "MISMATCH"
        else:
            verdict = "compatible" if (direct in run.outcomes or direct == "indeterminate") else "MISMATCH"
        results.append({"case_id": case["case_id"], "direct": direct, "tree_reachable": reach,
                        "tree_determinate": run.determinate, "verdict": verdict,
                        "pivotal_text": d.get("pivotal_text", ""), "reason": d.get("reason", "")})
        print(f"{case['case_id']}: direct={direct} tree={reach} -> {verdict}")
    n = len(results)
    mismatches = [r for r in results if r["verdict"] == "MISMATCH"]
    summary = {"n_cases": n, "n_mismatch": len(mismatches),
               "faithfulness": round(1 - len(mismatches) / max(n, 1), 3),
               "results": results}
    write_out(args, f"validation_{pathlib.Path(args.tree).stem}.json", summary)
    print(f"reconstruction faithfulness: {summary['faithfulness']:.2f} ({len(mismatches)}/{n} mismatches)")


def cmd_analyze(args):
    """Per-tree metrics on each tree's OWN fuzzed panel (fair burden/discretion
    numbers — a shared panel starves trees with different vocabularies), plus
    k-way divergence on a union-schema panel (with its coherence caveat).
    Pass --panel to override both with a specific panel (e.g. calibrated/real)."""
    sys.path.insert(0, str(HERE))
    from common import union_fields
    from metrics import static_metrics, behavioral_metrics, check_monotonicity
    from divergence import divergence_report

    priors = load(HERE / "burden_priors.json")
    tree_files = sorted(pathlib.Path(args.trees).glob("compilation_*.json"))
    trees = [load(p) for p in tree_files]
    if not trees:
        sys.exit(f"no compilation_*.json in {args.trees}")
    shared = load(args.panel) if args.panel else None

    report = {"trees": {}}
    for i, (p, t) in enumerate(zip(tree_files, trees), 1):
        panel = shared or fuzz_panel(t["input_schema"]["fields"], n=args.n, seed=i)
        report["trees"][p.name] = {
            "panel": panel["panel_id"],
            "static": static_metrics(t),
            "behavioral": behavioral_metrics(t, panel, priors),
            "monotonicity_violations": check_monotonicity(t, panel),
        }
    if len(trees) > 1:
        div_panel = shared or fuzz_panel(union_fields(trees), n=args.n, seed=99, panel_id="union_fuzz")
        report["divergence"] = divergence_report(trees, div_panel)
        if not shared:
            report["divergence"]["caveat"] = (
                "union-schema fuzz: same-named fields assumed synonymous, differently-named "
                "fields drawn independently — only meaningful to the extent vocabularies align "
                "(see field-crosswalk roadmap item)")
    write_out(args, "analysis.json", report)
    for name, r in report["trees"].items():
        s, b = r["static"], r["behavioral"]
        print(f"{name}: {s['n_predicates']} predicates "
              f"(judgment_mass={s['judgment_mass']:.2f}), "
              f"P(discretion)={b['p_discretion_exposed']:.2f}, "
              f"mean burden {b['mean_burden']['hours']:.1f}h / ${b['mean_burden']['dollars']:.0f} "
              f"[panel: {r['panel']}]")
    if "divergence" in report:
        print(f"k-way divergence (union panel): P(divergent)={report['divergence']['p_divergent']:.2f} "
              f"({len(report['divergence']['divergent_witnesses'])} witnesses)")


def write_out(args, name, obj):
    out_dir = pathlib.Path(args.out_dir or (HERE.parent / "examples" / getattr(args, "rule_id", "run")))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    path.write_text(json.dumps(obj, indent=2))
    print(f"wrote {path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backend", choices=["codex", "glm", "anthropic"], default=None,
                    help="LLM backend (default: env RC_LLM_BACKEND, else codex — keyless via the Codex CLI's ChatGPT login)")
    ap.add_argument("--model", default=None, help="model override for the chosen backend")
    ap.add_argument("--out-dir", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name in ("intake", "compile", "burden"):
        p = sub.add_parser(name)
        p.add_argument("--statute", nargs="+", required=True)
        p.add_argument("--rule-id", required=True)
        if name == "compile":
            p.add_argument("-k", type=int, default=3)
            p.add_argument("--start", type=int, default=1, help="resume from this compilation index")

    p = sub.add_parser("cases")
    p.add_argument("--tree", required=True)
    p.add_argument("--adversarial", help="path to a second compilation to split against")
    p.add_argument("-n", type=int, default=30)
    p.add_argument("--rule-id", default="run")

    p = sub.add_parser("fuzz")
    p.add_argument("--tree", required=True)
    p.add_argument("-n", type=int, default=200)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--rule-id", default="run")

    p = sub.add_parser("analyze")
    p.add_argument("--trees", required=True, help="directory containing compilation_*.json")
    p.add_argument("--panel", default=None, help="optional shared panel; default = self-panel per tree + union panel for divergence")
    p.add_argument("-n", type=int, default=200)
    p.add_argument("--rule-id", default="run")

    p = sub.add_parser("validate")
    p.add_argument("--tree", required=True)
    p.add_argument("--statute", nargs="+", required=True)
    p.add_argument("--panel", required=True)
    p.add_argument("-n", type=int, default=15)
    p.add_argument("--rule-id", default="run")

    args = ap.parse_args()
    llm.set_backend(args.backend, args.model)
    {"intake": cmd_intake, "compile": cmd_compile, "burden": cmd_burden,
     "cases": cmd_cases, "fuzz": cmd_fuzz, "analyze": cmd_analyze,
     "validate": cmd_validate}[args.cmd](args)


if __name__ == "__main__":
    main()
