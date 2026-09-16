# regulatory-complexity

Measure what a rule costs the people subject to it; simplify the rule while changing outcomes for as few of them as possible.

Collaboration: Alexander Spangher, Dan Ho (Stanford RegLab), Sanmi Koyejo.

Process-inference update (2026-09-16): [joint Bayesian agency/task/case model](docs/2026-09-16-bayesian-process-v4.md),
[evaluation protocol](docs/2026-09-16-bayesian-process-v4-protocol.md),
[experiments and limitations](docs/2026-09-16-bayesian-process-v4-results.md), and a
[simplified TikZ plate diagram with full glossary](docs/figures/latex_plate_diagram_simplified/README.md).
Typed evidence now retains step, segment and total timing; agency effects propagate
between tasks; work-hours remain separate from waiting. The
[earlier negative pilot](docs/2026-09-16-bayesian-process-v3-results.md) is preserved.
Completed v4 timing fits converge, but the reserved median misses its 90% interval
and step/agency-count inference remains unvalidated; see the experiment report.
The ongoing [v5 Bayesian measurement experiments](docs/2026-09-16-bayesian-process-v5.md)
test explicit clocks, censoring and case selection under a
[new development protocol](docs/2026-09-16-bayesian-process-v5-protocol.md). They have not
established overall superiority to the LLM or replaced the full burden hierarchy.
The [v5 results and benchmark clock audit](docs/2026-09-16-bayesian-process-v5-results.md)
also document a first-versus-last-decision mismatch in the legacy evaluation.
The [v6 joint visit-model experiments](docs/2026-09-16-bayesian-process-v6-results.md) connect
timing, repeat visits, route uncertainty and separate work-hour hierarchies in one
posterior. Controlled fitting and the source compiler are in development; the
full text-to-burden model and fresh matched-LLM comparison remain incomplete.
The same joint model now supports an explicit within-visit waiting/service split;
the [visit-clock contract](docs/2026-09-16-bayesian-visit-clocks.md) describes its assumptions
and distinguishes elapsed service from person-hours.
An independent [audit of the V3–V6 work](docs/2026-09-16-bayesian-overnight-audit.md)
verifies the numbers and samplers, lists the defects found, explains why the
comparison could not converge, records the agreed split of ambiguity between
the LLM and the model, and sets out the unification plan.
The [audit implementation record](docs/2026-09-16-bayesian-audit-implementation.md)
tracks completed repairs, the calibration-backed compiler interface, saved-draw
information diagnostics, and the still-pending unification/refactor work.

## Thesis

What people call a rule's "complexity" is three separately measurable costs, and the existing literature measures only the first — because it's the only one visible in the text:

1. **Size** — reading/structure cost. What Katz & Bommarito and Colliard & Georg count (nodes, operators, references). Measurable statically.
2. **Discretion** — prediction cost. The mass of cases whose outcome the rule does not determine, so the subject cannot know their outcome even after reading everything: it depends on which official shows up. *Invisible to text metrics* — "adequate" is one token. We measure it behaviorally: compile the rule into executable decision trees k times independently, run generated case panels through all k, and count the cases where defensible readings reach disjoint outcomes. Each such case is a **witness** — a concrete household the statute leaves undetermined. No LLM appears in the trust chain: models only *generate* compilations and cases; every measurement is made by execution.
3. **Burden** — production cost, the time tax. Every input the process demands, on a provenance ladder (known offhand → existing document → institutional request → self-made artifact → paid professional → government act), costed in hours/dollars/wait/trips, path-dependently: a case short-circuited at the first gate never pays for the inspection.

