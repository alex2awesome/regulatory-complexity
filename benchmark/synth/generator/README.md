# Synthetic process-ecosystem generator

County-panel update (2026-09-16): `world_model_version=2` adds a **58-county
panel** whose availability, caseload, speed and fee coefficients are calibrated
against real retrievals rather than chosen. The rates and their provenance are in
[the source-volume register](../../../docs/2026-09-16-source-volume-register.md);
the divergences from the W2 spec are in
[the decision log](../../../docs/2026-09-16-w2-decision-log.md). Version 1 is
unchanged and byte-identical: the panel is *appended* to the four hand-written
jurisdictions, never substituted for them.

Three things the calibration established that a reader should not have to
rediscover. **Existence and volume are separate mechanisms** — one real forum
assigned a thread to all 58 counties in a single administrative batch, so
existence carried no population signal while volume spanned three orders of
magnitude. **Slopes differ by source family** by more than 50%, so there is one
slope per channel, not a global one. And **a count of documents is not a count of
information**: only 10.6% of the real administrative records carry a measurable
span, and only 32% of user posts carry a duration at all.

Check a built county world with
`python3 pipeline/procbench/audit_corpus_anchors.py <world_dir>`, which compares
the artifacts against the measured anchors. It exists because a coefficient can
be right while the corpus is wrong: a render cap and a flat caseload each
flattened a correct population gradient during this build.

Clock-contract update (2026-09-16): newly generated logs retain explicit
`event_clocks` for the first decision, last decision and last modeled work, with
separate censoring flags and `event_clock_summaries`. Legacy `elapsed_days` remains
arrival-to-last-decision on the uncensored finally-decided cohort; it must not be
called first-decision time. These additions do not change RNG streams or existing
W1 files. New dashboard specs state their clock and use the median's own decided
sample size, not all completed cases including abandonment.
The build command refuses nonempty destinations; it no longer silently deletes
old generated truth/specifications while leaving old rendered documents behind.

New worlds also default to **`visit_accounting_version=2`**. This is a deliberate
generator-behavior change: repeat visits are distinct from loop-trigger counts,
repeat speedups apply to the actual visit index, base fees are charged once, and
inspection fees remain per visit. Version-2 paths record `visit_index`,
`loop_triggers_before` and `fee_charged_dollars`; `fees_paid_by_observation` excludes
future charges. Existing saved worlds without this knob replay with legacy version
1, including its known defects. Never regenerate W1 in place or compare changed
version-2 ground truth to old rendered documents.

New `world.json` files record `generator_version` and an explicit top-level
`visit_accounting_version` as well as the knob. **Seed 1 with current defaults
does not reproduce W1's legacy accounting.** A fresh diagnostic build must pass
`--knob visit_accounting_version=1`; exact historical specification/render replay
also requires the historical source and saved artifacts. This knob alone does
not undo later disclosure-contract fixes. Never overwrite W1 to add metadata.

Future observation contracts also distinguish first-visit cycle durations from
summed visit cycles. Observed first-visit summaries exclude future completions;
no observed visits yields a forecast rather than a fabricated measured median.
Persona reports omit future completed-visit durations and no longer describe a
completed delayed decision as an unfinished wait. The audit template reports p90
as a percentile, not the incorrect claim that 20% exceed it. These changes do not
retroactively repair W1's text or make prior estimator comparisons held out again.

Rework observations now have a separate count contract. Logs retain timestamped
`rework_events`; `observed_rework` excludes future triggers and future arrivals,
includes open/abandoned cases, and explicitly includes all modeled stages. New
dashboard specs use this actual cohort's numerator and denominator, not latent
lifetime totals. FAQ planning probabilities are per **eligible checkpoint visit**,
not the fraction of applications needing any correction, and no longer round a
zero retry probability up to one in ten. Version 2 also waits for a nonblocking
checkpoint's result before starting the correction it triggers. Legacy version 1
retains its old schedule; added event metadata does not consume RNG draws.

