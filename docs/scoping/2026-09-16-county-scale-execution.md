# County scale-up: execution and retrieval handoff

2026-09-16. Implements the scoping stage of the
[scale-up plan](../2026-09-16-county-scale-up-plan.md) and
[work packets](WORK_PACKETS.json). Live ownership/status comes from the append-only
[findings log](FINDINGS.jsonl), not the initial `status` fields in the packet JSON.
Updated after the independent source audit, P12 spot-check and N1–N11 retrieval continuation.
Alex's latest direction is source collection, not additional unit-test work.

The requested [synthetic corpus generation plan](../2026-09-16-synthetic-corpus-generation-plan.md)
turns these findings into a W1-style truth/simulation/visibility/render/verify
handoff, with a staged pilot, proposed program expansion and explicit corrections
to the earlier W2 spec. It is a plan, not an implemented or evaluated W2 release.

## Work delivered by this pass

| Packet | Status | Result and location |
|---|---|---|
| P1 CalFresh | Acceptance complete | [Report](2026-09-16-calfresh-58-counties.md); 58 counties × 121 report months in CF 296, plus FY 2024–25 CF 18 mean approval times and bins; [definitions/reproduction](../../corpus/counties/calfresh_README.md) |
| P3 ADU documents | Bounded scoping acceptance complete | [Report](2026-09-16-adu-58-counties.md); 58 inventory rows, 46 unincorporated-county source URLs (36 opened, 10 search-only), 11 unverified applicant-page searches, one separate SF scope exception; three actor-level sketches |
| P5 environmental health | Partial, released with gaps | [Report](2026-09-16-county-environmental-health-58.md); 58 LAMP inventory rows, 48 listed/historical approvals, three septic sketches; 16 well-instruction sources, 24 food plan-check sources and seven grading systems checked |

P0 permit timing was already owned by another session and was not duplicated or
modified. Its [report](2026-09-16-apr-permit-timing.md) and data were read as an
input. CCW, forums, covariate gaps, discretion and W2-spec work is also being
tracked by other owners in the shared log; this document does not claim their
results as this pass's work. General Assistance and the other-statute sweep
have since posted separate handoffs; the audit and new retrievals below qualify
some of their completeness and absence claims without overwriting their files.

## New source targets retrieved in the continuation

Each target has its own cached originals, source-state notes and hashed catalog.
“Complete” here means the bounded retrieval was completed, not that all desired
observations exist or that statewide coverage was achieved.

| Target | Material now retained | Main limitation |
|---|---|---|
| [N1 IHSS timing](2026-09-16-ihss-timing-target.md) | State Auditor county application/approval and approval/service tables for 2015 and 2019; selected June/July 2026 CDSS workbook fields | Completed-cohort selection; unresolved denial-bin/reporting-window labels; current workbook is not a mean approval-time panel |
| [N2 assessment appeals](2026-09-16-assessment-appeals-target.md) | Four BOE tables, each 696 county-year rows for FY2013–14 through FY2024–25: appeals filings, dispositions, assessor positions and budgets; two annual reports and Alpine/LA examples | 58 county slots do not imply 58 reporting counties; latest report has 48 reporters; stocks/flows, negative-count anomaly and missing cells retained; no case durations |
| [N3 Medi-Cal application timing](2026-09-16-medical-application-timing-target.md) | Official June 2026 announcement, exact CY2025 performance-workbook link and ACWDL clock/cohort definitions | Workbook download returned a challenge page: zero numeric application-timing rows verified, not “no published dataset” |
| [N4 agency workload](2026-09-16-agency-workload-target.md) | Historical CWS time-study summary, five program means, expense-claim measurement instructions, and actual five-year IHSS administrative spending for four counties plus statewide | CWS is not IHSS; statewide means are not county-specific labor observations; hours, random-moment observations and allocated costs differ |
| [N5 permitting labor](2026-09-16-permit-labor-target.md) | Four county cost/workload studies plus San Mateo billing context; ten originals, including Contra Costa's office/travel/technical-hour breakdown | Time-record-based estimates, expert standards and retainers are different source types; no raw worker-log panel or uncertainty estimates |
| [N6 workload methods](2026-09-16-workload-detail-target.md) | SB2030 main report pages 1–166, front matter and references; five primary-worker program aggregates and eight travel mean/median rows by staff role and county staffing-size group | Same study as N4, not independent replication; primary-worker means differ from all-staff totals; adjusted monthly means and travel-conditioned worker totals are not raw task durations |
| [N7 CalWORKs counts](2026-09-16-calworks-target.md) | Four current workbooks: CA237CW caseload and CA255CW denial reasons, each covering 58 counties × 13 months through July 2026; reporting definitions and historical timing instructions | No current elapsed-time or pending-age fields; 44,229 suppressed county cells; negative adjustment fields are not invalid negative caseloads |
| [N8 state hearings](2026-09-16-state-hearings-target.md) | Two CDSS annual activity reports plus latest Q4; CDII MY2023 report/tables/methods with 16 elapsed-time means and selected county complaint ratios (30 DHCS, 15 Covered California counties); 12 originals | Closed-case means, not county durations or worker hours; overlapping publications; two CDSS count differences and conflicting CDII display thresholds preserved |
| [N9 appeals capacity](2026-09-16-appeals-capacity-target.md) | Five more BOE tables, each with 696 county-year slots: boards/hearing officers, temporary positions, property transfers, new-construction workload and business-property audits | Nonreporters sometimes have raw No/zero values; fiscal/assessment years differ; arithmetic and narrative contradictions retained; no case times or labor logs |
| [N10 wide-net continuation](2026-09-16-wide-net-retrieval.md) | Sonoma and San Diego County permit-event exports, government-unit employment files and Alameda interdepartmental process/review documents | Duplicate identifiers, reversed dates and stale feeds; headcounts are not FTE; review cohorts overlap; broader retrieval remains incomplete |
| [N11 user-evidence enrichment](2026-09-16-county-user-evidence-enrichment.md) | Existing Reddit sweep confirmed; 14 targeted reply snapshots (117 IDs, 92 newly retained), seven other-forum pages and eleven county/advocacy document sources, including interview estimates and staff scripts | County-sweep program totals are unfiltered search yields; replies have mixed counties, clocks, cases and evidence roles; no verified 58 × program coverage matrix |

