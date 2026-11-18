# Synthetic process ecosystem — design (v1, 2026-09-15)

Purpose: a benchmark where the *full* process model is known by construction, the public information about it is generated **backwards** from that truth through an explicit **visibility model**, and every artifact carries provenance saying exactly which truth elements it reveals, at what fidelity, and why it exists. Then the information ceiling is computable, and an agent's error decomposes into availability / retrieval / reconciliation / disentanglement (docs/2026-09-15-process-benchmarks-plan.md §1).

Generated backwards, in this order:
1. **Statutes** (state level) — each authorizes a process and mandates a skeleton, leaving named choices open.
2. **Local rules** — each jurisdiction adopts an ordinance/resolution filling the open choices (fees, department, extra steps, stricter standards, timelines).
3. **Full designed process** — the operational graph including back-office activities nobody publishes (internal routing, second sign-off, referral to code enforcement, fee reconciliation, records archiving), with timing distributions, fees, rework triggers, and *local names* for activities.
4. **Simulated event log** — N synthetic applicants run through the process (Monte Carlo over the graph) → per-activity timestamps, outcomes, rework rounds. This is the observed-tier truth.
5. **Artifact specs** — the visibility model decides which artifacts exist for each (jurisdiction, process) and what each reveals; user posts are drawn from *actual simulated applicants* through a complaint-selection function (delayed/denied applicants post more).
6. **Rendered artifacts** — LLM agents render each spec to prose (web page, PDF-like form text, FAQ, ordinance text, staff report, subreddit thread, news article, employee SOP when published), then a verifier checks the artifact reveals exactly the spec (no leakage of hidden elements, required facts present).
7. **Mock web** — URLs, link graph, subreddits, a search index; distractors are other processes in the same jurisdictions, the same process in other jurisdictions, and a neighboring state's look-alike processes.
8. **Ceiling + tasks** — per task, the set of truth elements recoverable from public artifacts at each fidelity; timing ceiling from the sampled posts.

Everything above is logged to `worlds/<world>/provenance.jsonl` (one line per generated object: what, from what inputs, seed, why).

## Directory layout

```
benchmark/synth/
  DESIGN.md                      # this file
  schemas/                       # JSON schemas for the objects below
  generator/                     # Python package: world → truth → log → specs → ceiling (no LLM calls)
  style/                         # style guides for rendering, distilled from corpus/realworld exemplars
  worlds/<world_id>/
    world.json                   # parameters: seed, hardness knobs, jurisdictions, statutes list
    truth/statutes/<stat>.json
    truth/local_rules/<jur>__<stat>.json
    truth/processes/<jur>__<stat>.json      # full designed process (schema: process_truth)
    truth/log/<jur>__<stat>.jsonl           # simulated applicants
    specs/<artifact_id>.json                # artifact specs (schema: artifact_spec)
    artifacts/<artifact_id>.md              # rendered text (front-matter header with url/kind/date)
    artifacts/<artifact_id>.verify.json     # verifier output: required facts found, leakage found
    web/pages.jsonl  web/reddit.jsonl  web/links.jsonl   # mock web (built from artifacts)
    ceiling.json                            # per task
    tasks.json
    provenance.jsonl
```

## Hardness knobs (`world.json.knobs`)