Builds a complete benchmark world — statutes, local rules, full designed processes
(including the back-office nobody publishes), a simulated event log, artifact
**specs** with an explicit visibility model, the information **ceiling**, and
**tasks** — with **no LLM calls**, Python 3.12 **stdlib only**, deterministic
given a seed. Wave 2 renders the specs into prose; Wave 3 verifies them. Normative
design: [`../DESIGN.md`](../DESIGN.md). Framing: `docs/2026-09-15-process-benchmarks-plan.md`.

```bash
# build in a fresh destination (never overwrite the existing W1 evaluation corpus)
python3 -m benchmark.synth.generator.build --world WNEW --seed 101 --out benchmark/synth/worlds/WNEW
python3 benchmark/synth/generator/build.py --world W2 --seed 2          # equivalent

# knobs on the command line (JSON values)
python3 -m benchmark.synth.generator.build --world W3 --seed 3 \
    --knob p_publish_sop=0.4 --knob p_stale=0.5 --knob distractor_ratio=2 --knob n_applicants=50

# validate a built world and print counts
python3 benchmark/synth/schemas/validate.py --world benchmark/synth/worlds/W1

# smoke test (tiny world: 2 jurisdictions x 3 statutes)
python3 benchmark/synth/generator/test_generator.py
```

W1 (seed 1) builds in ~1.5 s and is ~16 MB (the per-applicant logs dominate).
Worlds are reproducible from `(world_id, seed, knobs)`, so `worlds/` need not be
kept in git.

## What it writes

```
worlds/W1/
  world.json                        knobs, 2 states, 6 jurisdictions, 12 statute domains,
                                    who implements what and why (+ why not)
  truth/statutes/<stat>.json        statute_truth   (S01..S12 Marisol, C01..C12 Corvane look-alikes)
  truth/local_rules/<jur>__<stat>.json   local_rule_truth (choices, added steps, lineage, prior version)
  truth/processes/<jur>__<stat>.json     process_truth  (8-20 activities, 4-11 actors, visibility,
                                    timing, fees, rework, prior-version diff)
  truth/log/<jur>__<stat>.jsonl     n_applicants simulated cases: per-activity start/end, rework
                                    rounds, outcome, elapsed days, fees paid
  truth/log/<jur>__<stat>.summary.json   median/p75/p90 elapsed, denial rate, mean rework rounds,
                                    per-activity medians and occurrence rates
  specs/<artifact_id>.json          artifact_spec: url, links_to, date, stale, reveals (ref/field/
                                    fidelity/value), must_not_reveal, contamination, persona, thread, why
  ceiling.json                      per task: recoverable_exact / _approx / only_wrong / hidden,
                                    field coverage, timing ceiling vs the true log median
  tasks.json                        one task per target process, five information conditions
  provenance.jsonl                  one line per generated object: inputs, the draws that mattered, why
  render_context/<jur>.json         the public facts a Wave-2 renderer may use (briefs/RENDER_BRIEF.md)
  verify_context/<model_id>.json    the hidden elements a Wave-3 verifier needs (briefs/VERIFY_BRIEF.md)
  counts.json                       the summary printed by the CLI
```

## How it works

Backwards generation, one module per stage (all draws come from
`rng.sub_rng(seed, *path)`, a RNG keyed by a hash of the seed plus a semantic
path — so generation order never affects content and any object can be
regenerated alone):

