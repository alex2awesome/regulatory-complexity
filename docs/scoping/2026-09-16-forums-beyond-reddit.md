# Forums beyond reddit: where else people describe county processes

Packet **P7-FORUMS-BEYOND-REDDIT** (workstream A9 of the
[county scale-up plan](../2026-09-16-county-scale-up-plan.md)). Written
2026-09-16 by the forums agent.

**The question.** The covariate table found that forum *channel existence*
scales with county population (r = 0.741 between the number of plausible county
subreddits and log population), and that nine counties — Alpine, Amador,
Calaveras, Colusa, Glenn, Mariposa, Modoc, Sierra, Trinity — have no candidate
subreddit at all
([county covariates](2026-09-16-county-covariates.md#3-forum-availability-scales-with-population-r--074)).
If reddit is the only venue we measure, the disappearing-commons claim is a
claim about reddit. This packet asks which other venues carry process evidence,
and specifically whether any of them **fill the rural gap**.

**The short answer.** Yes, one family does, decisively: **civil grand jury
reports**. They are mandated by Penal Code §§ 925–933.05 rather than produced by
a market, so they exist in the smallest counties, and they carry exactly the
material the project wants — vacancy counts, step sequences, statutory response
clocks, and explicit findings that a process is undocumented. Seven of the nine
no-subreddit counties post directly downloadable reports, an eighth posts them
behind a JavaScript widget, and only one posts none at all and answers report
requests by email. The staff-side review sites (Glassdoor, Indeed) are the only
staff-only process evidence available anywhere, but they are login-walled to
scripts and urban-skewed. Government-office reviews (Yelp, Google) are
bot-blocked to scripts and need either an API key or a browser.

## Method and its limits

**WebSearch was exhausted (200/200) before this packet started**, so nothing
here was found by web search. Everything was reached by (a) direct URL, (b)
on-site search endpoints, and (c) per-site index pages. Two search fallbacks
were tried and both failed, which is itself a retrieval finding:

- `https://html.duckduckgo.com/html/?q=...` and `https://lite.duckduckgo.com/lite/?q=...`
  return **HTTP 202** with a bot-check page, both GET and POST.
- `https://www.bing.com/search?format=rss&q=...` returns **HTTP 200 and parseable
  RSS**, but ignores `site:` and quoted-phrase operators: the query
  `site:avvo.com ADU Trinity County California` returned fresno.gov and hcd.ca.gov
  pages. It cannot be used to count anything.

So every count below is either an on-site result count quoted by the site
itself, or a count I made by hand from a fetched page. Where I could not count,
I say how a real harvest would. Raw bytes for every fetch are cached under
`corpus/counties/raw/forums/` with a `_fetch_log.jsonl` recording URL, HTTP
code, byte count and redirect target for each.

## Spot-check scoreboard

The packet named four spot checks. Two produced clean numbers, one was
half-answered, one was blocked and substituted.

| Spot check | Status | Number |
|---|---|---|
| Grand jury availability for the nine no-subreddit counties | **done** | 9/9 landing pages HTTP 200; **7/9 post reports downloadable by plain HTTP** (8/9 counting Calaveras, whose index is a JS widget); 5/9 machine-readable without OCR; only Amador posts none (email only) |
| CalGuns: San Bernardino versus Alpine CCW thread | **done** | **9,307 posts versus 15** (620:1); 58/58 counties have a thread; nine no-subreddit counties hold 212 of 71,065 posts (0.3%) |
| Avvo ADU questions, large county versus Trinity/Alpine | **blocked**, substituted | Avvo is behind a Cloudflare JS challenge (403 to curl and to WebFetch). Substitute on City-Data: "accessory dwelling unit Sacramento" **2 threads**, Trinity **0**, Alpine **0** |
| Yelp/Google reviews, LA DPSS versus a tiny county office | **half** | Google Maps HTML **confirms the place entity "Modoc County Social Services" exists**; review counts are JS-only and Yelp returns 403, so counts are not verified |
| Glassdoor large versus small county employer | **blocked** | 403 "Humans only" on every Glassdoor URL and 403 "Security Check" on every Indeed URL, via curl and via WebFetch; Wayback was offline. Comparably, the scrapable competitor, reports **0 participants and 0 rating** for County of Los Angeles |

Retrieval totals for the session: **139 fetches, 99.5 MB cached** — 105 × HTTP 200,
20 × 403, 6 × 404, 6 × 500 (Legistar clients that do not exist), 2 × connection
failure; 12 report PDFs downloaded and converted with `pdftotext -layout`.

## 1. Civil grand jury reports — the rural-gap answer

Every California county impanels a civil grand jury annually (Penal Code §§ 888,
893, 914) and must publish a final report; agencies must respond within 60 days
(department heads and elected officials) or 90 days (governing boards) under
§ 933.05. The obligation does not scale with population, so the supply of
documents does not either. This is the structural difference from every
market-driven venue in this document.

### Discovery route

`https://cgja.org/websites/` is a **single page listing a grand jury site URL for
all 58 counties** — the cheapest possible seed list for a harvest. Many entries
are stale `http://` URLs, but they redirect (e.g. Alpine's
`http://www.alpine.courts.ca.gov/generalinfo/jury-grandjury.htm` →
`https://www.alpine.courts.ca.gov/jury-service/grand-jury`; Amador's
`amadorcourt.org` → `amador.courts.ca.gov`). There is **no statewide full-text
index of reports**: `https://cgja.org/search-topics/` exists but is a stub whose
only outbound link is to leginfo, and `https://cgja.org/final-reports/`,
`/reports/`, `/grand-jury-reports/` all return 404. Harvest must therefore be
per county.

### Spot check: the nine no-subreddit counties

All nine grand jury landing pages returned HTTP 200. The question is whether the
*reports themselves* are fetchable, and whether they are machine-readable.

| County | Landing page (HTTP) | Reports posted | Machine-readable? | Latest posted |
|---|---|---|---|---|
| Alpine | 200 | Yes, 2005-06 → 2016-17 PDFs | **No — image-only** (5.1 MB PDF, `pdftotext` yields 0 chars) | 2016-17 |
| Amador | 200 | **None posted.** Page offers only `mailto:webdocrequest@amadorcourt.org?subject=Grand Jury Request: [Civil Grand Jury Final Report]` | n/a | not verified |
| Calaveras | 200 | Index exists but is a DNN **DocBox** widget (`docaccess.com/docbox.js`); static HTML contains `Loading...` and zero file links | Needs headless browser or DocBox endpoint | not verified |
| Colusa | 200 | Yes, **8 reports** 2015-16 → 2025-26, direct PDFs | Yes (47.5 k chars for 2024-25) | 2025-26 |
| Glenn | 200 | Yes, **5 reports** 2021-22 → 2025-26, direct PDFs | Yes (102.6 k chars for 2025-26) | 2025-26 |
| Mariposa | 200 | Yes, FY22/23 → FY25/26 plus an archive page, DocumentCenter PDFs, each with per-agency responses | **No — image-only** (850 KB PDF, 21 chars extracted) | FY25/26 |
| Modoc | 200 (court site points to county site) | Yes, **9+ reports** 2016-17 → 2025-26 | Mixed: 2024-25 yes (49.2 k chars), **2025-26 image-only** (27 chars) | 2025-26 |
| Sierra | 200 | Yes, 2015-16, 2018-19, 2022, 2024, 2025-26 | Yes (60.5 k chars for 2025-26) | 2025-26 |
| Trinity | 200 | Yes, per-year pages 1998-99 → 2024 with reports **and** agency responses | Yes (2024 continuity report, 11.3 k chars) | 2024 |

**Verdict: 7 of 9 post reports you can download with a plain HTTP request; an
8th (Calaveras) posts them behind a JavaScript file widget; 5 of 9 are
machine-readable as posted without OCR; only 1 of 9 (Amador) posts nothing and
answers by email.** Compare
with reddit, where the channel itself does not exist for any of the nine. The
commons does not vanish in rural California — it moves into the mandated civic
record. Two caveats that a harvest must budget for: **OCR is required for
roughly a third of rural reports**, and grand juries sometimes go dormant — the
Sierra County foreperson writes that "The last Sierra County Grand Jury Report
that included the required Findings and Recommendations was in 2018-19"
([2025-2026 final report](http://www.sierracounty.ca.gov/DocumentCenter/View/11941/2025-2026-FINAL-REPORT-copy), p. 1).

### Real reports, with process content where it exists

Twelve report PDFs were downloaded and text-extracted this session, covering
**eleven counties** (Sonoma, Modoc ×2 years, Sierra, Glenn, Colusa, Trinity,
Santa Barbara, Butte ×2 years, Mariposa, Alpine). The rows below list them plus
two Sonoma titles taken from an index but not fetched, marked as such.

| County | Year | Subject | URL | Process / timing line |
|---|---|---|---|---|
| **Sonoma** | 2024-25 | *Permit Sonoma 2025: management review is a start, not an end* — an audit of the county permitting agency against AB 2234 | [PDF](https://sonoma.courts.ca.gov/system/files/grand-jury/permit-sonoma-2025.pdf) | Reproduces the department's own **average days to review by permit type, June 2023 → Dec 2024**: Building 71 days (−68%), Encroachment 49 (−55%), Grading 82 → 41 (−50%), **Septic 98 (−79%), Well 123 → 18 (−85%)**; average −67% |
| **Sonoma** | 2024-25 | same report, AB 2234 compliance audit | same | "a time-consuming manual review of more than 5,000 permit review task status records for the mont[h]s of Feb[r]uary and October, 2024 found [t]hat fewer than 20 of ~1,100 permit applications requiring plan check failed to meet the AB2234 [r]equirements. All of the failures were permits that required review by multiple depart[m]ents" |
| **Sonoma** | 2024-25 | same report, routing structure | same | "In Permit Sonoma's traditional wo[r]kflow, plan check was a serial process and each person in the queue waited to be notified that the person before [t]hem had completed [th]eir task… work in parallel and use the Accela system's workflow management capabilities"; and "(289 of 525) require no plan check" (over-the-counter path) |
| **Modoc** | 2024-25 | *Report on Social Services Staffing* | [PDF](https://www.countyofmodoc.gov/DocumentCenter/View/1536/Fiscal-Year-2024-2025-Modoc-County-Grand-Jury-Final-Report) | "approximately 16 of the 45 positions in the department remain unfilled. This is due partly to a limited pool of qualified applicants and partly due to the complexity of the application process." |
| **Modoc** | 2024-25 | *Report on Elections Procedures* | same | "The Registrar of Voters and one staff member currently manage most tasks without adequate backup." |
| **Sierra** | 2025-26 | City of Loyalton review (governance, website, permits) | [PDF](http://www.sierracounty.ca.gov/DocumentCenter/View/11941/2025-2026-FINAL-REPORT-copy) | "the jury found that no designated phone or email is identified to log any complaints. **There is no information about the building permits process or how to apply for one.**… Council meeting notes… can often take a month to be posted." |
| **Glenn** | 2025-26 | LAFCo municipal service reviews | [PDF](https://www.glenn.courts.ca.gov/system/files/general/2025-2026-civil-grand-jury-final-report.pdf) | "No publicly available schedule exists for completing pending MSRs, making it difficult…" |
| **Glenn** | 2025-26 | First 5 Glenn County | same | "the previous Director, 3.5 staff members, as well as a commissioner, resigned from their positions"; "Policies and Procedures, Financial Plan as well as their Strategic Plan were outdated, causing… a delay in receiving much needed funds" |
| **Colusa** | 2024-25 | County Animal Control; City of Colusa; jail inspection | [PDF](https://www.colusa.courts.ca.gov/system/files/general/2024-2025-colusa-county-grand-jury-report-ada-fixed.pdf) | "Officer, two Animal Control Officers, and one inmate worker. Additional staffing would provide more…"; "the Animal Control staff has seen a dramatic increase in the level…" |
| **Trinity** | 2024 | Continuity report on responses to the 2022 County Counsel report | [PDF](https://www.trinitycounty.org/DocumentCenter/View/2221/2024-Grand-Jury-Report-Continuity-Report-PDF) | "there is no continuity for future administrations to know how well the service is being [provided]"; response required "within 90 days of receipt of this report" |
| **Santa Barbara** | 2024-25 | *Unpermitted Street Food Vendors* — retail food permitting and inspection | [PDF](https://sbcgj.org/wp-content/uploads/2025/06/6.22.25-Food-Vendor-Report.pdf) | "Inspections of food carts and food trucks are expected to occur at least…"; distinguishes "licensing" (city) from "permitting" (county health) and locates the enforcement step: "the County allocate funds to hire inspectors sufficient in number to enforce existing food safety laws" |
| **Butte** | 2019-20 | Jail grievance procedure (a staff-side step sequence) | [PDF](https://www.butte.courts.ca.gov/system/files/general/2019-2020_grand_jury_report.pdf) | "Due to the multiple steps and number of staff involved, the grievance process is open to interpretation by anyone along the chain of command" |
| **Sonoma** | earlier year | *Outsourcing Petaluma Planning Department* | [PDF](https://sonoma.courts.ca.gov/system/files/grand-jury/outsourcing-petaluma-planning-department.pdf) | not fetched (title only, from the archive index) |
| **Sonoma** | earlier year | *Affordable Housing: Monitoring and Compliance* | [PDF](https://sonoma.courts.ca.gov/system/files/affordable-housing-monitoring-and-compliance.pdf) | not fetched (title only) |
| **Mariposa** | FY25/26 | Final report + responses from Elections, Sheriff, John C. Fremont Healthcare, MCUSD | [PDF](http://www.mariposacounty.gov/DocumentCenter/View/102423/FY25-26-Civil-Grand-Jury-Final-Report) | image-only PDF; subjects inferable from the response titles, contents need OCR |
| **Butte** | 2021-22 | Sheriff recruit academy, behavioural-health crisis services, library | [PDF](https://www.butte.courts.ca.gov/system/files/2021-2022_grand_jury_final_report.pdf) | "Each program is 23 weeks long"; "Crisis Triage Connect; provides a patient advocate team for 60 days to facilitate a smooth [transition]" |
| **Alpine** | 2016-17 | subject not verified — **image-only PDF** (5.1 MB, 0 characters extracted) | [PDF](https://www.alpine.courts.ca.gov/documents/alpine/GrandJuryReport2016-17.pdf) | needs OCR; the page also posts School Board, Board of Supervisors and Sheriff response letters separately |
| **Modoc** | 2025-26 | subject not verified — **image-only PDF** (1.4 MB, 27 characters extracted) | [PDF](https://www.countyofmodoc.gov/DocumentCenter/View/1594/Fiscal-Year-2025-2026-Modoc-County-Grand-Jury-Report) | needs OCR; the 2024-25 report from the same county extracts cleanly, so machine-readability varies year to year within a county |

### Volume estimate

Counted, not guessed, from fetched index pages: Butte posts **15 annual reports**
(FY2010-11 → FY2024-25) on one page; Colusa 8; Glenn 5; Trinity has per-year
pages back to 1998-99; Santa Barbara posts a consolidated report **plus 4-6
separately titled investigations per year** with a separate response PDF per
responding agency (2024-25 alone: five titled reports and nine response letters);
Sonoma's 2025-26 page lists **8 titled reports** plus per-agency responses and
Spanish translations. So the per-county rate ranges from roughly **1 report-year
document in the smallest counties to 10-25 documents per year in a large one**.
For a statewide estimate: 58 counties × ~20 years × 1-8 titled reports per year
is of order **5,000-15,000 documents**, of which the fraction bearing on permits
and benefits is the open question. I did not count that fraction and would not
guess it; the way to get it is the harvest plan in § 10, which downloads titles
first and classifies them before downloading bodies.

### Urban-rural skew

**Inverted relative to reddit.** Small counties publish fewer documents per year,
but they publish, and — decisively — a small county's grand jury spends its one
or two investigations per year on the county's *core* administrative functions
(Modoc: social services staffing, elections, jail; Sierra: the city's permit
information and roads), whereas a large county's grand jury often picks school
districts and jails (Santa Barbara 2025-26: gangs in schools, Brown Act at
school board meetings; Santa Clara 2025-26: Brown Act in Cupertino, San José's
tree canopy). The rural reports are, if anything, **more on-topic per document**
for this project.

### Access findings (record these; they set the harvest cost)

- 403 to scripted fetch: `https://www.mendocinocounty.gov/government/grand-jury`,
  `https://www.eldoradocounty.ca.gov/GrandJury/` (redirected from edcgov.us),
  `https://www.tuolumnecounty.ca.gov/386/Grand-Jury`,
  `https://www.shastacounty.gov/grand-jury`. Same wall as the State Controller
  and six sheriff sites — a browser gets through, a script does not.
- Connection failure (curl exit 6 / HTTP 000): `https://nccourt.net/divisions/grand-jury.shtml`
  (Nevada County) — host did not resolve at fetch time; "not verified", not "gone".
- **San Luis Obispo publishes its reports in a Google Drive folder**
  (`https://drive.google.com/drive/folders/17tMD-cucoU6ohpMZD7fQK7mX8hgHOkNj`) —
  needs the Drive API or a browser, not a static crawl.
- San Francisco keeps 1995-2021 reports on an archive host
  (`https://civilgrandjury.archive.sf.gov/previousreport.html`) and offers a
  **Google Custom Search Engine** over them
  (`https://cse.google.com/cse/publicurl?cx=011908603973819582131:anyccoi8dfo`) —
  the only per-county full-text search I found; it needs JS or a CSE API key.
- Even large-county PDFs are sometimes scanned-then-OCR'd with visible noise: the
  Permit Sonoma text contains "wo[r]kflow", "pe[r]mits", "dep[a]rtment". Quotes
  above are marked where I repaired an obvious OCR character.

## 2. Staff-side review sites (Glassdoor, Indeed) — the evidence we most want is the least reachable

This is the family the synthetic benchmark cares about most: staff-only steps
are currently modelled as recoverable only from leaked SOPs, and county
eligibility workers, permit technicians and environmental-health specialists
describe caseloads and internal routing in employer reviews. Nothing else in the
corpus has that perspective.

**Every route tried was refused.**

| Target | Method | Result |
|---|---|---|
| `https://www.glassdoor.com/Reviews/Los-Angeles-County-Reviews-E15617.htm` | curl, browser UA | **403**, body titled "Security \| Glassdoor", text "Humans only" |
| `https://www.glassdoor.com/Reviews/company-reviews.htm?sc.keyword=Modoc+County` | curl | **403**, same wall |
| same Glassdoor URL | WebFetch | **403 Forbidden** |
| `https://www.indeed.com/cmp/County-of-Los-Angeles/reviews` | curl | **403**, "Security Check - Indeed.com … Additional Verification Required" |
| `https://www.indeed.com/cmp/Modoc-County/reviews`, `/cmp/Trinity-County/reviews` | curl | **403**, same wall (so even *existence* of a small-county employer page is unverified) |
| same Indeed URL | WebFetch | **403 Forbidden** |
| Wayback fallback (`archive.org/wayback/available`, `web.archive.org/cdx`) | curl | **429**, then "Internet Archive services are temporarily offline" |

So the large-versus-small-county Glassdoor spot check **could not be completed**,
and the honest statement is "not verified", not "no reviews exist". What I can
report is the one substitute that did answer:

- **Comparably**, a scrapable Glassdoor competitor, has a page for the largest
  county employer in the United States and it is **empty**:
  `https://www.comparably.com/companies/county-of-los-angeles` returns HTTP 200
  and reads "Employee Participants **0** … Total Rating **0**", last modified
  2018-11-07. So the smaller review sites are not a usable substitute even for
  LA; the content is concentrated on the two walled platforms.
- CareerBliss's LA County URL pattern 404s; Trustpilot returns 403.

**How I would count it in a real harvest** (three options, in cost order):
1. Browser automation with a logged-out session (the Claude-in-Chrome extension
   or Playwright with a residential-like profile): read the review count and
   rating off the employer page, then page through reviews filtered by job
   title. Glassdoor shows the count without login; the review *bodies* are
   metered after a few views and then ask for an account. Cost: ~1 minute per
   employer page, 58 counties plus large-county departments, so a half-day.
2. Indeed's employer pages are similar and additionally expose a
   **job-title filter** (`/cmp/<employer>/reviews?ftopic=…&fjobtitle=Eligibility+Worker`),
   which is exactly the slice we want.
3. Licensed data: Revelio Labs and Glassdoor's research programme both sell or
   grant review-level panels; that is the only route that is both complete and
   terms-compliant at scale.

**Expected skew, stated as a hypothesis not a finding.** County employer pages
should exist for all 58 counties because every county hires, but review volume
should track headcount, which tracks population — so this family probably
*worsens* the rural gap rather than filling it. The one piece of direct evidence
in this document points the same way: the Modoc grand jury investigated social
services staffing precisely because there was no other public signal than
newspaper job ads, and found "approximately 16 of the 45 positions in the
department remain unfilled"
([Modoc 2024-25](https://www.countyofmodoc.gov/DocumentCenter/View/1536/Fiscal-Year-2024-2025-Modoc-County-Grand-Jury-Final-Report)).
In rural counties the mandated civic record substitutes for the review site.

**A scrapable staff-side alternative worth a separate packet.** County job
postings and civil-service class specifications describe internal steps and
caseload expectations, are published by every county, and
`https://www.governmentjobs.com/careers/lacounty` returns HTTP 200 to a plain
curl (the rural slugs I guessed — `/careers/modoc`, `/careers/trinitycounty` —
redirect to the site root, so per-county slugs must be discovered, not guessed).
This is designed-tier rather than experiential, but it is staff-side, and it is
open.

## 3. Reviews of government offices (Yelp, Google Maps)

| Target | Result |
|---|---|
| `https://www.yelp.com/search?find_desc=Department+of+Public+Social+Services&find_loc=Los+Angeles%2C+CA` | **403** |
| `https://www.yelp.com/biz/los-angeles-county-department-of-public-social-services-los-angeles` | **403** |
| `https://www.yellowpages.com/...` (two URLs) | **403** |
| `https://www.google.com/search?q=Modoc+County+Social+Services+reviews` | HTTP 200 but the body is the redirect shim: "Please click here if you are not redirected within a few seconds" — no results, no counts |
| `https://www.google.com/maps/search/Modoc+County+Social+Services` | **HTTP 200, 213 KB**, and the HTML **confirms the place entity exists** (`"Modoc County Social Services"`, `itemtype="http://schema.org/Place"`), but contains **no review count and no ratings** — they are fetched by JS |

So the Yelp-versus-Modoc spot check is **half-answered**: the *venue* demonstrably
exists for a rural county office (Google has a place record for Modoc County
Social Services), but the review counts and texts are not retrievable by script.
The LA DPSS Yelp page is a known-good URL pattern that returns 403 to scripts.

**How to count it.** Google Places API "Place Details" returns a `user_ratings_total`
for every place plus **at most five review texts** — enough to measure
channel existence and rating volume for all 58 counties cheaply, but not enough
to harvest review corpora; the newer Places API (New) has the same five-review
cap. Yelp Fusion API returns up to three review excerpts per business. Both need
a free API key. Full review text needs a browser. **Recommended split: use the
Places API for the availability model (a per-county `n_reviews` covariate for
each office type), and a browser pass only for the counties that matter to a
case study.** Reviews of offices routinely contain wait times, which is why this
is worth the key.

## 4. CalGuns county CCW threads — channel existence solved, volume still skewed

The single cleanest natural experiment in this document. `calguns.net` runs a
**CalGuns Concealed Carry County Information Forum** in which one user (Gray
Peterson) opened **one thread per county in a single batch on 14-15 October
2010**, so the venue was created by fiat rather than by demand:
`https://www.calguns.net/forum/concealed-carry-license-to-carry/calguns-concealed-carry-county-information-forum`
(7 index pages, 303 topics; HTTP 200 to plain curl; reply and view counts are in
the static HTML as `posts-count` / `views-count`).

**Channel existence: 58 of 58 counties have a thread.** Volume:

| County | Posts | Views |
|---|---|---|
| Los Angeles | **17,267** | 1,915,285 |
| San Bernardino | **9,307** | 1,382,983 |
| Sacramento | 5,565 | 1,219,596 |
| Orange | 5,358 | 996,111 |
| Contra Costa | 4,413 | 775,997 |
| … | | |
| Calaveras | 98 | 59,660 |
| Amador | 53 | 33,924 |
| Glenn | 25 | 15,702 |
| **Alpine** | **15** | 7,351 |
| Colusa | 9 | 14,940 |
| Sierra | 5 | 5,488 |
| Mariposa | 4 | 7,489 |
| Trinity | 3 | 7,605 |
| Modoc | **0** | 4,123 |

**The required spot check, San Bernardino versus Alpine: 9,307 posts versus 15,
a ratio of 620:1.** Summed over the nine no-subreddit counties: **212 posts out
of 71,065 in county threads, 0.3%**, for 0.47% of the state's population. The
top five counties hold **59%** of all posts. Two counties' threads have zero
replies (Modoc, Del Norte) and Mendocino's only thread is a zero-reply question.

This is the result the availability model should be fitted against. It separates
the two mechanisms cleanly: **when a venue is created administratively for every
county, the hurdle term vanishes (58/58) but the volume gradient survives almost
unchanged.** The reddit r = 0.74 finding is therefore about channel creation,
and the post-level scarcity in small counties is a second, independent effect.
Note also that view counts do *not* collapse the same way — Trinity's 3-post
thread has 7,605 views — so small-county residents are reading a venue they do
not post in, which matters if the paper wants to claim the information is
*unavailable* rather than merely *unwritten*.

Timing content is present and thread titles advertise it: e.g.
`LASD RENEWALS TIMELINE`
(`…/1790537-lasd-renewals-timeline`) and `Madera county wait time`
(69-post Madera thread plus a dedicated 3-post wait-time thread).

## 5. City-Data county subforums — worse coverage than reddit

`https://www.city-data.com/forum/california/` returns HTTP 200 and lists
**exactly nine California sub-venues**: Los Angeles, Monterey County, Orange
County, Sacramento, San Bernardino and Riverside Counties, San Diego,
San Francisco - Oakland, San Jose, Ventura County. Everything else falls into
the general California forum (which runs past `index501.html`, so the statewide
volume is large but not county-tagged). **Nine metro sub-venues for 58 counties
is a harsher channel-existence skew than reddit's 49 of 58.**

City-Data's vBulletin search is reachable **by GET**, which makes it countable:
`https://www.city-data.com/forum/search.php?do=process&query=<terms>&forumchoice%5B%5D=9&childforums=1`
(forum 9 is California, `childforums=1` includes the nine metro subforums).
Counts are thread counts, from the page's own "Showing results 1 to 30 of N"
line:

| Query (California tree) | Threads |
|---|---|
| accessory dwelling unit (California tree) | **13** |
| accessory dwelling unit (whole site, no forum filter) | **250** (a display cap; treat as ≥250) |
| accessory dwelling unit permit | **5** |
| granny flat California | **10** |
| eligibility worker caseload | **1** |
| accessory dwelling unit Sacramento | **2** |
| accessory dwelling unit Trinity | **0** ("Sorry - no matches") |
| accessory dwelling unit Alpine | **0** |
| building permit Sacramento | **17** |
| building permit Trinity | **1** |
| septic permit county | **13** |
| CalFresh | **36** |

**The Avvo-style ADU spot check, done on City-Data instead because Avvo is
walled: Sacramento 2 threads, Trinity 0, Alpine 0.** Caveat: vBulletin filters
words shorter than four characters, so `ADU` cannot be searched — every query
must be spelled "accessory dwelling unit", which will undercount. Volume is low
in absolute terms: roughly a dozen threads statewide tie a permit to a process.

## 6. Legal Q&A (Avvo, Justia) — Cloudflare

| Target | Result |
|---|---|
| `https://www.avvo.com/legal-answers/search?q=accessory+dwelling+unit` | **403**, body is Cloudflare "Just a moment… Enable JavaScript and cookies to continue" |
| `https://www.avvo.com/topics/accessory-dwelling-unit` | **403**, same |
| Avvo search via WebFetch | **403** |
| `https://answers.justia.com/search?query=accessory+dwelling+unit` | **403**, same Cloudflare challenge |

The Avvo county spot check therefore **could not be run**; it is "not verified".
Avvo's structure is still worth recording because it is unusually well suited to
this project if access is solved: questions carry a **practice area plus a city
and state**, and answers are written by lawyers who describe the county process.
The way to count it is a headless browser with a JS-capable fetch (Cloudflare's
managed challenge passes with a real browser), or Avvo's sitemap, or a licensed
feed. I substituted the City-Data ADU counts in § 5 so that the ADU
urban-versus-rural comparison still has numbers behind it.

## 7. MuckRock — API needs a token

`https://www.muckrock.com/api_v1/foia/?format=json&search=building+permit`
returns **403 with the Cloudflare "Just a moment…" challenge** to curl, and
**401 Unauthorized** to WebFetch — i.e. the API itself requires a token, which
is free on registration (`Authorization: Token <key>`). MuckRock is the right
shape for this project (FOIA request threads contain agency response letters
with statutory clocks, and the requester's own timeline of delay), but it is
also **requester-driven and therefore urban- and journalist-skewed**; I would
not expect rural county coverage. Not verified either way in this session.

## 8. Board of Supervisors records (Legistar / Granicus) — open API, large counties only

The **Legistar Web API is open and needs no key**, and it answers:
`https://webapi.legistar.com/v1/lacounty/matters?$top=3&$filter=substringof('permit',MatterTitle)`
returns HTTP 200 with full agenda-item titles, e.g. a matter beginning "Adopt
findings and conditions and order relating to Project No. R2006-03771-(2),
Conditional Use Permit Case No. 200600326-(2)… (Continued from meetings of
12-16-08, 2-24-09, 3-24-09, 4-28-09, 6-23-09 and 11-24-09)". That parenthetical
continuation list is a **literal per-case timeline of hearing dates** — a
decision-node sequence for one permit, in a machine-readable API.

Client-code probe (10 URLs, `?$top=1`): **200 for `lacounty`, `sfgov`,
`santaclara`, `alameda`; HTTP 500 for `sonoma`, `sonomacounty`, `modoc`,
`trinity`, `mariposa`, `sandiegocounty`.** So Legistar is a **large-county
platform**: it deepens the urban record and does nothing for the rural gap. Note
that `matters` are agenda items, not public-comment text; spoken and written
public comment lives in minutes, video and Granicus eComment, which is a
separate and harder harvest.

## 9. The remaining families, briefly

- **BiggerPockets (ADU threads).** `https://www.biggerpockets.com/search?q=ADU+Sacramento+county`
  → **403 Cloudflare challenge**. Content is investor-side and city-skewed.
  Not verified.
- **Septic and well-drilling forums.** `https://permies.com/f/42/septic` and
  `https://www.terrylove.com/forums/index.php?forums/septic-systems.13/` both
  return HTTP 200 but **redirect to unrelated forum ids** (`/f/42/singles`,
  `hvac-heating-cooling.13`), so my guessed forum ids were wrong; the sites are
  reachable and scrapable, the taxonomy needs to be read off the index first.
  `https://www.inspectionnews.net/home_inspection/` did not connect (curl exit
  6 / HTTP 000). These forums are national and organised by topic, not by
  county, so county attribution will have to come from free-text mentions —
  expect low recall and a rural skew that is *favourable* (septic and well
  activity is concentrated in rural counties, the inversion A5 predicts).
- **Local news letters and county papers.** `https://modocrecord.com/` (200),
  `https://www.trinityjournal.com/` (200) both exist and both are subscription
  sites ("Subscribe", "e-Edition", "Subscription Services" in the nav), so the
  letters-to-the-editor that would carry rural process complaints sit behind a
  paywall. Careful: `mountainmessenger.com` is a **West Virginia** paper
  ("Lewisburg, Greenbrier County WV"), not Sierra County's Mountain Messenger —
  a reminder to verify small-paper domains by content, not name.
- **311 data and county satisfaction surveys.** Not fetched this session. 311
  exists only in the large metros, so it is an urban-depth source, and
  satisfaction surveys appear inside budget PDFs, which is a document-mining
  problem rather than a forum problem. The Permit Sonoma report is the proof
  that the survey numbers surface in oversight documents anyway: it quotes
  "a positive response of 95.41% out of 1,592 s[u]rvey respondents".

## 10. Synthesis

### The five sources that add most beyond reddit

1. **Civil grand jury reports.** *Rank 1 by a wide margin.* Mandated in all 58
   counties, so supply is decoupled from population; they contain oversight-grade
   process description, statutory clocks and staffing numbers; they are free,
   stable and citable; and they are the only family that is **richer per document
   in small counties**. The Sonoma *Permit Sonoma 2025* report alone delivers
   average days-to-review by permit type including septic and well, an AB 2234
   compliance audit over 5,000 task records, and a serial-versus-parallel
   plan-check routing description — i.e. a decision model with timings, for one
   county, in one PDF.
2. **CalGuns county CCW threads.** A user-side venue with **58 of 58 channel
   existence** and explicit timeline threads. Its value is partly evidentiary and
   partly methodological: it is the control that shows the reddit r = 0.74
   result is about channel creation, not only about demand.
3. **Google Maps / Yelp reviews of county offices.** The only family that
   plausibly gives *citizen wait-time reports for rural offices* — the place
   entity for Modoc County Social Services demonstrably exists — and the only one
   where a cheap API gives a clean per-county availability covariate
   (`user_ratings_total`) even though full text needs a browser.
4. **Glassdoor and Indeed staff reviews.** Ranked fourth despite being fully
   blocked this session, because the *perspective* is unique: staff-only steps
   are otherwise unobservable outside leaked SOPs, and this is the only public
   venue where a permit technician or eligibility worker describes internal
   routing and caseload. High value, high access cost, urban skew.
5. **Board of Supervisors records via the Legistar Web API.** Open, keyless,
   machine-readable, and it yields literal per-case hearing chronologies. Large
   counties only, so it is a depth source, not a coverage source.

Runners-up, with reasons: **City-Data** is countable by GET but has only nine
California sub-venues and ~a dozen permit-process threads statewide;
**Avvo** is the best-structured legal Q&A for county attribution but is
Cloudflare-walled; **MuckRock** needs a free token and is requester-skewed;
**septic and well forums** are reachable and rural-favourable but not
county-tagged; **rural county newspapers** exist and are paywalled.

### The rural-gap verdict

**The commons moves, it does not vanish — but it changes genre.** For the nine
counties with no subreddit:

- **Civil grand jury reports: 7 of 9 publish reports that can be downloaded
  right now** (Alpine, Colusa, Glenn, Mariposa, Modoc, Sierra, Trinity), and an
  8th (Calaveras) once a browser enumerates its DocBox widget; **5 of 9 are
  machine-readable as posted** (Colusa, Glenn, Modoc 2024-25, Sierra, Trinity);
  **2 of 9 are image-only and need OCR** (Alpine, Mariposa, plus Modoc's
  2025-26); **1 of 9 posts nothing at all** (Amador, which answers report
  requests by email at `webdocrequest@amadorcourt.org`).
- **CalGuns: 9 of 9 have a county thread, holding 212 posts between them**
  (0.3% of the forum's 71,065 county-thread posts).
- **City-Data: 0 of 9 have a sub-venue**, and ADU queries for Trinity and Alpine
  return zero threads.
- **Google Maps: place entities exist** for rural county offices; review counts
  not verified without a key.

The substantive difference matters for the paper's claim. What rural counties
lose is the *first-person applicant account* — "I applied on the 3rd, got the
appointment on the 21st". What they keep is the *institutional account* — a
grand jury writing that 16 of 45 social-services positions are vacant, or that
the city publishes no information about how to apply for a building permit. Both
are process evidence, but they identify different parameters: user posts
identify **realised durations**, grand jury reports identify **capacity,
structure and documentation gaps**. A fairness claim built only on user posts
will read rural counties as data-absent; a claim built on both reads them as
data-*different*. That is the better paper, and it is the one the evidence
supports.

One caution against over-claiming: grand jury supply is mandated but not
uniform. Sierra's own foreperson records a six-year gap in compliant reports,
and small-county juries choose one or two subjects a year, so for any *specific*
programme in any *specific* small county the probability of coverage in a given
year is low. The right model is a **low-rate Poisson process with a mandated
floor**, not guaranteed coverage.

### Harvest plan

Ordered by value per unit effort. Fetch counts are estimates; every count I
state as a fact above is either read off a page or computed from cached bytes.

| # | Harvest | Method | Fetches | Effort | Output |
|---|---|---|---|---|---|
| H1 | **Grand jury full sweep** | Seed the 58 county URLs from `https://cgja.org/websites/`; follow "reports/archives" links; download every report and response PDF; OCR the image-only third with `ocrmypdf`/tesseract; classify titles into programme families before downloading bodies where bandwidth matters | ~200 index + ~2,000–4,000 PDFs | **2 agent-days**, plus ~10–20 GB cache and a few CPU-hours of OCR | `corpus/counties/grandjury/` + a title-level index csv (county, year, title, url, bytes, has_text) |
| H2 | **CalGuns county threads** | 58 threads, 20 posts/page ⇒ ~3,600 page fetches for the full 71,065 posts; parse post date, author, body; flag timing words | ~3,600 | **0.5 day** | per-county post table directly comparable to `reddit_coverage.csv` |
| H3 | **Office-review availability pass** | Google Places API Place Details for 4 office types × 58 counties (social services, planning/building, environmental health, sheriff CCW unit) to get `user_ratings_total` and rating | ~230 API calls | **2 hours** + a free key, ~$5–10 | two new covariate columns per county for the availability hurdle |
| H4 | **Legistar depth pass** | `lacounty`, `sfgov`, `santaclara`, `alameda`; `matters` filtered on permit/CalFresh/General Relief terms, then `matterhistories` for hearing chronologies | ~500 API calls | **0.5 day** | per-case hearing timelines for large counties |
| H5 | **City-Data programme sweep** | GET search over forum 9 with `childforums=1`, ~8 programme phrasings × 58 county names, spelled out (no 3-letter tokens) | ~460 GETs | **2 hours** | thread counts per county per programme; expect mostly zeros outside the nine metros |
| H6 | **Staff-side browser pass** | Browser automation on Glassdoor and Indeed employer pages for all 58 counties: read review count and rating; then title-filtered review text for a large/small pair | ~150 page loads | **1 day**, needs a browser and careful rate limits | the only staff-side corpus; also the first real test of the urban skew |
| H7 | **Unlock list** (do first, it is cheap) | Register a free **MuckRock API token**; get a **Google Places** key and a **Yelp Fusion** key; retry the four 403 grand jury sites (Mendocino, El Dorado, Tuolumne, Shasta) from a browser; retry Internet Archive when it is back up | — | **1 hour** | converts four "not verified" rows into data |

### What this implies for the availability model (W2)

The measurement model needs a **per-source-family hurdle**, not a single one:

- reddit: hurdle on channel existence (49/58), then volume ~ population.
- CalGuns: **no hurdle** (58/58), volume ~ population with the same slope.
- City-Data: hurdle at the *metro* level (9 sub-venues), effectively zero outside.
- grand jury: **no hurdle, and no population slope** — instead a low per-county
  per-year rate of subject coverage, times a machine-readability factor of about
  ⅔, times an access factor for the 403/JS/email-only counties.
- Glassdoor/Indeed and Legistar: hurdle plus a steep population slope.

Planting these five different availability shapes, rather than one, is what lets
the recovery experiment show that a fairness conclusion depends on which venues
the analyst happens to observe.

## Files produced

- This report: `docs/scoping/2026-09-16-forums-beyond-reddit.md`
- `corpus/counties/forum_sources.csv` — 15 source families with url_pattern,
  program_family, evidence_type, scrapable_how, estimated_volume,
  urban_rural_skew, example_url and notes.
- `corpus/counties/raw/forums/` — every fetched byte, one file per URL plus a
  `<file>.meta.json` recording HTTP code, byte count and redirect target, and
  `_fetch_log.jsonl` as the append-only log. Extracted PDF text is under
  `corpus/counties/raw/forums/txt/`.
- `corpus/counties/raw/forums/_calguns_county_threads.json` — the parsed
  CalGuns county-thread table (303 topics with post and view counts), which is
  the input for the H2 harvest and directly comparable to
  `corpus/counties/reddit_coverage.csv`.

Nothing under `benchmark/synth/` or `pipeline/procbench/` was touched, and
nothing was committed.
