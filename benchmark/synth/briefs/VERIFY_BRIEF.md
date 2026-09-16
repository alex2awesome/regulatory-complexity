# Wave-3 brief: verifying rendered artifacts against their specs

You are the leakage/faithfulness checker. For each artifact you get: the spec, the rendered text, and — unlike the renderer — the descriptions of the `must_not_reveal` elements (from `truth/`, supplied to you in `verify_context/<id>.json`).

Write `benchmark/synth/worlds/<W>/artifacts/<id>.verify.json` per DESIGN.md `verify`:
- `required_found`: for every `reveals` entry, was it stated at the right fidelity? Quote the sentence. An `exact` fee written as "about $430" is a fidelity error (record `found: true, fidelity_ok: false`).
- `leaks`: any sentence that discloses a hidden element (a staff-only step, its actor, its timing) — quote it. Also flag *invented* process facts (a fee, step, department, or timeline not licensed by the spec) under `extraneous_facts`; those are leaks of a different kind (fabrication) and must be fixed too.
- `contamination_ok`: each contamination fact present and plausibly attributed to the other process/jurisdiction.
- `style_ok`: brief judgment vs the style guide.
- `pass`: true only if all required found at correct fidelity, zero leaks, zero extraneous process facts.

Explicitly check measurement semantics, not just matching numeric strings:

- Start and end events must match `measurement_clock`. First decision, last decision
  and closeout are different; first filing is not receipt of a complete application.
- A completed decision cannot be rendered as an ongoing wait because its poster is
  labeled "delayed". A sum of visit cycles is neither one visit nor a first-to-last
  span, and is not necessarily all pre-filing preparation. Elapsed time is not labor.
- A median, p90, informal forecast and legal target must retain their meanings.
  Cohort denominators must match the timing statistic; missing observations do not
  imply a zero-day processing time.
- Actor assignments require an explicit activity/actor reveal or the supplied
  public-law relationship. A named department's existence is not permission to
  assign other steps to it.
- Persona `true_timeline`/`true_days` values are verification-only. The document
  must preserve the specified noisy report, not replace it with the hidden number.

For failures, write a one-line fix instruction in `fix` (the renderer will be re-run with it). Append a summary line per artifact to `verify_log.jsonl`. Never git commit; never edit the artifacts yourself.
