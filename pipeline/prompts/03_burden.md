# Burden audit — the time tax

Go through the SOURCE TEXT and record **every point where the rule's process requires an input from someone** — every document, fact, artifact, appointment, or disclosure a person or institution must produce for the process to run. Output JSON valid against the provided schema.

This is a two-part task with different epistemic status:

## Part 1 — Extraction (this is a reading task; be exhaustive)

One `demands[]` entry per distinct input. Include:
- explicit demands ("the applicant shall submit …"),
- implicit demands: any predicate the process turns on that someone must establish ("constructed before January 1, 2020" silently demands proof of construction date),
- process demands: inspections to host, appointments to attend, notices to respond to.

Every entry carries a verbatim `span`. Missing a demand is the failure mode that matters most — err toward inclusion and mark duplicates rather than omitting.

## Part 2 — Categorization and effort (these are priors, not findings)

For each demand:
- `provenance_class`: a = known offhand / self-attestation; b = document already in household records; c = must be requested from an institution; d = artifact the applicant creates (sketch, site plan, written description); e = artifact a paid professional creates (engineer letter, licensed inspection); f = a government act (inspection visit, appointment).
- `effort`: rough hours / dollars / wait_days / trips ONLY where you can articulate a basis; set `empirical_flag: true` and name in `basis` the real-world data source that would validate it (fee schedule, records-request policy, market quotes, permit timestamps, PRA/ICR burden-hour inventory).
- `sensitive: true` when supplying the input exposes the party to legal or financial risk (e.g. disclosing an unpermitted structure to the agency that could cite it). Never fold this into hours — it is counted separately.
- `learning_cost`: what the party must already understand to know this is demanded of them.
- `conditional_on`: if the demand only arises on some process paths, state the condition — path-dependent demands are the difference between the rule's worst-case and expected burden.