These are additions to the source inventory, not an unreviewed change to the
other session's W2 program selection. In particular, labor evidence is now more
concrete, but its availability does not establish that an intrinsic agency
effect can be separated from task mix, service standards and source methods.

N6 corrected an interpretation inherited from the SB2030 executive summary:
13,584 staff and 1,140,667.6 recorded hours include primary, non-primary and
administrative-only roles, not exclusively case carriers. Its five headline
program means concern primary workers and use report/referral/case denominators
with adjustments. The N4 report now points to those refined definitions; original
source tables and hashes remain preserved.

The completed P5 continuation corrected stale approval dates, including
San Mateo's March 28, 2022 approval. Only two full current LAMP versions were
checked. Its two actual 2026 rural food-inspection examples and one weekly
three-record well report are useful outcome documents, not a complete case-time
panel. Rural superiority in evidence volume remains unestablished.

## Independent audit follow-up

The [cross-scoping audit](2026-09-16-cross-scoping-audit.md) records the checks,
source links, reproduction artifacts and cautions sent to the other owners:

- HCD's application date means **complete application** when the initial filing
  was incomplete. Parcel identifiers do not uniquely identify projects; the
  earliest-parcel join has linkage and cohort-selection problems. On the same
  90,845 eligible ADU rows, the comparison median changes from 150 to 140 days
  with a stricter tracking-ID/date linkage. Neither linkage is declared gold.
- All **894,381 exported CalFresh cells** checked against the eleven cached
  workbooks matched, extending the initial 200-cell spot check. Source errors,
  suppression and reporting limitations remain; extraction fidelity does not
  make the reported outcomes error-free.
- USDA's actual 2024 noncore classification gives **11**, not the 15 obtained
  by relabeling RUCC ≥6. The correct join is saved separately; the shared
  covariate table was not silently overwritten by this pass. Its owner has now
  applied the correction; all 58 UIC/noncore values were independently checked.
  Local-government QCEW counts
  are not county-agency staffing counts.
- Reproduced descriptive correlations do not identify discretionary choice,
  platform effects or queue mechanisms. WAF failures do not identify why a
  county publishes less. Cross-program and capped-versus-uncapped contrasts
  still have confounding and measurement differences.

The audit also flags partition/leakage and clock issues in the draft W2 plan.
It is evidence for revising the experiment, not a claim that this retrieval
pass implemented those revisions.

The subsequent [P12 spot-check](2026-09-16-p12-independent-spotcheck.md) confirms
the rurality and main APR clock repairs, but finds three substantive problems in
the new generator/scorer: a reversed statutory floor; prediction-dependent
planted histograms when criteria are missing; and a distinct-reading contrast
that can give the modal-everywhere predictor zero error at 58 jurisdictions.
Those findings were sent through the shared log, without modifying model code.
The review also retains legal-exception and causal-identification cautions.

## Findings that change the scale-up assumptions

1. **There is real county timing variation to model.** CalFresh offers both
   binned counts and conditional mean approval times. It is not just a collection
   of statutory deadlines. The common platform has not made reported county
   outcomes identical. The P1 report separates that observation from any causal
   claim about the rollout or intrinsic agency efficiency.
