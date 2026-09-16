# Reconstruct an implemented process by searching a mock web

You are an agent with a search engine over a closed mock web (municipal pages, forms, fee
schedules, ordinances, staff reports, news, and reddit threads). Your job: build the process
model of the TARGET program in the TARGET jurisdiction — actors, activities, order, rework, fees,
timing — and then stop.

**Each turn you emit exactly one JSON object**, one of:

```json
{"op": "search",        "args": {"query": "…", "k": 8}}
{"op": "fetch",         "args": {"url": "https://…"}}
{"op": "reddit_search", "args": {"query": "…", "sub": "r/Somewhere"}}
{"op": "reddit_thread", "args": {"thread_id": "t_xxxxx"}}
{"op": "finish",        "args": {}, "model": { …the process model… }}
```

`sub` is optional. Never invent a url: fetch only urls that appeared in a search result or as an
outgoing link on a page you fetched. Unknown urls return 404. The observation from each call is
appended to the transcript below; some conditions hide whole classes of document (reddit, staff
reports), and a 404 or an empty result set is information, not a bug — record it in `unknowns`.

Search strategy that works here:

- Start with the program's own words plus the jurisdiction name; then re-query with the terms the
  first page used (its local name for the program, the code chapter, the form number).
- **Follow one hop of links** from the program page: the fee schedule, the application form, the
  FAQ, the adopting ordinance. The fee amounts and the real checklist are usually there, not on
  the program page.
- The **form** reveals steps no page lists (a required pre-application block, a department-use
  block naming who signs off, what happens on a failed inspection).
- A **staff report / audit / SOP**, where one is reachable, is the only source for back-office
  steps (internal routing, second-level sign-off, fee reconciliation) and for real medians. Search
  for the council item, the fee amendment, the program update.
- **Reddit for timing and for practice**: applicants post dated step-by-step timelines and
  occasionally a counter employee explains an invisible step. Search reddit separately.

Skepticism you are graded on:

- **Contamination.** The same statute is implemented differently by every city, and the same city
  runs many programs. A page or comment about another jurisdiction (a county, a neighbouring city)
  or another program (vending, variances) must not enter the model, however similar it looks.
  Check the jurisdiction and the program on every document before using it.
- **Staleness.** Pages outlive the process they describe. Compare dates; prefer the later document
  and the ordinance/fee schedule; treat an older fee, department, or step count as the *previous*
  version and say so in `unknowns`.
- **Selection bias.** Reddit oversamples the delayed and the denied. A thread's elapsed time is an
  upper tail; estimate the median below it and say so in `basis`.
- **Do not invent steps.** If nothing supports a step, it goes in `unknowns`, not in `activities`.

When you finish, `model` must be a JSON object valid against the process-model schema:
`model_id`, `source: "declared"`, `jurisdiction`, `actors` (lane strings), `activities`, `edges`,
`terminal_artifact`. Each activity: `id`, `name`, `actor`, `occasion`, `artifacts_in`,
`artifacts_out`, `optional`, `visibility` (`applicant_facing|applicant_inferable|staff_only`),
`timing` `{"median_days", "range": [lo,hi], "basis"}`, `fee` `{"amount","when"}` or null,
`rework` `{"p_trigger","back_to","reason"}` or null, `confidence` (0–1), `evidence` (urls or
thread ids you actually read). Edges include `rework` loops. Also top level: `process_timing`
`{"median_days","p90_days","range","basis"}`, optional `denial_rate`, and `unknowns`:
`[{"what": "…", "why_unknown": "…"}]`.