| knob | meaning | v1 default |
|---|---|---|
| `p_publish_program_page` | jurisdiction has a dedicated program page (else only a generic permits page mentions it) | 0.7 |
| `p_publish_form` / `p_publish_faq` / `p_publish_fee_schedule` | | 0.8 / 0.4 / 0.9 |
| `p_publish_staff_report` | designed-tier doc exists in the council record | 0.35 |
| `p_publish_sop` | employee procedure leaks/is published (audit, records request) | 0.1 |
| `p_third_party_guide` | a law firm / consultant / installer / expediter publishes an explainer (often the most complete *public* description; may be stale or wrong on fees) | 0.4 |
| `p_bill_analysis` | legislative committee analysis of the statute exists (state-level designed tier: intended process, cost estimates) | 0.8 |
| `p_official_stats` | agency publishes aggregate volumes/timing (dashboard, annual report) | 0.3 |
| `p_reveal_backoffice_in_comments` | a "I work at the counter" comment reveals a staff-only step | 0.15 per thread |
| `p_stale` | an artifact describes the *previous* version of the process (fee, step, department renamed) | 0.25 |
| `p_wrong_fact_user` | a user post states a wrong fee/timeline | 0.3 |
| `complaint_selection` | P(post | outcome): denied 0.5, delayed(>p75) 0.35, normal 0.08 | |
| `distractor_ratio` | non-target artifacts per target artifact in the search index | 4.0 |
| `naming_drift` | probability an activity gets a jurisdiction-specific name | 0.6 |
| `neighbor_state` | include look-alike processes from a second state | true |
| `n_applicants` | simulated log size per process | 200 |

## Schemas (normative; JSON files in `schemas/`)

### `statute_truth`
```
{ "stat_id": "S03", "state": "Marisol", "cite": "Marisol Gov. Code § 41210", "title": "...",
  "domain": "unpermitted_unit_amnesty | str_registration | sidewalk_vending | tree_removal | home_business | mobile_food | solar_auto_permit | rental_inspection | backyard_hens | special_event | well_permit | contractor_registration",
  "text": "<rendered later; generator emits section outline>",
  "sections": [{"sec": "(a)", "kind": "purpose|definition|mandate|option|timeline|fee|appeal|preemption|record", "content_spec": "...", "mandated_element": "E1" | null}],
  "skeleton": [ {"element_id": "E1", "kind": "application|notice|checklist_publication|inspection|third_party_option|decision|fee|fee_waiver|appeal|timeline|record|correction|public_hearing|referral", "name": "...", "optional": false, "shot_clock_days": 30|null, "actor_role": "applicant|agency|third_party|public", "must_precede": ["E3"], "text_anchor": "(c)(2)"} ],
  "open_choices": [ {"choice_id": "C1", "what": "fee amount", "constraint": "shall not exceed actual cost"}, {"choice_id":"C2","what":"which department administers"}, ... ],
  "version": 1 }
```

### `statute_truth.decision_function` — predicate kinds

`decision.py` plants five kinds, and the fifth exists because of a real statute.

| kind | the statute | what jurisdictions do | reading space |
|---|---|---|---|
| `crisp` | fixes the test exactly | apply it, or mis-implement it with `p_misimplement` | one reading |
| `standard` | uses a standard word, states no number | draw from a lenient-to-strict space | wide, unbounded |
| `delegated` | expressly leaves it to the local agency | follow the ordinance choice already adopted | the `open_choices` options |
| `local` | silent; a `stricter_standards` entry adds it | the county invented it | one reading, ids `Q*` |
| **`capped`** | **bounds it but does not fix it** | **pile onto the bound** | **the bound plus lawful lesser values** |

A `capped` dimension carries `bound`, and the world validator rejects any
reading beyond it. Welf. & Inst. Code §17001.5 is the model: a residency
requirement "shall not exceed 15 days", and five verified California counties
chose exactly 15 while nine of eleven employable time limits sit at exactly the
permitted three months. The statute's bound is public by construction, so the
statute text discloses it; which value the county chose underneath is a local
fact and is disclosed only at `approximate` fidelity at statute level.

**Why the kind earns its place.** It gives the benchmark a within-statute
control. Capped and uncapped dimensions are administered by the same counties,
on the same day, under the same document, so every county-level confounder
(wealth, politics, staffing, urbanity, caseload, vendor) is held fixed and the
only difference is whether the Legislature wrote a number down. The scored
quantity is therefore the **gap** between uncapped and capped spread, reported
by `decision_metrics.cross()` as `capped_vs_uncapped`. A model that predicts one
reading everywhere collapses both families and scores a zero gap against a
positive planted gap, so the degenerate strategy earns nothing — which plain
dispersion or entropy recovery cannot guarantee. See
`docs/2026-09-16-county-scale-up-plan.md` §12.

