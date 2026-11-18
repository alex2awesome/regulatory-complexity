# Solar/ADU: administrative anchors and burden-first execution

2026-09-30. One bounded session implementing the revised Solar/ADU handoffs.
This is the task's single execution/results document; update it in place.

## Priority and definition of done

The September 30 priority shift supersedes the older request to enlarge all 22
forum-only timing fits. Agency-recorded clocks will use administrative anchors;
forum reports on those clocks become source-comparison/calibration evidence.
Forum-only fitting in this session is limited to three previously unmodeled
burden intervals: contract to permit submission, order to design, and order to
cancellation. These are conditional report distributions, not population clocks,
abandonment rates, or identified agency capability.

Session deliverables:

1. A single-pass working crosswalk of the 9,360 excluded Solar timing candidates,
   preserving every candidate and its inherited interpretation.
2. Prospective start/end event guidance for Solar and ADU readers, plus a consuming
   adapter that retains unknown geography/year and distinguishes admin matches.
3. One attempt per eligible burden frame using unchanged V6 conditional-frame
   priors, support rules and numerical gates. No chain extensions or successor fits.
4. Two burden-ranked full-read Solar packets and one at-most-25-thread ADU slice,
   using Sol; one existing mechanical check per output, not a new audit queue.
5. Explicit status of the administrative dependency, denominators and next steps.

No toy-model changes, synthetic work, CalFresh work, acquisitions, commits, raw
source changes, or historical-output replacements are in scope.

## Ownership and current artifacts

- Claude owns Arctic Shift acquisition and admin preparation steps 1–7.
- Luna produced the working Solar crosswalk in
  `runs/solar_admin_integration_20260930/clock_crosswalk_review.jsonl`.
- Sol completed Solar `CODEX_SOLAR_0343` and `CODEX_SOLAR_0404`, selected by burden
  signals from held Gemma metadata, reading every held comment.
- Sol completed ADU `codexA54`, 25 burden-ranked unread threads, using the existing
  validated presentation method for long ADU threads. A53 remains unassigned.
- Root integration uses `pipeline/procbench/forum_admin_cells.py`; outputs are
  `runs/solar_admin_integration_20260930/{solar,adu}/`.
- Remote fits use `/dfs/scratch0/alexspan/solar_admin_integration_20260930/`,
  separate from every historical fit and Claude's administrative work.

## Crosswalk: what the review does and does not establish

All 9,360 candidates have a row. The working categories are 1,878 declared-clock
matches, 3,510 other process intervals, 3,884 non-process, and 88 unclear.
Some Gemma “other” labels exactly equal an existing declared clock; the adapter
uses the explicit target label, not this inconsistent category alone.

This was a Luna-authored rule review of Gemma candidates, **not 9,360 independent
contextual adjudications**. It must not be presented as semantic gold. An initial
adapter incorrectly let incidental warranty/cancellation words override a claim;
that unadopted working logic was corrected before consumption. No source quotes
were reverified or historical records altered.

The resulting labels are working interpretations for a bounded exploratory
analysis, with the audit's approximate 80% declared-match precision as a warning,
not a calibrated per-row probability. No made-up uncertainty weights are used.
Original labels, quotations, statuses, bounds and source references remain intact.

Reapplying the existing support/thinning rules to the same 15 historical Solar
clocks produces **3,277 eligible pooled reports**, versus 1,225 previously fitted,
and **987 California-supported reports**, versus 321 previously fitted. These are
admission/accounting results, **not newly fitted observations**. The corresponding
plans are `legacy_pooled_accounting/fit_plan.json` (15 eligible frames) and
`legacy_california_accounting/fit_plan.json` (13), under this session's run directory.
Interconnection-submission-to-PTO has 236 pooled/93 California-supported reports;
permit-submission-to-approval has 195/84. This recovers useful evidence without
claiming that its working semantic labels have all been individually reviewed.

## Administrative matching preparation

The adapter preserves all **10,605 Solar** timing candidates and all **475 ADU**
admitted elapsed readings in the A1–A52 snapshot. It identifies **527 Solar** and
**28 ADU** candidate claims on admin-equivalent clocks. At this initial preparation,
13 Solar candidates and zero ADU candidates have enough typed cell keys to attempt
an actual jurisdiction/utility/start-year match. This is a metadata-readiness count,
not a judgment that the remaining reports are invalid or lack usable context.

A bounded Luna pass through the **28 existing coded ADU records** recovered
location/region candidates for 24 and start-year candidates for seven, including
previously declared contextual date assumptions. The adapter now consumes
`adu_cell_key_readings.json`, retaining its evidence references and qualifications.
**Four ADU claims now have candidate geography/year keys** (Poway, Sacramento
County, and two San Jose-context claims). This does not establish four matches:
county/city distinctions, thread-inferred locations, and date assumptions still
matter, and a corresponding administrative cohort may not exist. No invented
weights, inferred certainty, or post-year-only date assignments were added.

Unknown geography stays in the forum evidence. County does not become city/AHJ;
bare PGE needs California context to distinguish it from Portland General Electric.
Explicit event dates, or a dated completed endpoint plus an elapsed interval, can
provide start-year candidates. A post's year alone is not the project year.
All unready rows retain reasons and their original evidence for subsequent key
extraction or an explicitly uncertain cell assignment; they are not deleted.