2. **The extra data need different measurement types.** CF 296 expedited bins
   concern benefit issuance, while CF 18 means concern initial approval, sometimes
   starting at discovery rather than application. Overdue counts can be explicitly
   county-error-attributed. Do not collapse these into one “days” field or count
   their overlapping populations independently.
3. **Published does not mean clean.** CalFresh has suppression, missing months,
   `#REF!` cells, zero-coded reporting limitations, form changes, and statewide
   means that numerically match unweighted county averages. Provenance and flags
   now preserve these distinctions. An official source is not an error-free
   measurement channel.
4. **A 58-row inventory is not 58 observed processes.** ADU has a substantial
   county source layer, but search hits, opened pages, linked PDFs and current
   operative procedures are different evidence levels. San Francisco also cannot
   be assigned a fictional separate unincorporated-county workflow.
5. **The assumed guaranteed LAMP corpus does not exist on that basis.** Tier 1
   is available without a LAMP; Tier 2 is the approved local-program route.
   Reporting obligations do not guarantee observed public reports. Rural process
   evidence exists, but a rural advantage in evidence volume is not established.

Primary-source URLs and dated citations are retained in the linked packet
reports. No absent search result is coded as a nonexistent program or zero burden.

## Implications for the Bayesian question

These outputs improve the proposed experiment's inputs; they do **not** yet
demonstrate improved Bayesian performance. No new Bayesian fit, synthetic render,
held-out score, or LLM-versus-Bayes comparison was run by this pass.

The hierarchy still has to earn its parameters. More scalar cells do not imply
more independent cases, and many counties do not by themselves separate county,
agency class, task, platform, applicant mix and source effects. The next design
needs crossed tasks/programs and an identification check using the actual
observation pattern, including missing channels. Timing-only evidence must not
be presented as learned payer or agency labor hours.

Process documents remain necessary to constrain step inventories, responsibility,
dependency/parallelism and correction loops. Administrative timing tables then
constrain the corresponding clocks. Source lineage and overlapping summaries
must prevent double counting. Use the existing V6 integration target, not another
parallel model architecture.

## Next execution gates

1. **Reconcile source readiness with the proposed program selection.** Use
   the completed packet handoffs and new targets without mistaking inventory
   rows for observed county processes. Complete P5's remaining well/food checks
   only where the selected programs need them, or explicitly revise its scope.
   The blocked Medi-Cal workbook remains a concrete retrieval target.
2. **Resolve the audited measurement issues before declaring external ground
   truth.** The APR dictionary/linkage audit is now complete; clock origin,
   linkage, selected-case coverage and city-versus-county scope need explicit
   decisions in the data design. Weak marginal correlations do not establish
   policy-choice causes; missing or coincident entitlement dates do not
   establish a route by themselves. Labor inputs now require an equally explicit
   distinction between records, edited averages and normative estimates.
3. **Freeze W2's design and partitions.** Choose the programs; encode observation
   types, shared task keys, local structural hypotheses, publication/fetch
   missingness and source families. Pin dates and freeze calibration/development/
   reserved county partitions before rendering and calibration.
4. **Calibrate, fit, then test transfer.** Measure semantic ambiguity accuracy on
   calibration data; use calibrated mixtures where needed. Fit the identified
   V6 hierarchy on development data, with every fit's identification report and
   prior-sensitivity checks. Freeze the system before the reserved comparison.
   Give the LLM baseline the same available cross-county evidence; it is not
   inherently incapable of transfer. Compare calibration, interval scores and
   held-out timing/count predictions, not just an in-sample point estimate.

## Verification and boundaries

CalFresh extraction validates county grids, cell inventories, unique keys,
publication states, source hashes and numeric ES-bin sums. The later independent
audit round-tripped all 894,381 exported cells to original workbooks. All 24 inspected statewide
CF 18 timing means match the unweighted county average numerically; 11 differ
from bin-count-weighted county means by more than one day. These are data checks,
not sampler validation or proof that the underlying reports are correct.

P3/P5 record source-access failures, evidence levels, budgets and remaining gaps.
An offline CalFresh conversion helper and independent source-audit artifacts
were added earlier. After Alex redirected the effort to retrieval, no additional
unit tests were added or run. N1–N7 cache sources and preserve their limitations.
The N4 time-study counts, table and special two-week intake footnote were checked
against the original PDF, not only the agent's summary.
All 254 P5, 17 N4 and 16 N5 cataloged file hashes were independently rechecked.
The later N6/N7 continuation checked another 28 and 12 cataloged files, respectively.
That establishes cache integrity, not the truth of every source claim.

No production model/generator changes, repository restructuring, Git commit,
account creation or outreach was performed by this pass. Other sessions' work
must not be attributed to this retrieval continuation.