### `local_rule_truth`
```
{ "jur": "J2", "stat_id": "S03", "instrument": "ordinance|resolution|admin_policy", "cite": "Ordinance No. 24-118", "adopted": "2025-03-11",
  "choices": {"C1": "$430", "C2": "Building Division", ...},
  "added_elements": [ {"element_id": "L1", "kind": "pre_application_meeting", "name": "...", "mandatory": true} ],
  "stricter_standards": ["..."], "text_spec": "outline for rendering", "version": 1,
  "prior_version": {"adopted": "2023-06-02", "choices": {...}} | null }
```

### `process_truth` — extends `pipeline/schemas/process_model.schema.json`
```
{ "model_id": "J2__S03", "source": "designed", "jurisdiction": "City of Halvern", "stat_id": "S03", "version": 2, "version_date": "2025-04-01",
  "actors": [{"id":"applicant","name":"Applicant"},{"id":"permit_center","name":"Permit Services Counter","dept":"Building Division"}, ...],
  "activities": [ { "id": "A04", "name": "Intake completeness check", "local_name": "Application screening", "actor": "permit_center",
      "visibility": "applicant_facing | applicant_inferable | staff_only",
      "element_ref": "E2" | "L1" | null,           # which statute/local element it implements (null = pure back-office)
      "occasion": "counter|online|site_visit|internal|mail|hearing",
      "artifacts_in": [], "artifacts_out": ["completeness letter"],
      "timing": {"dist": "lognormal", "median_days": 4, "p90_days": 12},
      "fee": {"amount": 430, "when": "at submittal"} | null,
      "rework": {"p_trigger": 0.3, "back_to": "A03", "reason": "incomplete application"} | null,
      "optional": false, "notes": "" } ],
  "edges": [{"from":"A03","to":"A04","type":"sequence|handoff|rework|optional","condition":""}],
  "terminal_artifact": "Certificate of Compliance", "denial_rate": 0.08,
  "prior_version": { "changes": ["fee was $390", "no pre-application meeting", "Planning ran intake"] } | null }
```
`visibility` is the key field: `applicant_facing` (the applicant does it or receives an artifact), `applicant_inferable` (applicant sees a status change or a delay), `staff_only` (invisible without staff documents).

### `artifact_spec`
```
{ "artifact_id": "J2__S03__program_page", "kind": "program_page|generic_permits_page|form|checklist|faq|fee_schedule|ordinance|fee_resolution|staff_report|sop|audit_excerpt|news|reddit_thread|forum_thread|council_minutes|third_party_guide|bill_analysis|official_stats",
  "world": "W1", "jur": "J2", "stat_id": "S03" | null, "target": true|false,      # false = distractor
  "url": "https://www.halvern.gov/building/unit-legalization", "links_to": ["<artifact_id>", ...], "publisher": "City of Halvern", "audience": "applicant|staff|council|public",
  "date": "2025-02-10", "describes_version": 1|2, "stale": true|false,
  "reveals": [ {"ref": "A04", "field": "exists|actor|order|timing|fee|artifact|rework", "fidelity": "exact|approximate|vague|wrong", "value": "<the fact to state>", "must_quote": false} ],
  "must_not_reveal": ["A09","A11"],                 # staff-only ids that must stay hidden in this artifact
  "contamination": [{"about": "J3__S03" | "J2__S07", "value": "..."}],   # facts about OTHER processes deliberately mixed in
  "style": {"register": "municipal_web|legal|bureaucratic_memo|reddit_casual|news", "length_words": [200, 500], "template_lineage": "J1" | null},
  "persona": {"applicant_id": "J2__S03#117", "outcome": "delayed", "true_timeline": {...}, "reported_timeline": {...}, "why_posting": "waited 61 days, no update"} | null,
  "thread": [ {"role": "op|comment", "author": "u_xxx", "reveals": [...], "contamination": [...], "wrong": [...], "is_staff_insider": false} ] | null,
  "why": "visibility model: p_publish_program_page=0.7 drew 0.41; stale because version bump 2025-04-01 after page date" }
```

