# County user-evidence and document enrichment

2026-09-16, packet N11-COUNTY-USER-EVIDENCE. Requested continuation focused on
Reddit replies, non-Reddit forums, county FAQs and unofficial process guides.
Budget: 24 search queries and 50 distinct public source fetches. No model edits
or unit tests. This is targeted enrichment of prior retrieval, not a new claim
that Reddit had never been swept.

## Existing collection checked first

- `corpus/counties/reddit_coverage.csv`: 1,298 county/program/query rows.
- `corpus/counties/reddit_raw/`: 1,047 JSON responses, 355 nonempty, containing
  4,664 distinct post IDs; no embedded reply bodies in these response files.
- Older full-comment collections: ADU 170 post files / 4,344 comments;
  CalFresh 143 / 1,431; food-facility 285 / 3,758. These are file-level counts,
  not deduplicated independent cases or verified county-level observations.
- The non-Reddit sweep already located county CalGuns threads and other venues.
  Its cached thread index is reused to retrieve specific useful discussions.

Important coverage qualifier found on inspection: the county sweep's regional
and statewide searches can query only the county name. The same cached result
is then entered under several program rows without a program-content filter.
Thus the summary's program totals/counties-with-any are **search yields**, not
verified program-by-county evidence coverage. A time-word match is likewise not
a validated administrative duration. Original outputs remain untouched.

## Enrichment rules

Use existing post IDs before spending new searches. Retrieve replies for
process-rich threads; separately target program venues absent from the first
sweep (notably IHSS). Keep post versus comment identity, dates, reply structure,
same-author/case relationships and source URL. An archive is a snapshot, not a
promise of every live comment. Deleted/unavailable bodies stay unavailable.

Attribute county and program at the individual statement level: a commenter in
an LA thread may describe Riverside or Ventura, and living in a county does not
prove the county rather than a city administered a permit. Staff-role claims
are self-reports, not verified credentials. Do not infer private identities or
profile users; summarize process facts without unnecessary health/financial
details. Repeated posts, quoted replies and copied advice are not independent
cases. Service hours awarded by IHSS are not hours spent administering a case.

Store originals/API snapshots, readable excerpts, reviewed source entries and
hashes in `corpus/counties/raw/county_user_evidence_target/`. Distinguish a
search-only hit, a retrieved reply, a reviewed process claim, and a current
official or unofficial guide. Never label an unsearched/unreachable cell zero.

## Findings

The bounded pass is complete: **24 search queries, 36 distinct source URLs
attempted**, within the 24/50 budget. URL count includes archive endpoints and
browser page opens, deduplicated across retrieval methods; it excludes the
many unvisited links returned by search. This is not exhaustive 58-county
coverage.

The [reviewed source ledger](../../corpus/counties/raw/county_user_evidence_target/reviewed_source_ledger.json)
has **32 entries**: 14 Reddit threads, seven other-forum pages, and eleven
official/advocacy document sources. The
[manifest](../../corpus/counties/raw/county_user_evidence_target/MANIFEST.json)
records originals, derived copies, reused dependencies, hashes and failed
retrievals. Search-result caches are retained as discovery evidence, not silently
promoted to complete page retrievals.

### Reddit: reuse plus targeted replies

The fourteen archive responses contain **117 distinct comment IDs**, 116 with
available bodies and one marked removed. Comparing IDs against the older
`corpus/realworld/**/reddit/posts/` collections found **25 already cached IDs**
and **92 newly retained IDs** (91 available bodies, one removed). These are
records, not 92 independent cases. Six parents were recovered from the existing
county cache; another selected parent was already in the food-facility corpus.
The other parent accounts are retained through browser/search snapshots.

