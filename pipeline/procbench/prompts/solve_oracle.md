# Reconstruct an implemented process from its full public footprint

The SOURCE TEXT is a set of `=== DOCUMENT n ===` blocks: everything public that bears on ONE
program in ONE jurisdiction, plus, in some conditions, documents about **other** jurisdictions
and **other** programs. Produce the process model of the TARGET program as it is *actually
implemented* — actors, activities, order, rework, fees, timing — as one JSON object valid
against the schema.

Conventions (same as the statute compiler, `14_process_compile.md`, extended for timing/fees):

- `source`: `"declared"`. `model_id`: the task id. `jurisdiction`: the target jurisdiction's name.
- `actors`: lane strings. Use the document's own department names (e.g. `building_division`,
  `permit_center`, `plans_examiner`, `inspector`, `applicant`, `third_party`, `finance`, `council`).
- One `activity` per distinct act. Each gets:
  - `id` (A01, A02, …), `name` (prefer the jurisdiction's own term), `actor`, `occasion`
    (`counter|online|site_visit|internal|mail|hearing`), `artifacts_in`, `artifacts_out`,
    `optional` (true only where a document says "may" / offers rather than requires).
  - `visibility`: `applicant_facing` (the applicant does it or receives an artifact),
    `applicant_inferable` (the applicant sees only a status change or a delay),
    `staff_only` (invisible without staff/council documents).
  - `timing`: `{"median_days": <number|null>, "range": [lo, hi]|null, "basis": "<where it came from>"}`.
  - `fee`: `{"amount": <number>, "when": "<at submittal|before inspection|…>"}` or `null`.
  - `rework`: `{"p_trigger": <0-1|null>, "back_to": "<activity id>", "reason": "…"}` or `null`.
  - `confidence`: 0–1, your probability that this activity exists in the real process with this
    actor and this position.
  - `evidence`: the urls (or `thread_id`s) of the documents that support it. Never cite a
    document you were not given.
- `edges`: `sequence`, `handoff` (an artifact crosses lanes), `optional`, and `rework` (a
  correction loop back to an earlier activity — include these, they are commonly missed).
- `terminal_artifact`: what the applicant ends up holding.
- Top level, also emit: `process_timing`
  `{"median_days": n, "p90_days": n|null, "range": [lo, hi], "basis": "…"}` for end-to-end
  elapsed time from application to terminal artifact, `denial_rate` if supported, and
  `unknowns`: a list of `{"what": "…", "why_unknown": "no public document states it |
  sources conflict | only a stale source states it"}` — everything you could not determine.

Discipline:

- **Do not invent steps.** A back-office step goes in only if a document supports it (a staff
  report, an SOP, a form's department-use block, an insider comment). Otherwise it belongs in
  `unknowns`, not in `activities`.
- **Disentangle.** Documents about another jurisdiction or another program are contamination,
  including when a user post compares them ("in the county it took four months"). Use them for
  nothing. Check every document's jurisdiction and statute before you use a fact from it.
- **Date everything.** Where two documents conflict, prefer the later-dated one and the
  ordinance/fee schedule over a web page, and record the conflict in `unknowns` or in the
  activity's `notes`. An undated or old page may describe a superseded version (a different fee,
  a different department, a step that no longer exists).
- **De-bias user reports.** People post when they are delayed or denied; a thread's reported
  elapsed time is an upper tail, not a median. Say so in `basis` and adjust downward rather than
  reporting the worst case as typical.
- Set `confidence` low where you are inferring rather than reading, and prefer a short honest
  model plus a long `unknowns` list to a long speculative one.