### `artifact` (rendered)
`artifacts/<artifact_id>.md` — YAML-ish front matter (`url`, `kind`, `title`, `date`, `jur`, `subreddit` if any) then the text. Reddit threads: OP then comments as `--- comment by u_xxx (score N, date) ---` blocks.

### `verify`
```
{ "artifact_id": "...", "required_found": [{"ref":"A04","field":"fee","found":true,"quote":"..."}], "leaks": [{"ref":"A09","quote":"..."}], "extraneous_facts": ["..."], "pass": true }
```

### `ceiling.json`
Per task: `{ "task_id": "...", "elements_total": 14, "recoverable_exact": [...], "recoverable_approx": [...], "only_wrong": [...], "hidden": [...], "timing_ceiling": {"true_median_days": 47, "best_estimate_from_posts": 58, "n_posts_with_timing": 6}, "distractor_count": 31 }`

### `tasks.json`
`[{ "task_id": "W1__J2__S03", "world":"W1", "jur":"J2", "stat_id":"S03", "prompt": "Construct the process model and expected timeline for <program name> in <jurisdiction>, under <cite>.", "conditions": ["search", "oracle_docs", "oracle_no_distractors", "declared_only", "declared_plus_users"] }]`

## Mock web API (`pipeline/procbench/web.py`)

Built from `artifacts/` + `specs/`. CLI (so any agent — a Codex loop, a Claude subagent — can be the solver):
```
python3 web.py --world W1 search "unit legalization Halvern"        # BM25 over pages+reddit → url, title, snippet
python3 web.py --world W1 fetch https://www.halvern.gov/building/unit-legalization   # text + outgoing links
python3 web.py --world W1 reddit search "Halvern unpermitted unit" [--sub r/Halvern]
python3 web.py --world W1 reddit thread <id>
```
Every call is appended to `runs/<run_id>/trace.jsonl` (condition, query, results) so retrieval can be scored separately.

## Scoring (`pipeline/procbench/score.py`)

Input: predicted process model (our schema + optional `timing`, `confidence`, `evidence`), gold `process_truth`, `ceiling`. Steps: (1) align predicted activities to gold via k-vote LLM matching with deterministic fallback (token overlap); (2) metrics: activity P/R/F1 (all gold; applicant-visible gold; ceiling-recoverable gold), actor accuracy on matched, order agreement (pairwise precedence over matched pairs), rework recall, fee error, timing log-ratio error, hallucination rate (predicted activities matching nothing, incl. matches to *distractor* processes = disentanglement failures), staleness (predicted facts matching the prior version). (3) Report both absolute and ceiling-relative numbers.

## Rendering discipline (Wave 2)

Renderers receive only the spec (not the truth file), a style guide distilled from real exemplars in `corpus/realworld/`, and hard rules: state every `reveals` fact at the stated fidelity; never mention `must_not_reveal` ids' content; include the `contamination` facts as if natural; reddit posts must read like the real ones (typos, digressions, wrong guesses, timelines in comments). Verifier (Wave 3) receives spec + artifact + the hidden element descriptions and produces `verify.json`; failed artifacts are re-rendered.

## Wave-2/3 finding: statutory mandates cannot be hidden (2026-09-15, corrected)

The target render+verify pass (263 artifacts, 241 passing first time, 18 repaired, 4 hand-fixed) put every
failure in one place: **documents that restate public law**. Ordinances, fee resolutions, staff reports, bill
analyses and news accounted for all 4 residual failures (fail rate 0.05 for official/legal kinds vs 0.00 for
the 177 pages, forms, FAQs, guides and threads). The mechanism is the world's own logic, not sloppy writing:
if a statute mandates a verification, a registry or a record-retention duty, then any document restating the
statute necessarily discloses that step — and the implementing activity was labelled `staff_only`.