| Target | New detail / correct interpretation |
|---|---|
| IHSS, Riverside | [Dated March–June 2026 sequence](https://www.reddit.com/r/IHSS/comments/1u0ezyl/timeline_of_the_whole_process/): March 6 application, April 22 assessment, April 30 NOA, May 27 provider orientation/timesheets, June 1 payment. These imply 47, 55 and 87 elapsed calendar days to assessment, NOA and payment respectively; exclude the starting day. They are not worker hours. |
| IHSS, Kern | [Explicit 2024 case in a newer thread](https://www.reddit.com/r/IHSS/comments/1vzcq8a/anyone_applied_ihss_in_bakersfield_ca_kern/): intake, home assessment, provider requirements, NOA, linking and backpay are separate milestones. The OP's newer provider number does not imply recipient approval. |
| IHSS, Fresno / San Diego | [Replies in one thread](https://www.reddit.com/r/IHSS/comments/1wi8ys1/hi_everyone_how_long_does_the_process_take_after/) describe a four-month Fresno **initial approval** and a San Diego **annual reassessment**. Other replies do not name a county. |
| IHSS, LA / Riverside / Ventura | [Mixed-county thread](https://www.reddit.com/r/IHSS/comments/1sb1uoq/assessment_was_conducted_last_month_and_i_havent/) contains same-case followups, delayed NOAs and a claimed worker→supervisor handoff. Two Ventura comments are one author's case; two Riverside comments are another's, not four cases. Staff identity and disputed deadline/backpay claims remain unverified. |
| IHSS, Contra Costa | [OP is still waiting for a home assessment](https://www.reddit.com/r/IHSS/comments/1w6lknh/in_home_assessment_appointment/). A long-wait reply does not explicitly confirm its own county. The pending case is not a completed duration. |
| CalFresh, LA | [Applicant's 1.5-hour hold ending in hangup](https://www.reddit.com/r/foodstamps/comments/19a636h/calfresh_told_me_to_call_them_for_an_interview/) is phone waiting, not interview service or approval time. Replies include Ohio and New York; do not inherit OP geography. |
| CalFresh / CalWORKs, San Diego | [Interview-duration discussion](https://www.reddit.com/r/foodstamps/comments/142yzq7/calworkscalfresh_phone_interview/) includes an explicitly San Diego staff-role claimant's 20-minute–2+ hour range and another, unspecified-county claimant's 30-minute–2-hour range plus scheduled blocks. Claimed work roles are not verified task logs. |
| General Relief, San Diego | [45-minute interview, external verification and rejection loop](https://www.reddit.com/r/foodstamps/comments/1i1r4vu/san_diego_general_relief_application_process/). A later same-author reply reports acceptance and then a new application. Do not fit the two applications as one long case. |
| Medi-Cal, Santa Clara context | [Pending application and callback reports](https://www.reddit.com/r/SanJose/comments/1d2phr2/). A 45–60-day reply is a forecast; a callback is not approval; a separate reply's county is not explicit. |
| CalFresh, Riverside; Contra Costa→Santa Clara | [Income-proof rejection](https://www.reddit.com/r/foodstamps/comments/1w6b5o7/applying_for_calfresh_while_self_employed/) and [move/reapplication questions](https://www.reddit.com/r/foodstamps/comments/1hi5dk6/calfresh_application_questions_after_moving_to/) illustrate correction and jurisdiction ambiguity, but their ten replies were already cached. |
| Food-trailer plan check, Southern California | [Rejected self-drawn plans and $1,000 drafting quote](https://www.reddit.com/r/foodtrucks/comments/1tcbvxe/permit_plans/); county unknown, quote not paid cost. A generic reply names five counties but supplies no five-county case sample. |
| Food-trailer paperwork, San Diego | [Cross-city/county/state questions](https://www.reddit.com/r/foodtrucks/comments/1rulzna/paperwork_needed/); all thirteen replies already cached. Commercial advice, possible expansion to LA and vehicle purchase costs are not verified local process measurements. |
| ADU, Santa Clara | [Contractor-referral thread](https://www.reddit.com/r/bayarea/comments/16i5ah5/how_to_get_adu_permit_santa_clara_county/); both comments already cached, no timing outcome. Retained as a negative usefulness check. |

An especially useful topology example: the Riverside OP reports being told to
wait for recipient approval before provider enrollment, while a different-county
staff-role claimant recommends starting orientation earlier. This motivates
conditional route hypotheses; it does **not** establish a universal serial or
parallel rule. The retrieved Humboldt registry instructions address providers
without a recipient in mind and explicitly route other providers elsewhere.

### Other forums

Seven pages retained, with **84 body records / 83 nonempty bodies** in the
readable extracts: CalGuns 33/32, Permies 27/27, BiggerPockets 24/24. This counts
OPs, replies and quote-containing posts; it does not remove quoted duplication
or establish independent cases. No matching URLs were found in the earlier
forum `.meta.json` files; the existing CalGuns index was reused for discovery.

- **CalGuns:** Madera, Alpine, Trinity and Colusa threads. The Madera account
  reports April 2 interview/fingerprinting to May 12, 2021 ready-for-pickup call
  (40 calendar days). The other threads mostly supply historical policy/link
  discussions. Retrieved posts date from 2010–2021; old eligibility language is
  not a statement of current law. One Madera OP body is empty.
- **Permies:** two composting-toilet/septic discussions from 2019/2020. One
  names Humboldt and several rural neighbors; another begins in Washington and
  has multi-state replies. Mentions and recollections are not verified county
  policies. A building-permit story in a septic thread is not a septic-only
  duration. Advice about evading requirements is retained as source context,
  not endorsed or used as authoritative process evidence.
- **BiggerPockets:** a Claremont ADU project narrative, with permitting November
  2022–June 2023 and subsequent same-project updates. **City of Claremont**, not
  Los Angeles County, is the permitting comparator. JSON-LD exposes the OP plus
  23 replies, although metadata says 29 comments; this is an incomplete snapshot.
  The readable copy omits the residential street address.

Direct URLs and post IDs/dates are in the source ledger and per-forum extracts.

### County and unofficial process documents

| Source retained | What it adds; what it does not measure |
|---|---|
| [Humboldt General Relief info sheet](https://humboldtgov.org/DocumentCenter/View/55857/I-13-32-Info-Sheet---General-Relief), November 2024, 2 pages | Published 1.5–2-hour interview estimate; location-specific interview access and cross-program referrals. Not a sampled duration distribution. |
| [Humboldt GR/CalFresh interview script](https://humboldtgov.org/DocumentCenter/View/136776/I-18-16-GR-and-CF-Rights-and-Responsibilities-Script-PDF), December 3, 2024, 4 pages | Back-end explanation, verification, signatures, reporting and renewal steps. Program-specific clocks and historical legal conditions must stay separate. |
| [Santa Clara staff interview handbook](https://stgenssa.sccgov.org/debs/program_handbooks/calfresh/assets/CalFresh/Application/SchedIntrvw.htm?agt=index&f=Audience%3AIncome) | Scheduling, case-file documentation, missed-interview notices and home-visit branch. Normative instructions, not observed staff time. |
| [Sutter CalFresh page](https://www.sutter.gov/government/county-departments/health-and-human-services/employment-and-eligibility-services-branch/calfresh-program) | Applicant route through submission, interview, verification, NOA and EBT; recertification is separate. Browser text retained after direct HTML request returned 403. |
| [Humboldt IHSS provider enrollment](https://www.humboldtgov.org/3747/IHSS-Provider-Enrollment) | Registry-specific BOUNDS, videos, orientation and Live Scan sequence; monthly appointment release, 24-hour email follow-up and 90-day enrollment window have different semantics. |
| [Humboldt IHSS eligibility](https://humalertca.gov/508/IHSS-Eligibility) | Recipient application/home-visit/provider-choice route, distinct from provider registration. Browser text retained. |
| [Shasta IHSS packet](https://www.shastacounty.gov/media/58611), browser-readable 13 pages | Applicant/medical forms, social-worker assignment, home visit and NOA. Its normal 30-day expectation is not an empirical mean. PDF download returned 403; no original PDF is claimed. |
| [Trinity food plan checklist](https://www.trinitycounty.org/DocumentCenter/View/1579/Food-Facility-Plan-Checklist-PDF), 5 pages | Environmental Health, Building/Planning and water/sewage coordination; completeness and inspection. Undated listed fees are not certified current. |
| [Modoc food application](https://webgen1files.revize.com/modocenvironmental/Food%20Sanitation%20Program/Operate%20a%20Food%20Establishment%20Permit%20Application.pdf), 1 page | Facility class, plan-check flag, menu, certification and three approval fields. Form fields are not automatically separate completed tasks. |
| [Disability Rights California IHSS guide](https://www.disabilityrightsca.org/publications/ihss-in-home-and-self-assessment-guide), December 1, 2025 | Unofficial assessment/NOA/appeal explanation. Awarded care hours are **not** administrative work hours. |
| [Legal Services of Northern California interview guide](https://calfresh.guide/the-interview-process/) | On-demand/scheduled interview, verification and missed-interview loops with citations. Normative rules and mixed program references require attribution/version checking. |

The 11 document entries comprise eight original downloads and three browser-only
sources. The originals include four PDFs (12 pages total) and four HTML files.
The Shasta packet is additional browser text, not part of that PDF/page count.

## Implications for generation and extraction

1. Generate thread-level **and statement-level** place/program/actor ambiguity;
   do not equate a regional subreddit or generic county query with a verified
   county-administered process. Include city comparators and unknown counties.
2. Preserve parent/reply links, same-author followups, quoted advice and distinct
   applications by the same person. More text need not mean more cases.
3. Model observation endpoints explicitly: applicant submission, completed
   packet, assessment, approval call, NOA receipt, provider enrollment, account
   linking, payment. Include incomplete and abandoned waits.
4. Keep scheduled blocks, realized service, phone holding, forecast/deadline,
   awarded care hours, quoted costs and administrative labor distinct.
5. Include published applicant guides and worker-facing scripts, without making
   unmeasured agency labor or intrinsic agency delay identifiable by fiat.
6. Do not calibrate synthetic per-program forum availability directly to the
   unfiltered county sweep summary. First deduplicate and review jurisdiction,
   program relevance, case identity and retrieval selection.

These examples inform document/observation design; they do not establish county
population means or empirically calibrated source-error distributions.

## Remaining gaps

There is no verified 58 × program forum-coverage matrix. Small-county mentions
are still mostly advice or old policy discussions, not observed modern cases.
Some useful parents are search-snapshot-only; live-thread and older archive
completeness remain unknown. The bigger statewide quantitative gaps in the
[retrieval handoff](2026-09-16-county-scale-execution.md) also remain, including
the inaccessible Medi-Cal timing workbook and sparse direct agency labor data.
No log-in, paid API, private material or access-control bypass was used; no
model, generator, collection code or tests were changed for this pass.

Final integrity check: all 65 manifest-listed local files and ten reused source
dependencies matched their hashes; every ledger file existed, all 117 comment
IDs were unique, new/overlapping/body-availability counts reconciled, and all
60 relative links across this report, the retrieval handoff, generation plan
and new raw-directory README resolved. These are storage/count checks, not
validation of the commenters' accounts or the currentness of legal rules.
