# Exhaustive county retrieval: scope and completion criteria

2026-09-17. Packet N12-EXHAUSTIVE-RETRIEVAL. Alex explicitly requested
exhaustive coverage after the N11 targeted increment. The earlier per-packet
query budgets are **not** this workstream's completion rule. N11 remains an
accurate record of one increment, not a completed retrieval census.

## Scope

Cover all 58 California counties, with San Francisco's consolidated city/county
scope explicit. The operational program list is the union of the existing
county retrieval work and the proposed synthetic-corpus families:

1. ADU permitting/legalization (county unincorporated jurisdiction; SF separate).
2. General building permits (kept distinct from ADUs).
3. Food-facility and mobile-food approval.
4. Septic/onsite wastewater approval, including Tier 1 versus LAMP routes.
5. Well construction approval.
6. CalFresh.
7. Medi-Cal application and renewal, with different clocks.
8. General Assistance/General Relief.
9. IHSS recipient and provider routes.
10. CalWORKs.
11. CCW licensing/renewal.
12. Property assessment appeals.
13. Elections/mail-ballot processing and cure.
14. Agricultural restricted-material permits.

This is **812 county–program pairs**, not a change to the synthetic generator's
program selection. Each pair tracks six source channels: applicant-facing
official instructions, official policy/staff/oversight material, administrative
data, Reddit, other forums, and advocacy/other explanatory sources. Staff
perspective is an additional source role, not assumed from a website category.

For dated user accounts, the initial common window is September 1, 2022 through
September 17, 2026, extending the existing sweep's start date. Preserve earlier
material already collected and older versions needed to interpret a current
process, but report them separately. Official instructions are checked for the
current route and available historical versions; statistical-series coverage
is recorded by actual years/months, not silently restricted to the forum window.
Indexes must be checked even when an older thread's initial date predates the
window: it may contain recent replies.

## What exhaustive means operationally

The open web cannot support a proof that no unknown document exists. The
deliverable is an auditable public-source census within this scope, with known
sources and paginated results followed through, not a sample that stops after
a fixed number of searches. Do not call it complete while protocol steps or
known relevant links remain unchecked. Access-restricted/private material is
listed as unavailable, not bypassed and not counted as absent.

For every pair:

- Follow official state/association directories to the responsible county or
  delegated authority; distinguish a city, district and county administrator.
- Check the program landing page, linked FAQs, forms, checklists, fee schedules,
  ordinances, staff manuals and available historical versions. Follow substantive
  linked documents rather than counting the landing page as all these sources.
- Check published datasets, agency reports, audits, county legislative records
  and grand-jury report indexes for the program. Count relevant titles and
  covered periods; a report-producing institution is not a report on every
  program, and a renewal dataset does not close application-timing retrieval.
- Search county/city-seat aliases jointly with program synonyms, in relevant
  program and regional Reddit venues. Generic county hits are discovery only.
  Paginate or date-split capped archive queries; preserve failed queries.
  Retrieve relevant comment trees, not only original-post snippets.
- Search non-Reddit forums and explanatory/advocacy material using the same
  county/program scope. Business applicants do not make agricultural-permit
  user evidence automatically out of scope; voter-facing county instructions
  are not excluded merely because some rules are statewide.
- Resolve duplicate URLs, copied versions, post/comment IDs, same-case reports
  and overlapping cohorts. Review county/program attribution per statement.
  Separate observed durations, forecasts, normative clocks, care-service hours,
  work hours, paid fees and quoted costs.
- Reconcile every attempt and known link into the coverage ledger. Preserve
  `not_yet_checked`, `located`, `retrieved_unreviewed`, `reviewed`, `blocked`,
  and `searched_not_located` as different states. No empty cell means zero.

One reviewed source does not close an entire source channel. Report completion
of each search/index/link-following step separately from documents found and
from whether a burden estimand is actually measurable.

## Execution and evidence preservation

Start by reusing the existing corpus and structured inventories. Keep originals
unchanged; retain new originals, response metadata, query details, timestamps
and hashes under `corpus/counties/raw/exhaustive_2026_09_17/`. All derived files
identify their inputs. Coverage files belong to this workstream; other agents'
source-volume and closure files are not silently rewritten.

Use modest concurrency and respect rate limits. A 429 is a pause/backoff signal,
not a reason to evade the service or turn the result into an empty list. Use
cached directory bytes and documented public alternatives while a host is
unavailable. Login, purchases, outreach and access-control bypass are not part
of the current authorization.

Work proceeds across continuations until the checklist is covered or specific
external blockers require user action. An interim handoff must list remaining
work and keep this packet open; it must not equate a completed increment with
exhaustive coverage. Retrieval completeness and sufficient information for
Bayesian identification are different questions.

## Working ledgers

- [Progress and spot checks](2026-09-17-exhaustive-retrieval-progress.md): dated
  retrieval increments and remaining pagination, relevance and access gaps.

- [Coverage matrix](../../corpus/counties/exhaustive_coverage_matrix.csv): 4,872
  county–program–channel rows. Every channel starts open. A blank lead count
  means unreconciled inventory, not an absence of evidence.
- [Matrix metadata](../../corpus/counties/exhaustive_coverage_metadata.json):
  program definitions, legacy inventory pointers and remaining reconciliation.
- [Known leads](../../corpus/counties/exhaustive_known_leads.json): references
  imported from P5, N11 and P3/P1, plus qualified county-forum and ADU follow-ups,
  with their qualifications preserved; not the whole
  corpus and not new independent observations.
- [Oversight link catalog](../../corpus/counties/raw/exhaustive_2026_09_17/grand_jury_link_catalog.jsonl):
  discovered URLs, source indexes and unverified headings. Keyword hints are
  discovery aids, not program or jurisdiction labels. Generic-title consolidated
  reports also require review; title matching cannot complete this channel.
- [Reddit comment discovery queue](../../corpus/counties/raw/exhaustive_2026_09_17/reddit_comment_discovery_queue.json):
  candidate IDs from the earlier county cache, prior comment-snapshot references
  and literal county mentions. A county mentioned in an OP does not establish
  the county of each reply. Neither the keyword filter nor its complement is a
  reviewed relevance judgment. Existing capped/failed searches still need their
  own follow-up; this queue only exposes gaps within already retained posts.