**16 of the 26 target processes' staff-only activities implement a mandated element** (26 of 184 across all 38
processes: every "Maintain the public … registry", "Verify the applicant's record against the state registry",
"File the required report with the state agency"). All 26 trace to statute elements; none to admin-policy-only
local additions.

What was actually broken, and what was not:

1. **The defect was in the specs, not the ceiling.** 34 specs forbade *legal* documents from restating their
   own statutory mandates (`must_not_reveal` included the mandated step for 12 fee resolutions, 10 ordinances,
   7 sets of council minutes, 5 staff reports). That is what the 4 residual failures were. Fixed: the
   generator now drops such activities from `must_not_reveal` for `LAW_RESTATING_KINDS` = {ordinance,
   fee_resolution, staff_report, bill_analysis, council_minutes} only. Every other kind — program page, FAQ,
   form, checklist, news, third-party guide, reddit/forum thread — still treats a disclosure as a genuine leak.
2. **The ceiling was NOT under-crediting** (an earlier version of this section claimed it was; that was wrong).
   The pre-existing statute-level reveal rule already credited all 16 — 7 exact, 9 approximate, none hidden —
   because the statute text and bill analysis reveal element ids at `level: "statute"`, which credits the
   implementing activity. Ceiling means are unchanged by the fix: `exists_exact` 0.79, `exists_any` 0.84,
   `hidden` 0.16. So the availability term of the error decomposition was never biased.
3. **Visibility is now a two-axis fact.** Every activity carries `statutorily_disclosed` (true for a
   `staff_only` activity implementing a public mandate) alongside `visibility`. The step stays invisible in the
   *applicant's* experience while being inferable from *public law*. `ceiling.json` gained
   `statutorily_disclosed_credited` / `_ids`, and `coverage` now separates
   `staff_only_recovered_from_artifacts` (2.00 per task) from credit earned by the mandate alone (0.27 per
   task, 7 tasks) — the substantive quantity: mandated staff-only steps that *no document describes*.
4. **Renderer and verifier rule** (now in the verify prompt): statutory or fee-policy boilerplate restating a
   public mandate is a note, not a leak. A leak is an internal step, actor or timing that no public mandate
   implies.
4b. **Fee-administration notes: the line is quantification** (decided 2026-09-18). Rule 4 above
   settles whether such a note is a LEAK; it is silent on whether it is an *extraneous fact*, and
   `VERIFY_BRIEF`'s definition enumerated four categories (fee, step, department, timeline) that a
   non-refundability rule belongs to none of. The gap showed up at scale: free-standing
   fee-administration notes appear in 137 of the 163 rendered fee schedules (non-refundable 91,
   cost-recovery 57, state surcharge 52, ordinance-controls 14, supersession 12, blanket basis 5),
   159 of the 163 pass, and 3 of the 4 failures are fixes targeting exactly these notes. The same
   sentence was therefore passing in ~132 artifacts and failing in 3, and two agents independently
   asked for an adjudication.
   The line drawn: an unquantified statement of fee POLICY is boilerplate and passes; a statement
   attaching a QUANTITY to a fee -- a denominator, a rate, a proration, or a blanket "unless
   otherwise noted" -- is an extraneous fact unless a `fee` reveal licenses that basis for that row.
   It sits there because payer cost is a scored quantity: a denominator is what an extractor turns
   into a burden number, and an unquantified policy rule is not.
   Two clarifications the first application earned, recorded because they existed only in the
   dispatch text and that is exactly how the same sentence came to pass in ~132 artifacts
   and fail in 3: a **Basis column** is caught only when it states a QUANTIFIED basis the
   spec withheld, since "Cost recovery" answers how an amount was set rather than "per
   what?", and the licensed blanket sentence "fees are set on a cost-recovery basis"
   stays -- failing the same content in column form would make the standard turn on
   typography. And a **period word for how often the schedule is reviewed or amended** is
   not a denominator: "reviewed annually as part of the budget" is an amendment cadence,
   not a charging basis. "Annually" is a denominator only where it says what the payer is
   charged per. Realistic boilerplate survives,
   which matters for a corpus calibrated to real documents, and nothing that can move a scored
   quantity goes unlicensed.
   Measured cost of the decision: of the 43 fee schedules that carry reveals, 27 have no quantified
   note, 4 already fail with fixes aimed at one, and 12 pass today and need a one-clause edit. The
   61 distractor fee schedules that carry a quantified note are unscored noise and are left alone --
   real schedules do say "per application", and the distractor corpus is where that realism is free.
   The rule thus reproduces the corpus's existing behaviour on 159 of 163 artifacts while making it
   principled rather than instinctive.
