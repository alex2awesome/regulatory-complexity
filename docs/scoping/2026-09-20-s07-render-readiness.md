# W2 S07 solar counterpart: rendering readiness check

2026-09-20, 11:25 UTC. This is a filename/status-log inventory, not a review of
synthetic content, source fidelity, reserved truth or fitting readiness.

The existing S07 process world is **not an existing twelve-jurisdiction prose
pilot**. Under `benchmark/synth/worlds/W2_DEV_001`:

- There are 2,369 `Cxx__S07__*.json` specification files across 57 county
  prefixes. Another 27 S07 specification filenames have J1/J2/J3 prefixes;
  those were counted separately and their meaning was not inferred from names.
- There are 31 S07 Markdown artifacts, across only C03, C06, C09 and C12.
- All 31 have a latest verification-log verdict: 27 pass labels and four fail
  labels. These labels were not rechecked against artifact/specification hashes
  in this bounded scan and are not fresh semantic certification.

| County prefix | Specification filenames | Markdown artifacts | Latest passing verdicts |
|---|---:|---:|---:|
| C03 | 7 | 7 | 7 |
| C06 | 7 | 7 | 5 |
| C09 | 8 | 8 | 8 |
| C12 | 14 | 9 | 7 |

The four latest failed labels are `C06__S07__form`,
`C06__S07__staff_report`, `C12__S07__news`, and `C12__S07__reddit_2`.
Only C03 and C09 have a passing label for every current specification filename;
that is not a claim that either has completed independent verification for this
study. C12 also lacks five artifacts relative to its unthinned specifications.

## Consequence for the approved pilot

The [three-family plan](../2026-09-20-three-statute-parse-verify-analysis-plan.md)
still requires a metadata-selected, partition-respecting twelve-jurisdiction
S07 pilot and a frozen artifact quota. Do not silently select only the passing
counties, call the 57 private process implementations a public corpus, or expand
this experiment to all 2,369 county specifications. Existing artifacts may be
reused only after current binding/fidelity checks. Missing SolarTRACE-style
published observations require an explicitly versioned observation layer;
private phase timings are not already-public evidence.

The hourly W2 status command currently describes a **245-document S03 lane**.
Its `observed.complete_by_counts=true` does not establish S07 or whole-world
completion. Selection must be checked along with the trusted count key.

## Reproduction boundary

Use `Path.glob('C[0-9][0-9]__S07__*.json')` on `specs/` and
`Path.glob('*__S07__*.md')` on `artifacts/`; group by the first `__` component.
Read only `artifact_id` and `pass` from successive `verify_log.jsonl` records,
retaining the last record per artifact. Match verdicts to existing artifact
stems; absence is not a passing verdict. The scan did not decode specification
contents, process/case truth, summaries, ceilings or scores, and did not alter
render selection or launch rendering.
