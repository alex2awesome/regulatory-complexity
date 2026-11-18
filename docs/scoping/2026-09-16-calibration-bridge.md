# The calibration bridge, and how much world it needs

2026-09-16. Stage 4 of [the plan](../2026-09-16-county-scale-up-plan.md), opened.
Builder: `pipeline/procbench/build_semantic_labels.py`. Fitter, pre-existing:
`pipeline/procbench/semantic_calibration.py`.

## The blocker this removes

The audit named calibrating interpretation error as the highest-value missing
piece, and `semantic_calibration.fit_calibration` was already written to do it.
It refuses any row whose `link_status` is not `verified`, which is the right
refusal: a guessed crosswalk between a rendered sentence and the fact behind it
would fabricate the very confusion matrix it is meant to measure. That refusal
is why the W1 attempt (`prepare_semantic_labels.py`) stopped at **zero verified
labels** — a document-level render log cannot say which sentence carries which
claim.

A world built with `decision_model_version` 2 does not have that problem.
Every `criterion` reveal in an artifact spec names the predicate it discloses,
the fidelity it must be written at, and the literal value the renderer must
state; the truth carries that predicate's actual reading. **The link is verified
by construction**, because the generator planted the sentence in order to
disclose that specific reading. No inference is required, so the label set can be
emitted directly.

Four ambiguity classes come out, matching the plan's §4 table: `reading_value`
(which threshold this jurisdiction applies — the discretion residual),
`criterion_kind`, `fixability`, and `evaluating_step`. Groups are
(program, artifact) pairs, because every claim in one document shares its author
and its errors. The split is **by programme**, not by artifact, since two
artifacts about one process disclose the same readings and splitting artifacts
would leak the answer across the boundary.

## It works end to end

On the tiny three-statute world: 196 rows over 6 programmes, 49 per class, 2
programmes held out. The fitter accepts the set and returns per-class routing
decisions with group-bootstrap intervals:

| ambiguity class | labels | fit | validation | groups | top accuracy | 90% interval | routing |
|---|---:|---:|---:|---:|---:|---|---|
| `criterion_kind` | 3 | 35 | 14 | 9 | 0.929 | [0.81, 1.00] | **top_reading** |
| `reading_value` | 12 | 35 | 14 | 9 | 0.857 | [0.69, 1.00] | mixture_candidate |
| `fixability` | 2 | 35 | 14 | 9 | 0.786 | [0.60, 0.93] | mixture_candidate |
| `evaluating_step` | 6 | 35 | 14 | 9 | 0.786 | [0.57, 0.94] | mixture_candidate |

That is the §4 decision rule executing for the first time: measure the top
reading's accuracy per class, keep the accurate classes upstream, hold a
calibrated mixture for the rest.

**These numbers are from a simulated extractor, not a real one.** The builder's
`--extractor simulated` exists to exercise the fitter against a *known* error
rate and stamps the output `SIMULATED-NOT-A-REAL-EXTRACTOR` so it can never be
mistaken for a measurement. The real version needs one extraction run over the
rendered artifacts to fill `top_label`; the ground-truth half is already
complete.

Aggregate recovery is good: the simulator realised 0.898 accuracy and the fitter
measured 0.786 to 0.929 per class, with every planted value inside the interval.

## The finding: a small world cannot calibrate a high-cardinality class

My first recovery check compared the fitted confusion diagonal against the
planted per-stratum accuracy and appeared to fail badly — 0.26 to 0.34 fitted
against 0.85 to 0.97 planted. That is **not a fitter bug and not a simulator
bug**. It is Dirichlet smoothing doing its job on almost no data.

`reading_value` has 12 labels and 4 fidelity strata, so 48 possible cells, and
35 fit rows. **18 cells have any data at all, and they hold one to three rows
each.** With a pseudocount of 0.5 and a 12-label space, a cell with one
unanimous observation can express at most:

| unanimous rows in a cell | maximum P(true = reported) |
|---:|---:|
| 1 | 0.214 |
| 2 | 0.312 |
| 5 | 0.500 |
| 20 | 0.788 |
| 100 | 0.948 |

So the conservative diagonal is the correct answer to "what do you know from one
observation?", and my check was wrong to average sparse cells as though they
were estimates. Aggregate accuracy, which pools across cells, recovered fine.

**The requirement this implies.** To reach a 0.80 diagonal in a 12-label class
needs about **22 unanimous rows per cell**, hence roughly **264 rows per
stratum** and **about 1,056 rows per class** across four fidelity strata. The
tiny world yields 49. So calibrating the reading class needs on the order of
**20× the label volume** the current world produces.

This is a concrete sizing requirement for W2, derived rather than guessed, and
it is met comfortably by the planned scale: 58 counties implementing 4 to 6
statutes, each with several disclosing artifacts and about three predicates,
produces thousands of criterion reveals. It also argues for keeping the
**fidelity strata coarse** — pooling `vague` with `wrong` would halve the cell
count — and for **not** expanding the reading space beyond the three or four
options per predicate the generator currently plants, since cost grows with the
square of the label count.

## What remains before Stage 4 closes

1. **One real extraction run** over the rendered artifacts of a calibration
   partition, to fill `top_label`. Nothing else blocks it.
2. **A world large enough**, per the sizing above. This is now a stated
   dependency of W2 rather than a discovery to be made later.
3. **Wire the fitted weights into the compiler.** `calibrated_weights` and
   `operator_weights` already exist for this; the compiler consumes a
   calibration artifact rather than raw truth or an LLM's self-reported
   confidence.