5. **The claim is testable on the real corpus**: the share of a process's back-office steps inferable from
   statute alone is a property of the statute's specificity — high for DROS (the Penal Code scripts the
   dealer's acts) and low for CalFresh (the caseworker procedure lives in a county manual, not the statute).
   It predicts how far public-information reconstruction can reach into the back office.

## Retrieval realism: how the mock web differs from real search (2026-09-15)

Alex's question: the search process is a discrepancy between the synthetic benchmark and the real web. It is, and the traces in `runs/synth_search/*/trace.jsonl` show exactly where. The solver wrote **real-search-shaped queries**:

```
City of Halvern "Unit Legalization Program" "Marisol Gov. Code § 41210"
site:halvern.gov "Unit Legalization Program" application form checklist
site:halvern.legistream.com Halvern "Unit Legalization Program" "staff report"
```

### Fixed now
The mock was BM25 bag-of-words, so `site:`, quoted phrases, `filetype:` and `OR` were **silently tokenised** — a solver that searched well was punished for it, and a solver that searched naively was not. `pipeline/procbench/web.py` now parses and honours `site:`/`inurl:`/`-site:`, `filetype:`, `intitle:`, quoted phrases and `-term` exclusions, records which operators a query used in the trace (so operator reliance is measurable), and applies an **authority prior** by document kind (an official program page outranks a forum thread for the same terms, as a live engine would). Verified: the `site:halvern.legistream.com` query now returns only that host, and `filetype:pdf` returns only PDFs.

### Remaining, unfixed discrepancies — ordered by how much they distort the retrieval term

1. **No retrieval hazards.** Every document is indexed, fetchable, and text-extractable. The real corpus collection hit the opposite constantly: 403 to scripts (Justia, LADBS, sanjoseca.gov, El Dorado County), JS-rendered shells that return navigation only (LADBS program pages, Socrata dataset pages, PowerBI dashboards), documents that exist only in the Wayback Machine (Lafayette's page), scanned PDFs whose extracted text is garbled (Sonoma's grand jury report: "wi6in l5" for "within 15"), and reddit.com refusing scripts entirely so an archive API was required. Proposed knobs: `p_403_to_bot`, `p_js_shell`, `p_wayback_only`, `p_scanned_pdf`, `p_not_indexed` (findable only by following a link from a hub page). These change *which strategy wins*, which is the thing being measured.
2. **Corpus scale and ranking regime.** 1,315 documents versus billions. On a small closed corpus BM25 almost always returns something plausible, so a wrong guess is rarely punished with an empty result — real search punishes it. Conversely the 4:1 decoy ratio may *overstate* difficulty: for a real permit query the city's own page usually ranks first. Both directions are unmeasured.
3. **No non-search discovery channels.** Real agents use sitemaps, site search boxes, "related documents" rails, agenda-management systems (Legistar/Granicus), Google cache and the Wayback Machine. The mock has fetch-plus-links, so one-hop following works, but there is no sitemap or per-site search.
4. **Reddit search is unrealistically good.** The mock runs BM25 over thread text. Real reddit search is poor, which is why practitioners use `site:reddit.com` on a general engine or an archive API — we learned this first-hand.
5. **Snippets and result counts are fixed** (8–10 hits, head-of-document snippets) rather than query-biased and variable.