| module | stage |
|---|---|
| `domains.py` | the 12 statute domains as data: mandated elements, open choices, program-name variants, fee ranges, plausible back-office tags, pace |
| `world.py` | knobs; the states (Marisol, neighbour Corvane); 6 jurisdictions with real department structures; assignment of 6–8 statutes per Marisol jurisdiction (2–4 implementers per statute, 26 target processes) with a `why` for every adoption and non-adoption |
| `statutes.py` | `statute_truth`: skeleton (5–9 elements, kinds from the enum, shot clocks, "may" options, `must_precede`), 3–6 open choices, `sections` with `content_spec` detailed enough to render statutory prose; Corvane look-alikes differ in 1–3 elements |
| `local_rules.py` | `local_rule_truth`: a concrete value for every open choice, 0–3 locally added steps, stricter standards, a fee with its cost-recovery derivation, **template lineage** (copies another jurisdiction's rule, with a tell), **retrofit** and **prior version** |
| `processes.py` | `process_truth`: composes applicant steps, agency steps, locally added steps and **back-office** steps from a library into a phase-ordered graph, with visibility labels, **verb-first action names** (+ `element_text`/`span` for the statute wording, `local_name` for naming drift), kind-checked actors and `counterparty`, `per_case` standing obligations, lognormal timing, fees, rework loops, flow gates, and the prior-version diff |
| `simulate.py` | Monte-Carlo event log: per-activity cycle times, optional-step occurrence, rework, denial, ~3 % abandonment, right-censoring at `as_of` |
| `visibility.py` | **the visibility model** (below): which artifacts exist and exactly what each may say |
| `specs.py` | artifact identity: URLs and a navigable link graph, staleness, contamination, personas/threads, and the distractor corpus |
| `ceiling.py` | reduces the specs to per-element recoverability, the timing ceiling, and `tasks.json` |
| `counties.py` | **`world_model_version=2` only:** 58 fictional county-like jurisdictions shaped like the real California panel — the 8,600-fold population range, the **inverse** staffing-per-capita gradient, RUCC and UIC as separately-disagreeing rurality codes, the 39/18/1 consortium split. No real county name is reused. |
| `capacity.py` | **every planted coefficient in one place, each tagged `measured_anchor` / `derived_with_assumptions` / `design_assumption`** with its source file; the per-channel existence hurdle and volume slope, the retrieval funnel, caseload, speed, hourly rate, defect rates, and the named scenarios that carry the alternatives where the evidence does not identify a direction |
| `lineage.py` | the three source-dependence types kept apart — same case, same cohort, copied text — with `facts_agree` as an **independent** field, so shared prose over different procedures and different prose over one aggregate are both representable |
| `build.py` | CLI, file writing, `provenance.jsonl`, counts |

### The visibility model, in words

Nothing in an artifact is implicit: **every fact an artifact may state is a
`reveals` entry** with a `ref` (an activity id, a statute element id for
state-level documents, or `process` for end-to-end facts), a `field` (`exists`,
`actor`, `order`, `timing`, `fee`, `artifact`, `rework`), a `fidelity` (`exact`,
`approximate`, `vague`, `wrong`) and the literal `value` to state. Everything not
revealed anywhere is the availability gap the benchmark measures.

1. **Which artifacts exist** is drawn per (jurisdiction, process) from the
   publication knobs, with realistic overrides: a statute that mandates checklist
   publication makes the checklist near-certain; a program adopted by
   *administrative policy* almost never has an ordinance, staff report or council
   minutes (the Hayward finding: the designed tier can be empty at the
   legislative level); retrofits and contested programs are more newsworthy.
2. **What each kind may say** — applicant-facing steps are public; `applicant_inferable`
   steps leak only as status changes and delays; `staff_only` steps appear **only**
   in staff documents (SOP, staff report, audit) or an insider comment:
   - *program page* — applicant steps `exists` exact, the published order exact,
     end-to-end timing approximate-and-optimistic (p≈0.45) else vague, fee exact,
     lead department exact, terminal artifact exact;
   - *generic permits page* — the machinery (portal, resubmittal loop) not the program;
     one per jurisdiction, so its reveals carry a `process` field;
   - *form* — the application step and its required documents exact; with p=0.3 an
     "office use only" box leaks one back-office step at `vague`;
   - *checklist* — the inspection, what is inspected, the third-party option;
   - *FAQ* — timing approximate for 2–4 steps, one rework loop approximate;
   - *fee schedule* — fees exact (or `wrong` when stale); *fee resolution* — fees
     exact plus "supersedes Resolution No. X", the prior-version hook;
   - *ordinance* — the local rule: added steps, administering department, appeal;
   - *staff report* — 30–60 % of staff-only steps exact, the fee derivation,
     expected volumes, the neighbouring-city comparison (the lineage hint);
   - *SOP* — nearly everything exact, but a revision behind (each step missing with
     p=0.15): the ceiling-raising artifact;
   - *audit excerpt* — observed per-step timing plus staff-only steps;
   - *news* — adoption (fee, department, date) or backlog (volumes, waits, and with
     p=0.4 one internal bottleneck at `vague`);
   - *third-party guide* (law firm / expediter / installer) — every applicant step
     exact and in order, timing approximate from experience, fee approximate or
     plainly wrong, 1.5× more likely to be stale: often the most complete public
     description, and a trap;
   - *bill analysis* — state level: the intended skeleton and shot clocks exact
     (refs are statute element ids), the workflow the committee expected at `vague`;
   - *official stats* — end-to-end median, volumes, rework share, approximate;
   - *reddit thread* — see 4;
   - *forum thread* — older, politer, low fidelity, high contamination.
3. **Staleness**: an artifact dated before the current version's adoption describes
   version 1 (`stale: true`), and its changed facts are emitted at fidelity `wrong`
   with the prior value — so the ceiling counts them as wrong rather than missing.
4. **User posts** are drawn from the *simulated log* through the complaint-selection
   function (`P(post | denied)=0.5`, `delayed(>p75)=0.35`, `abandoned=0.25`,
   `normal=0.08`), so the reddit sample is biased exactly as much as the knob says.
   The OP reports *their* case with user noise (rounded to weeks/months, and with
   `p_wrong_fact_user` exaggerated or a wrong fee); comments add other sampled
   applicants, contamination about another jurisdiction or program, a stale "I did
   this in 2023" reply, and with `p_reveal_backoffice_in_comments` an insider
   revealing one staff-only step.
5. **Distractors**: look-alike Corvane processes (full artifact sets), unmodelled
   programs in the same jurisdictions (encroachment, banner, dog licence …), generic
   city pages that make the link graph navigable, off-topic threads in the same
   subreddits, and filler generated until `distractor_ratio` is met or `filler_cap`
   binds. URLs form a plausible graph: city home → departments → department →
   program page → form/fee/FAQ; ordinances on a municode-like host; staff reports on
   a Legistar-like host; threads under reddit-like URLs.
6. **Statutorily disclosed steps.** A `staff_only` activity whose `element_ref` names
   a statute element (or a locally added element carried in an ordinance/resolution)
   gets `statutorily_disclosed: true`. It is invisible in the applicant's experience
   but *inferable from public law*: any document restating the mandate discloses it.
   Consequences — the law-restating kinds (ordinance, fee resolution, staff report,
   bill analysis, council minutes) do not list it in `must_not_reveal`, while pages,
   FAQs, forms, checklists, news, third-party guides and threads still must; and the
   ceiling credits its **existence** at `approximate` (actor and timing stay hidden
   unless a document reveals them), audited per task as
   `statutorily_disclosed_credited`. In W1, 16 of the 184 staff-only steps in target
   processes are statutorily disclosed; 7 rest on the mandate alone.
   See DESIGN.md "Wave-2/3 finding: statutory mandates cannot be hidden".
7. **The ceiling** takes the best fidelity per (activity, field) over all artifacts
   about the process. A statute-level reveal credits the implementing activity at
   `approximate` (the statute proves the step exists, not how the city runs it); a
   stale fact counts as `wrong`. `timing_ceiling` reports the true log median, the
   best estimate from the posts, and the decomposition of the gap into selection
   bias (who posts) and report bias (how they round and exaggerate).

## Knobs (`world.json.knobs`, all overridable with `--knob k=v`)

DESIGN.md table:

| knob | default | knob | default |
|---|---|---|---|
| `p_publish_program_page` | 0.7 | `p_reveal_backoffice_in_comments` | 0.15 |
| `p_publish_form` | 0.8 | `p_stale` | 0.25 |
| `p_publish_faq` | 0.4 | `p_wrong_fact_user` | 0.3 |
| `p_publish_fee_schedule` | 0.9 | `complaint_selection` | denied 0.5 / delayed 0.35 / abandoned 0.25 / normal 0.08 |
| `p_publish_staff_report` | 0.35 | `distractor_ratio` | 4.0 |
| `p_publish_sop` | 0.1 | `naming_drift` | 0.6 |
| `p_third_party_guide` | 0.4 | `neighbor_state` | true |
| `p_bill_analysis` | 0.8 | `n_applicants` | 200 |
| `p_official_stats` | 0.3 | `world_model_version` | 1 (2 = the 58-county panel) |
| `n_counties` | 58 | `availability_scenario` | `reference` |
| `speed_scenario` | `reference` | `max_threads_per_county_process` | 400 |

Generator extensions (documented, same override path): `p_publish_checklist` 0.55
(→0.97 where the statute mandates publication), `p_publish_ordinance` 0.92,
`p_publish_fee_resolution` 0.6, `p_publish_council_minutes` 0.35, `p_publish_news`
0.3, `p_publish_audit` 0.06, `p_publish_forum_thread` 0.25, `p_template_lineage`
0.4, `p_prior_version` 0.4, `p_retrofit` 0.3, `p_backoffice` 0.55,
`p_abandon_total` 0.03, `p_appeal_if_denied` 0.25, `max_rework_rounds` 3,
`n_applicants_neighbor` 50, `max_threads_per_process` 3, `filler_cap` 1000,
`as_of` "2026-09-15", `sim_window_days` 760, `only_jurisdictions` / `only_domains`
(build a subset world — used by the smoke test).

## Adding a domain

1. Add one entry to `DOMAINS` in `domains.py` (copy the closest existing one). You
   need: `title`, `statute_title`, `cite`, `bill`, `shape`
   (`prescriptive`/`mid`/`minimal`), `pace` (clock speed relative to the amnesty
   baseline of 1.0), `state_agency`, `applicability`, `purpose_spec`, `defs`,
   `elements` (tuples `(element_id, kind, name, actor_role, optional,
   shot_clock_days, must_precede)` — kinds from the DESIGN enum), `choices`
   (`(choice_id, kind, what, constraint)`), `programs`, `terminal`, `lead_roles`,
   `fee_range`, `fee_label`, `fee_basis`, `app_form`, `checklist`,
   `inspection_name`, `backoffice` (tags from `processes.BACKOFFICE`),
   `extra_actors`, `user_terms`, `news_adopt`, `news_backlog`, `local_names`.
2. Add the substantive choice values to `CHOICE_VALUES` in `local_rules.py`
   (`"<domain>.<choice_id>"` → 2–3 variants) and, if useful, `STRICTER` and
   `ADDED_BY_DOMAIN`.
3. Add a Corvane cite/title to `CORVANE_CODES` in `statutes.py`, a kind-fit row to
   `KIND_FIT` in `world.py`, and a `DENIAL_BASE` entry in `processes.py`.
4. Add the new domain string to the `domain` enum in
   `../schemas/statute_truth.schema.json`, `local_rule_truth`, `process_truth`.
5. Rebuild and validate. The generic machinery (phases, back office, visibility,
   ceiling) needs no changes.

New back-office step: one entry in `processes.BACKOFFICE` (name variants, actor
role, occasion, visibility, phase, median/p90, output artifact) plus its tag in
the domains that should draw it; add it to `NON_BLOCKING` if the case does not
wait for it.

## What W1 (seed 1) contains

24 statutes (12 Marisol + 12 Corvane look-alikes) · 6 jurisdictions · 38 processes
(26 target + 12 look-alike) · 571 activities (260 applicant-facing, 127
applicant-inferable, 184 staff-only; 45 of them standing obligations) · 76 rework
loops · 5,800 simulated applicants · 1,315 artifact specs (263 target, 1,052
distractor = ratio 4.00, of which 600 pure filler = 57 %) · 26 tasks. Mean
ceiling: 79 % of activities exactly recoverable, 16 % hidden, 2.3 staff-only steps
recovered per task; the published order is exactly recoverable for 25 of 26 tasks;
believing the user posts overstates the median timeline by 30 % (selection bias
+18 days on top of report bias). Expected rendering volume ≈ 499k words: 163k
target, 248k structured distractor, 87k filler.

| task | jurisdiction | program | lead department | af/ai/so | actors | program fee | true median/p90 days | ceiling exact | hidden |
|---|---|---|---|---|---|---|---|---|---|
| J1__S01 | Halvern | Unit Legalization Program | Permit Services Center | 7/2/6 | 8 | $380 | 128 / 199 | 0.67 | 5 |
| J1__S02 | Halvern | Short-Term Rental Registration | Planning Division | 9/3/5 | 8 | $700 | 74 / 126 | 1.00 | 0 |
| J1__S03 | Halvern | Street Vending Program | Finance, Revenue Division | 7/4/2 | 8 | $175 | 74 / 119 | 0.92 | 0 |
| J1__S04 | Halvern | Urban Forestry Permit | Parks and Recreation Department | 9/3/3 | 9 | $540 | 124 / 198 | 0.80 | 2 |
| J1__S05 | Halvern | Home Business Clearance | Finance, Revenue Division | 3/3/3 | 5 | $190 | 22 / 46 | 1.00 | 0 |
| J1__S10 | Halvern | Community Event Permit Program | Office of the City Clerk | 5/5/5 | 10 | $1,485 | 175 / 264 | 0.67 | 3 |
| J1__S12 | Halvern | Contractor Business Registration | Finance, Revenue Division | 5/2/6 | 5 | $170 | 43 / 72 | 0.77 | 2 |
| J2__S03 | Ellinsport | Street Vending Program | Finance, Business Tax Section | 8/5/2 | 8 | $140 | 76 / 116 | 0.87 | 2 |
| J2__S04 | Ellinsport | Tree Removal Permit | Current Planning Section | 7/3/4 | 6 | $200 | 133 / 246 | 0.71 | 3 |
| J2__S07 | Ellinsport | One-Day Solar Permit | Development Review Section | 7/3/6 | 6 | $230 | 21 / 55 | 0.94 | 1 |
| J2__S08 | Ellinsport | Healthy Housing Inspection Program | Neighborhood Compliance Bureau | 9/4/7 | 7 | $110 | 195 / 308 | 0.60 | 6 |
| J2__S09 | Ellinsport | Small Animal Keeping Clearance | Neighborhood Compliance Bureau | 4/2/4 | 5 | $65 | 34 / 73 | 0.60 | 3 |
| J2__S11 | Ellinsport | Well and Septic Permit Program | Sennet Co. Env. Health (by agreement) | 6/4/6 | 6 | $910 | 98 / 252 | 0.56 | 5 |
| J2__S12 | Ellinsport | Contractor License Verification Program | Development Review Section | 7/2/3 | 5 | $200 | 52 / 97 | 0.92 | 0 |
| J3__S02 | Calder Springs | Vacation Rental Permit Program | Finance and Administrative Services | 8/4/6 | 8 | $760 | 68 / 109 | 0.94 | 1 |
| J3__S05 | Calder Springs | Home-Based Business Registration | Planning Technician | 3/3/4 | 6 | $155 | 22 / 43 | 0.90 | 0 |
| J3__S06 | Calder Springs | Mobile Unit Plan Check | Sennet Co. Env. Health (by agreement) | 8/5/2 | 6 | $1,395 | 181 / 344 | 0.93 | 1 |
| J3__S07 | Calder Springs | One-Day Solar Permit | Sennet Co. Building Insp. (by contract) | 7/3/6 | 6 | $375 | 33 / 76 | 0.75 | 4 |
| J3__S08 | Calder Springs | Proactive Rental Inspection Program | Code Compliance Officer (0.5 FTE) | 9/4/6 | 7 | $145 | 221 / 372 | 0.63 | 5 |
| J3__S10 | Calder Springs | Street Closure and Event Permit | Public Works Maintenance Division | 6/7/4 | 8 | $1,435 | 230 / 344 | 0.53 | 6 |
| J4__S01 | Sennet County | Unit Legalization Program | Building Inspection Division | 7/2/4 | 8 | $704 | 118 / 201 | 0.69 | 4 |
| J4__S06 | Sennet County | Mobile Food Facility Permit | Environmental Health Division | 8/3/3 | 5 | $352 | 92 / 176 | 0.86 | 2 |
| J4__S07 | Sennet County | One-Day Solar Permit | Building Inspection Division | 6/2/6 | 6 | $176 | 22 / 60 | 1.00 | 0 |
| J4__S08 | Sennet County | Rental Housing Safety Program | Code Compliance Unit | 8/4/4 | 7 | $115 | 132 / 209 | 0.81 | 1 |
| J4__S09 | Sennet County | Backyard Hen Permit | Code Compliance Unit | 4/4/4 | 7 | $120 | 34 / 60 | 0.83 | 2 |
| J4__S11 | Sennet County | Water Well Construction Permit | Public Works, Road Division | 7/4/6 | 8 | $1,232 | 148 / 262 | 0.59 | 5 |

(Corvane look-alikes, distractors only: Tarnbrook — mobile vending, solar express,
rental safety, contractor registration; Wexley County — heritage trees, food
trucks, animal keeping, community events. Numbers above are from the build at the
time of writing; rebuild prints the current ones.)

Statute shapes in W1: prescriptive S02, S03, S06, S07, S08 (7–8 mandated elements,
shot clocks, appeals); mid S04, S10, S11, S12; minimal S01, S05, S09 (5 listed
elements, 2 optional → 3 mandated, AB 2533-like — the process is mostly local
invention). Of the 34 local rules, 10 carry template lineage (with a tell), 20
have a superseded prior version, and 11 are retrofits of a pre-statute program.

## Decisions taken beyond DESIGN.md

* **Extensions to `process_truth`**: `blocking` (whether the case waits for a step
  — without it, 15 serial back-office steps make a four-month permit take two
  years), `per_case` (standing obligations such as publishing a checklist are not
  walked by an applicant), `p_occurs` and `flow_gate` (`if_denied` / `if_appealed`
  / `if_rework`), plus `jur_id`, `domain`, `program_name`, `unimplemented_elements`
  and `deviations` (e.g. a third-party report filed with the agency, so the
  statute's confidentiality is not preserved in practice — the §10a finding).
* **Base-schema conflicts resolved in DESIGN's favour**: `source: "designed"` and
  actors as objects are not in `pipeline/schemas/process_model.schema.json`;
  `validate.py` checks the base schema's *required keys* and validates the rest
  against the extended schema.
* **No `statute` artifact kind exists in DESIGN's enum**, so the statute text is
  emitted as `kind: "ordinance"` with `subkind: "statute_text"` on a leginfo-style
  host.
* **`reveals.ref` namespace** extended to `process` (end-to-end facts: elapsed
  time, volumes, the published order), statute element ids (with
  `level: "statute"`, for bill analyses and statute text) and `prior_version`.
  Shared multi-process artifacts tag each reveal with `process`, and their
  `must_not_reveal` ids are process-qualified (`"J1__S03:A07"`).
* **`distractor_ratio` is enforced globally** (non-target artifacts per target
  artifact across the index) by generating filler up to `filler_cap`; per task the
  effective distractor count is far higher (~1,050) and is reported in
  `ceiling.json`.
* **Right-censoring**: cases still in flight at `as_of` are emitted with
  `censored: true` and excluded from the elapsed summary, as in a real permit
  extract; `denial_rate_all` (using provisional outcomes) is the unbiased
  comparison against `process_truth.denial_rate`.
* **Two extra outputs** the briefs need: `render_context/<jur>.json` (public facts
  for Wave 2) and `verify_context/<model_id>.json` (hidden-element descriptions for
  Wave 3).