The shared event vocabulary lacks order, deposit, installation completion,
provider-selection completion and cancellation. Those endpoints remain null with
the existing clock meaning preserved. In particular, installed is not finaled,
design completion is not design start, and general preapplication work is not
necessarily a preapplication meeting.

Administrative input availability was checked once, locally and on sk3:
`admin_data_20260929` exists on sk3, but the promised
`admin_model_inputs_20260930` directory was not present in either location.
No source-offset fit can yet be claimed. Preparing comparisons is useful work
while Claude shapes the cohorts; duplicating that acquisition/preparation is not.

The current V6 histogram contract supports completed multinomial bin counts, not
pending-case ages/censoring. Administrative preparation must retain pending ages
and their denominators separately for a survival likelihood; putting pending cases
in the last completed-duration bin would be wrong. A completed-only fit must say
that it is conditioned on completion. DG applications and interconnected sites
overlap, and different phases of the same projects are not independent cohorts
merely because they measure different clocks. Their lineage must survive binding.

## Modeling assumptions and limits

- Existing V6 conditional-frame priors are unchanged: elapsed median prior 7 days,
  log-location SD 2, case-log-SD median 1 and prior SD .5. Four chains, 1,000 warmup,
  2,000 draws; the existing numerical gates and 128-node quadrature are retained.
- At least 15 contributor labels and five finite completed intervals are required.
  Contributor thinning is recomputed across the expanded snapshot, not appended
  from separately thinned batches. An author label is not a verified unique project.
- Order-to-cancellation describes the wait in reported terminated projects. It
  does not estimate an abandonment probability or treat cancellation as installation.
- National and unresolved reports stay in the pooled conditional report frame;
  these fits must not be called California population estimates.
- In later admin integration, negligible forum/admin project overlap is a stated
  assumption, not demonstrated record disjointness.
- “Reference admin source” does not mean every dataset is a census of applicants.
  Interconnected sites exclude pending cases; the applications table has broader
  coverage. San Jose's active/expired stock cannot identify survivor selection merely
  by adding a source indicator; use its data with explicit conditioning/sensitivity.
- No claim of learned source trust, superior LLM performance, full process structure,
  or intrinsic agency capability follows from this preparation.

## Results and remaining work

All three burden fits completed on sk3 on their first attempt and passed the
existing numerical gates. Results use 125 contributor reports from the frozen
crosswalk snapshot, not the newly staged reader batches below.

| Reported interval | Reports | Completed intervals / completed lower bounds / pending | Posterior median duration, days (90% credible interval) |
|---|---:|---:|---:|
| Contract to permit submission | 21 | 14 / 0 / 7 | 40.7 (21.3–83.4) |
| Order to design | 76 | 49 / 3 / 24 | 45.3 (30.5–69.4) |
| Order to cancellation | 28 | 25 / 3 / 0 | 228.1 (141.9–370.7) |

These intervals describe uncertainty in the fitted distribution's **median**, not
90% of individual projects. They are conditional on forum reporting and the working
clock interpretation. “Order to design” does not establish whether every speaker
meant the same design milestone. Cancellation is a reported terminated-case wait,
not a probability of cancelling. These limitations survive excellent convergence.
Only 8, 25, and 6 reports respectively have California support; these pooled fits
are not California population estimates. Nine dependent reports remain outside
the independent likelihood; one business-day report is below support.

Fit receipts and saved posteriors:
`runs/solar_admin_integration_20260930/burden_frames/fit_results.json` and the
three `frame_*/fit/` directories. No chain extension or prior change was used.

Completed reading, each with its one existing mechanical check:

| Batch | Threads disposed | Held comments read | Episodes staged | Other staged evidence |
|---|---:|---:|---:|---|
| Solar CODEX_SOLAR_0343 | 30 | 318/318 | 17 | 9 timing, 4 incurred-cost, 29 action claims |
| Solar CODEX_SOLAR_0404 | 30 | 368/368 | 18 | 11 timing, 7 incurred-cost, 37 action claims |
| ADU codexA54 | 25 | Existing ADU presentation method | 3 new + 3 confirmed additions | 14 practice claims; 42 action rows |

Solar outputs live in `runs/solar_forum_20260922/parse/claude_bulk/<packet>/`
(`coverage.json`, `decisions.json`, `timing_staged.json`, `manifest.json`).
ADU output is `runs/adu_forum_20260921/parsed/codexA54_recoded.json`, with the
receipt in `work/codexA54/reading_receipt.json`. ADU includes 20 correction/response/
failed-inspection action rows, six cost rows, two effort rows, six bounded-round
rows, and an abandonment episode; these overlapping counts are not separate cases.
All three batches are **staged, not consumed by the reported fits**. No historical
batch was reverified and no claim of complete corpus coverage follows.

The larger unread Solar/ADU queues, Houzz answers, and future Claude deliveries
remain. These 85 threads are this bounded batch, not a declaration that reading
is finished. Costs, effort, repeats and action counts were extracted but have not
yet been converted into new posterior estimates; availability, participation and
repeat counts must not be conflated. New staged evidence needs the ordinary
deduplication/compiler adoption before it reaches those likelihoods.

After the administrative cohorts arrive: resolve remaining cell keys from retained
context, bind exact clocks/cohort hashes, implement the declared source-comparison
fit, then evaluate held-out jurisdictions/years and the same-evidence LLM baseline.
These later steps are not completed by a crosswalk or a numerical timing fit.