### The validity move that settles it
We hold nine real processes with known target documents. Run the *same query strings* against a real engine for a real process, and measure where the true documents rank and how many queries it takes to reach them. That gives an empirical target for the mock's decoy ratio, authority prior, and hazard rates, instead of guessing. Until that calibration exists, the retrieval gap measured on W1 (ceiling-relative recall 0.96 → 0.53) should be read as *the cost of searching a well-behaved corpus*, which is a lower bound on the real cost.

## Agency maps and sitemaps: giving the model the universe of actors (2026-09-15)

**The problem being fixed.** Documents disclose that a step *exists* 79% of the time but say *which department does it* only 36% of the time, and the statutes deliberately leave "which department administers" to the jurisdiction. So for two thirds of steps the model must invent a department. Measured actor accuracy is 0.33–0.79 with no baseline to compare it against, because the guess is drawn from an unbounded space. That makes the number uninterpretable, not just bad.

**Why adding an agency map is realistic rather than a cheat.** Verified against our own real corpus:

| real source class | tier | what it gives | verified in corpus |
|---|---|---|---|
| Master fee schedule organised under department headings | declared | which division collects money for which service — a *partial* program→actor map | yes — Hayward's FY2026 schedule is sectioned by Building Division, Development Services, Fire, Housing, Maintenance Services, Police |
| Staff-report `FROM:` line | designed | which director owns the program | yes — "Sara Buizer, Director of Development Services", "Director of Finance", "Peg Stevenson, Director, City Performance Unit" |
| Budget / audit organisation chart with authorised positions | designed | divisions, sub-units, staffing per function; names internal units the public never sees | yes — 8 documents (State Auditor EDD/gambling/mobilehome/hospice, San Diego DSD, San José permit review, CSLB board packet) |
| Permit-portal routing display / routing dataset | observed | the actual review stations a case passed through, sometimes with reviewer names | yes — SF's `Building Permit Addenda with Routing` carries `station` and `plan_checked_by` per addendum (see `corpus/ab2533/process/observed_data_scan.md`) |
| Municipal code administration chapter ("the Building Official shall enforce…") | local statute | duties assigned to named officers | **no** — the class certainly exists but we saved program pages and state statutes, not local admin chapters. Collect. |

**What to add to the world, and the one rule that keeps it a benchmark.** Give the model the *universe*, never the *mapping*. The mapping from program to department is the thing under test.

1. `department_directory` — one per jurisdiction, declared tier, always present. Every department and division with a one-line remit, address, phone, counter hours. **Must not** state which department runs which program beyond what the program pages already say.
2. `sitemap` — one per jurisdiction, declared tier, always present. An A-Z service index of titles and urls on that host, covering target *and* decoy programs so it does not hand over the answer. This also repairs a logged discrepancy: link-following from a hub becomes a viable retrieval strategy, as it is on real `.gov` sites.
3. `org_chart` — designed tier, knob `p_org_chart` ≈ 0.4, rendered as a budget excerpt. Divisions, sub-units, authorised positions, reporting chain. May name internal units, so it legitimately raises the staff-only ceiling.
4. `portal_routing` — observed tier, knob `p_portal_routing` ≈ 0.25. A case-status extract showing review stations per case. The strongest actor signal, and real.
5. `fee_schedule` reveals regrouped so each fee sits under its collecting department — a partial actor map, exactly as real schedules do.

**Why this is the research point, not a polish item.** With a directory of K departments, actor attribution becomes a *selection* problem with a chance baseline of 1/K, so the scorer can report three separable quantities: whether the predicted actor exists in the jurisdiction at all (hallucination of institutions), whether it is the right one (attribution), and lift over chance. And because the world can be built with and without the agency map, the with/without comparison is a clean ablation on whether an LLM can attribute ownership given the institutional universe — which is the learnable question underneath, per `docs/2026-09-15-process-benchmarks-plan.md`.

**Consequence to honour.** Adding these sources changes the benchmark. Every actor number measured so far (actor accuracy 0.33–0.79, actor disclosed for 36% of steps) is the **no-agency-map** condition and must be labelled as such; the new condition is `agency_map`. Re-run both, report the pair.
