#!/usr/bin/env python3
"""Stage 1 validation: run SARA entailment cases through our compiled trees.

SARA gives real ground truth: each case has narrative facts, a question
("Section 7703(a)(1) applies to Alice for 2018."), and a gold answer
(Entailment / Contradiction). Pipeline per case:

  1. LLM extracts facts from the narrative into the tree's input schema
     (prompt 12; closed-world). The LLM never sees the statute or the answer.
  2. The tree executes offline (identified-set executor).
  3. Prediction: outcomes wholly in {approve, conditional_approve} -> Entailment;
     wholly in {deny, not_applicable, refer} -> Contradiction; mixed -> abstain.

Numeric cases (dollar answers) are skipped in this pilot — our trees decide,
they don't yet compute amounts (score nodes are the path to that).

Usage:
  python3 sara_eval.py --section 7703 --tree ../examples/sara/section7703/compilation_1.json -n 10
"""

import argparse
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import llm
from llm import llm_json
from common import load
from executor import reachable_outcomes, eval_expr, Indeterminate


def target_cite(question):
    """'Section 68(b)(1)(A) applies to Alice' -> ('68', '(b)(1)(a)'); bare
    section cites return subs='' (handled by whole-tree mode)."""
    m = re.search(r"[Ss]ection\s+(\d+)((?:\([0-9A-Za-z]+\))*)\s+applies", question)
    return (m.group(1), m.group(2).lower()) if m else None


def nodes_for_cite(tree, sec, subs):
    out = []
    for n in tree["nodes"]:
        if "predicate" not in n:
            continue
        cite = (n.get("span", {}).get("cite", "") or "").lower().replace(" ", "")
        if re.search(rf"(?<!\d){sec}(?!\d)", cite) and subs and subs in cite:
            out.append(n)
    return out


def subsection_verdict(nodes, facts):
    """Evaluate the queried subsection's own predicates. Returns
    (pred, detail): all objective-true -> Entailment; any false ->
    Contradiction; judgment-typed or missing input -> abstain."""
    judgment_typed, verdicts = [], []
    for n in nodes:
        p = n["predicate"]
        if p["type"] != "objective":
            judgment_typed.append(n["id"])
            continue
        try:
            verdicts.append(bool(eval_expr(p["expr"], facts)))
        except Indeterminate as e:
            return "abstain", {"why": "missing_input", "field": str(e)}
    if judgment_typed:
        return "abstain", {"why": "judgment_typed", "nodes": judgment_typed}
    if not verdicts:
        return "abstain", {"why": "no_matching_nodes"}
    return ("Entailment" if all(verdicts) else "Contradiction"), {"why": "subsection_eval"}

SARA = HERE.parent / "corpus" / "tax" / "sara" / "dataset" / "sara"

ENTAIL_SET = {"approve", "conditional_approve"}
CONTRA_SET = {"deny", "not_applicable", "refer"}


def parse_case(path):
    txt = path.read_text()
    def block(name):
        m = re.search(rf"% {name}\n((?:%.*\n)+)", txt)
        return " ".join(l.lstrip("% ").rstrip() for l in m.group(1).splitlines()) if m else ""
    text, question = block("Text"), block("Question")
    m = re.search(r"\b(Entailment|Contradiction)\s*$", question)
    gold = m.group(1) if m else None            # numeric cases have "$..." answers -> gold None
    return {"case_id": path.stem, "text": text,
            "question": question[: m.start()].strip() if m else question, "gold": gold}


def cases_for_section(section):
    out = []
    for p in sorted((SARA / "cases").glob(f"s{section}_*.pl")):
        c = parse_case(p)
        if c["gold"]:
            out.append(c)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--section", required=True, help="e.g. 7703")
    ap.add_argument("--tree", required=True)
    ap.add_argument("-n", type=int, default=None)
    ap.add_argument("--backend", default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    llm.set_backend(args.backend, args.model)

    tree = load(args.tree)
    schema_desc = json.dumps(tree["input_schema"], indent=1)
    cases = cases_for_section(args.section)[: args.n]
    if not cases:
        sys.exit(f"no binary cases found for section {args.section}")

    results = []
    for c in cases:
        extra = (f"case_id: {c['case_id']}\n"
                 f"Input schema:\n```json\n{schema_desc}\n```\n"
                 f"Question context (person/year to resolve for): {c['question']}\n"
                 f"CASE NARRATIVE:\n{c['text']}")
        try:
            ext = llm_json("12_case_facts.md", "", None, extra=extra, max_tokens=4000)
            facts = ext.get("facts", {})
        except Exception as e:
            results.append({**c, "pred": "error", "detail": str(e)[:200]})
            print(f"{c['case_id']}: extraction error")
            continue
        # subsection-targeted mode when the question names a subsection whose
        # nodes we can find; whole-tree identified-set mode otherwise
        tc = target_cite(c["question"])
        mode, detail = "whole_tree", {}
        pred = None
        if tc and tc[1]:
            nodes = nodes_for_cite(tree, *tc)
            if nodes:
                pred, detail = subsection_verdict(nodes, facts)
                mode = "subsection"
        run = reachable_outcomes(tree, facts)
        outs = run.outcomes
        if pred is None:
            if outs and outs <= ENTAIL_SET:
                pred = "Entailment"
            elif outs and outs <= CONTRA_SET:
                pred = "Contradiction"
            else:
                pred = "abstain"
        ok = pred == c["gold"]
        results.append({"case_id": c["case_id"], "gold": c["gold"], "pred": pred,
                        "mode": mode, "detail": detail, "facts": facts,
                        "outcomes": sorted(outs), "correct": ok,
                        "pivotal": sorted(run.pivotal_judgment),
                        "missing": sorted(run.missing_inputs)})
        print(f"{c['case_id']}: gold={c['gold']} pred={pred} [{mode}{',' + detail.get('why','') if detail else ''}] {'OK' if ok else 'X'}")

    scored = [r for r in results if r.get("pred") in ("Entailment", "Contradiction")]
    correct = sum(1 for r in scored if r.get("correct"))
    summary = {
        "section": args.section, "tree": args.tree,
        "n_cases": len(results),
        "n_answered": len(scored),
        "n_abstain": sum(1 for r in results if r.get("pred") == "abstain"),
        "n_error": sum(1 for r in results if r.get("pred") == "error"),
        "accuracy_on_answered": round(correct / len(scored), 3) if scored else None,
        "results": results,
    }
    out = pathlib.Path(args.out or (HERE.parent / "examples" / "sara" / f"eval_s{args.section}.json"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2))
    print(f"\nsection {args.section}: {correct}/{len(scored)} correct on answered "
          f"({summary['n_abstain']} abstain, {summary['n_error']} errors) -> {out}")


if __name__ == "__main__":
    main()