Vague law is not simpler law — its complexity is shifted off the statute book onto applicants and officials at decision time (Kaplow's rules-vs-standards, made measurable). Simplification is then a search problem: find a smaller tree whose harm-weighted disagreement with the original, on a calibrated population, is bounded — and report *who* the flipped cases are.

## Pilot: AB 2533

Cal. Gov. Code § 66311.7 (unpermitted-ADU amnesty) requires cities to legalize pre-2020 units unless substandard per Cal. HSC § 17920.3 — a provision saturated with judgment predicates ("adequate", "good and safe condition", "in the opinion of the fire chief"). Every California city must publish a § 17920.3 checklist, so hundreds of independent human compilations of the same rule exist. **Falsifiable claim: the predicates our divergence measure flags are the ones where city checklists actually differ.** Statute texts are in `corpus/ab2533/`.

## Pipeline

```
statute text ──► intake (6 questions, span-grounded)          [LLM]
             ──► compile ×k → decision trees                  [LLM, independent samples]
             ──► burden audit (every demanded input, costed)  [LLM extraction + priors]
case panels  ──► fuzz / coverage / adversarial / calibrated   [offline or LLM]
analysis     ──► size, P(discretion), expected burden,        [offline: executor.py,
                 monotonicity violations, k-way divergence     metrics.py, divergence.py]
adjudication ──► bug / schema gap / genuine underdetermination [LLM, human-audited sample]
```

## Quickstart

```bash
pip install -r requirements.txt
python3 tests/smoke.py                      # offline compile-side stack
python3 tests/test_instrument.py            # offline instrument stack
python3 pipeline/instrument.py plant        # planted-world validation ladder (no API)

# LLM stages default to the Codex CLI backend — keyless, authenticated via
# `codex login` (ChatGPT account). Alternatives: --backend glm (needs
# GLM_API_KEY; optional GLM_BASE_URL, default https://api.z.ai/api/paas/v4)
# or --backend anthropic (needs ANTHROPIC_API_KEY + `pip install anthropic`).
cd pipeline
# Compile-side pipeline (k compilations -> divergence):
python3 run.py compile --statute ../corpus/ab2533/gov-66311.7.txt ../corpus/ab2533/hsc-17920.3.txt --rule-id ab2533 -k 3
python3 run.py fuzz    --tree ../examples/ab2533/compilation_1.json -n 200 --rule-id ab2533
python3 run.py analyze --trees ../examples/ab2533 --panel ../examples/ab2533/panel_fuzz.json --rule-id ab2533

# Looseness instrument (price one word — "adequate sanitation"):
python3 instrument.py sweep   --world ../worlds/ab2533_sanitation.json -n 40
python3 instrument.py render  --world ../worlds/ab2533_sanitation.json --sweep ../examples/ab2533_sanitation/sweep.json
python3 instrument.py elicit  --world ../worlds/ab2533_sanitation.json --vignettes ../examples/ab2533_sanitation/vignettes.json --n-readers 7
python3 instrument.py measure --readings ../examples/ab2533_sanitation/readings.json --world ../worlds/ab2533_sanitation.json

# Three-layer screening at scale:
python3 instrument.py tag        --statute ../corpus/ab2533/hsc-17920.3.txt --cite "HSC 17920.3" --rule-id ab2533
python3 instrument.py screen     --spans ../examples/ab2533/discourse.json           # heuristic lexicon (offline)
python3 instrument.py screen-llm --spans ../examples/ab2533/discourse.json           # typology classification
python3 instrument.py calibrate  --pairs pairs.json                                  # screener vs instrument
```

## Layout

- Naming: docs with a half-life (plans, protocols, results, audits, inventories, status notes) carry a `YYYY-MM-DD-` prefix, the date they describe. Undated docs (`design.md`, `references.md`, the related-work reviews) are living and kept current in place.
- `docs/design.md` — full design: formal objects, positioning against prior work, validation plan.
- `corpus/ab2533/` — statute texts (verbatim from leginfo), source links, city-checklist collection point.
- `worlds/` — latent-world specs, one per judgment predicate under measurement (`ab2533_sanitation.json` is the first word priced).
- `pipeline/schemas/` — data contracts: decision tree, intake, burden audit, case panel, latent world, readings, discourse spans.
- `pipeline/prompts/` — the ten LLM task prompts; the methodological discipline lives here.
- `pipeline/run.py` — compile-side CLI (incl. `validate`, the ground-truth-free direct-reading reconstruction check); `executor.py`/`metrics.py`/`divergence.py` — the offline compile-side stack; `common.py` — shared helpers (load, statutes, fuzz panels, union schemas); `llm.py` — multi-backend LLM layer.
- `pipeline/instrument.py` — looseness-instrument CLI; `worlds.py`/`looseness.py` (sweeps, cutoff fits, ensemble bands, planted ladder, κ(L) codability profiles), `screener.py` (layer-2 static typology, calibration), `simplify.py` (reorder/prune/substitute with flip reports).
- `dashboard/` — the inspection dashboard: `template.html` (source of the published artifact) + `build.py` (injects pipeline artifacts, writes `dashboard/out/`, gitignored).

## Hygiene

Periodically refactored on request — at natural pauses: dedupe helpers into `pipeline/common.py`, promote one-off analysis scripts into real subcommands, keep dashboard source in `dashboard/` (never only in a session scratchpad), keep `tests/` green, keep this README's layout section true. Commit after each coherent milestone.

## Status / roadmap

- [x] Offline compile-side stack (identified-set executor, three-axis metrics, divergence, monotonicity checks) — smoke-tested.
- [x] Synthetic-world instrument, offline core: latent sweeps, cutoff estimation, reading-ensemble bands + band mass, planted ladder (threshold/conjunction/gestalt) with κ(L) codability profiles, identifiability curves — tested.
- [x] Three-layer scaffolding: LegalDiscourse tagging prompt, heuristic + LLM screeners, screener↔instrument calibration.
- [x] Simplification surgery: burden-optimal reordering (provably flip-free), panel-constant pruning, judgment→objective substitution priced by flip reports over identified sets.
- [x] First real run (2026-08-31, Codex backend): k=3 compilation of AB 2533 (judgment_mass 0.65–0.72 across compilers); "adequate sanitation" band [0.50, 0.73], SD 0.079, 7/7 threshold-like readers, ≈9.5% band mass under the placeholder prior. Artifacts in `examples/`.
- [ ] Cross-compilation **field crosswalk — confirmed unavoidable by the v2 run (2026-09-01)**: prompt-level vocabulary discipline made overlap *worse* (all-3 shared vocab 7% → 1%; only `construction_date` survives), because raw-observable-fact granularity multiplies naming surface. You cannot prompt your way to a shared vocabulary: either supply a fixed field lexicon to all compilers or build the post-hoc LLM crosswalk (human-audited). Also needed before cross-reading divergence is meaningful: adversarial panels, and normalized acquisition-event names.
- [x] v2 re-compile with contract prompt (2026-09-01): granularity pinned to subdivisions → predicate counts 51/66/92 (vs 10/29/20), judgment mass uniform 0.90–0.92, P(discretion) tightened to 0.23–0.28, zero conclusion-shaped fields, 100% span grounding, coverage lists populated, acquisition bundling working (76 inspection fields → 1 priced event). Note: judgment mass is granularity-sensitive (0.72→0.90 on the same statute) — only behavioral P(discretion) is comparable across granularities.
- [ ] Scrape 10–20 city § 17920.3 checklists (prompt 10 normalizes them) → cross-city divergence vs. instrument prediction; checklist-sourced readers into the ensemble.
- [ ] Calibrated case panels and population priors (ACS/assessor marginals; later RegLab permit records) — replace the placeholder beta prior before reporting band mass as a population claim.
- [ ] Looseness lexicon of recurring regulatory terms ("adequate", "reasonable", ...) — standalone artifact + drafting tool.
- [ ] Burden validation: PRA/ICR burden-hour inventory as calibration data (noisy labels — GAO-documented errors; use ordinally/differentially); fee schedules; permit timestamps.
- [ ] Simplification search (edit proposer + Pareto frontier over the three edit families).
