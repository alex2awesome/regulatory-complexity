# Measuring how long California procurement processes take: data sources and designs (2026-10-15)

Context: students in Dan's lab have collected and normalized California purchase data (what was bought,
by whom, by which acquisition method) and have no timing. This note lists where timing can come from,
what each source measures, and which designs turn it into a comparison of *processes* (the rule set a
purchase went through) rather than a description of delays. Sources were checked by web search on
2026-10-15; "verify" marks claims to confirm before relying on them.

## 0. What a procurement timeline looks like (events to look for)

need identified → requisition created/approved → [NCB or special-category request → DGS approval] →
solicitation posted (CSCR) → Q&A / addenda → bids due → evaluation → notice of intent to award (NOI) →
protest window → award / contract execution → SCPRS registration → PO issued → delivery → invoice →
payment (Prompt Payment Act, 45 days) → amendments / extensions → contract end → successor contract.

Every pair of adjacent events that appears in some public record is a measurable interval. The goal is
not one "cycle time" but intervals that attach to steps the rules require, so that two acquisition methods
(e.g. informal vs formal competitive, or competitive vs NCB) can be compared step by step.

## 1. Sources that carry dates

| Source | Dates it carries | Access | Measures |
|---|---|---|---|
| **SCPRS purchase-order extract** (the eSCPRS "Purchase Order Data" on data.gov / Kaggle, FY2012-13 to 2014-15; later years via Cal eProcure SCPRS search) | My recollection of the columns: `Creation Date`, `Purchase Date`, `Fiscal Year`, `Requisition Number`, `Acquisition Type/Method`, `Sub-Acquisition Method`, department, supplier, UNSPSC, price (verify against the data dictionary PDF on the data.gov listing) | Public bulk file (old years); Cal eProcure search (2015+); PRA for a full extract | PO date vs registration lag; June fiscal-year-end bunching; the acquisition-method label is the treatment variable for everything below |
| **Cal eProcure / CSCR solicitation events** | Publish date, bid due date, addenda dates, NOI and award documents per event (status "historical" after close) | Per-event web pages; no bulk export found; PRA to DGS Procurement Division (eprocure@dgs.ca.gov) for the event table | Posting → due (bid window), due → NOI, NOI → award: the California analogue of federal PALT |
| **SCPRS contract records** | Contract execution / start / end dates, amount, method | Cal eProcure SCPRS search; PRA | Award → registration; contract term; successor-contract gaps |
| **FI$Cal internal tables** (requisition, sourcing event, PO, receipt, voucher, payment) | Timestamps for the whole chain, all 150 departments | Not on Open FI$Cal (expenditures only); PRA or data-sharing agreement | The gold standard; a sample of departments would calibrate every other source |
| **Caltrans awarded-contracts listing** (ppmoe.dot.ca.gov, construction) | Bid opening date, award date, approval date per contract (page is JS-rendered; verify fields) | Public, scrapable | Ready-made bid-open → award times for one large agency, by contract size |
| **DGS Late Payment Penalties Paid reports** (Gov. Code §927.9, annual per agency) | Penalty counts and dollars by agency and by small/other business | Public PDFs on DGS site | The payment phase: which agencies miss the 45-day clock, by year |
| **CDT Project Approval Lifecycle** (IT projects; quarterly approved-project lists; TMF/TSF legislative reports) | Stage 1–4 approval dates, expected completion dates | Public PDFs; verify whether a dated list is downloadable | Stage 3 approval → award for IT procurements, the slowest class |
| **Local governments: Legistar / Granicus agendas** | Dates of "authorize solicitation" and "award contract" actions, by department | Legistar web API for the cities and counties that use it (verify coverage) | Authorization → award per local agency and method; comparable across jurisdictions under the same state rules |
| **Local bid portals (PlanetBids, BidNet, OpenGov)** | Posting, due, NOI dates per solicitation | Per-agency portals, scrapable; no statewide feed found | Local analogue of CSCR |
| **Bid protests** (DGS / OAH decisions) | Filing and decision dates | Public decisions | Time cost of a protest, and how often it is triggered by method |
| **NCB / special-category request forms** | Request and approval dates; stated justification | PRA to DGS | Time cost of the NCB approval step; justifications that cite lack of time (see §3) |
| **Federal FPDS** (solicitation date field, awards above the simplified threshold) | Solicitation date → award date (PALT) for federal awards located in California | Public bulk | External calibration and the template analysis: GAO's PALT study split lead time by value, competition, contract type and product |
| **Forum / vendor reports** (r/govcontracting, r/procurement, vendor blogs, GovWin-style commercial data) | Narrated intervals ("posted in March, awarded in November") | Scrape; our forum-report pipeline already handles timed gaps and selection | Noisy applicant-side view, useful for the phases no record sees (pre-solicitation, evaluation) |
| **Audits and reviews** (State Auditor, HSR 2026 procurement review, LAO) | Case-level timelines in prose (e.g. HSR: five procurements 3–10 months later than needed; Medi-Cal dental: 18-month delay, 7 amendments) | Public PDFs | Anchors and failure cases, not a sample |

Not found: any statewide dataset or DGS dashboard with cycle times (the six DGS dashboards are all spend);
any State Auditor report measuring procurement time statewide; a bulk CSCR export.

## 2. Designs that turn dates into process comparisons

1. **Event pairing across systems.** Join CSCR solicitation events to SCPRS contracts and POs (department,
   supplier, amount, description, event ID where present). Each join yields posting → NOI → award → PO
   intervals with the acquisition method attached. This is what the admin-milestone likelihood in the toy
   model consumes: exact intervals between named events, with open solicitations right-censored and
   cancelled solicitations as a terminal outcome.
2. **Dollar-threshold discontinuities.** The State Contracting Manual switches the required method at dollar
   thresholds (fair-and-reasonable → informal competitive → formal competitive; SB/DVBE option; IT vs non-IT;
   each department's delegated purchasing authority sets its own ceiling). Compare intervals just below and
   just above a threshold: the jump is the causal time cost of the stricter process. This is the procurement
   version of the "edit the statute" counterfactual.
3. **Bunching below thresholds (no timing needed).** From the PO data alone, the density of purchase amounts
   just under each threshold measures how much buyers avoid the stricter process. Revealed cost of the
   process, available today from the students' data. Also: purchase splitting (several POs to one supplier
   just under the threshold in a short window).
4. **Planned vs actual schedules from solicitation documents.** Most RFPs/IFBs contain a "Key Action Dates"
   table (release, Q&A, due, NOI, award, contract start). Extract with an LLM at scale: the planned table is
   the agency's own process model, step by step; later addenda and NOI documents give the actuals; the
   difference is delay by step. Closest to our text → process pipeline.
5. **Successor-contract gaps and symptoms of lateness.** For recurring services, predecessor end date →
   successor start date in SCPRS; count of extensions/amendments; emergency or NCB use whose justification
   cites insufficient time. These measure process time without observing the process.
6. **Department heterogeneity under one rule set.** Departments differ in delegated authority and in
   staffing; with method and threshold fixed, between-department variation in intervals is the analogue of
   between-town variation in the toy model, and the same shared-duration, town-pace structure applies.
7. **Payment phase.** Late-payment penalty reports by agency and year give the end of the chain; join to the
   PO data by department to see whether slow-to-buy departments are also slow-to-pay.
8. **Survival framing.** Treat each solicitation as a case: posted, then awarded, cancelled, or still open
   at extraction. Cancellation and re-solicitation rates are burden outcomes in their own right.

## 3. Where I would start

- **Week 1, no new data:** bunching and splitting analysis on the students' PO data; PO-date seasonality
  (fiscal-year-end rush); registration lag (`Purchase Date` → `Creation Date`) by department and method.
- **Week 2, public scrape:** CSCR historical events for a few departments (publish, due, NOI, award) and
  the Caltrans awarded list; pair with SCPRS; first posting → award distributions by method and size.
- **In parallel, one PRA:** FI$Cal requisition → PO → payment timestamps for a handful of departments, or the
  CSCR event table from DGS. One PRA to DGS for the NCB request log with justifications.
- **Then:** the threshold discontinuity on the paired data, and the planned-vs-actual extraction from
  solicitation PDFs.

Sources consulted (2026-10-15): DGS SCPRS/CSCR historical data page and public-access bulletin; data.gov
"Purchase Order Data" (eSCPRS, FY2012-13 to 2014-15); DGS PD-Dashboards; DGS Late Payment Penalties Paid
reports and Gov. Code §927.9; OFPP PALT memorandum (2021) and GAO/DAU PALT material; CDT PAL stage
documents and TMF/TSF reports; HSR Authority procurement review (2026); State Auditor noncompetitive
contracting findings; Caltrans awarded-contracts page.

## 4. Joinability onto the students' SCPRS scrape (added 2026-10-19)

Yasmine Mabene (Dan's student) says the dataset was scraped from the Cal eProcure SCPRS search
(`caleprocure.ca.gov/pages/SCPRSSearch/scprs-search.aspx`, which fronts the FI$Cal SCPRS component) and
carries no timing. Checked what the public record actually holds and which dated sources share a key with it.
Browser extension was not connected, so the FI$Cal screens were read from DGS's own walkthrough screenshots
(`ADA-CaleProcureFISCalSCPRSSearch.docx`); Cal eProcure event pages are JS-rendered and were not inspected.

### 4a. What a public SCPRS record contains (verified from DGS screenshots)
- Header: Department (business unit), Purchase Document #, Transaction Status, Start Date, End Date, Supplier,
  Buyer Name, LPA ID, Version #, Bill Code, Acquisition Type, Acquisition Method, Merchandise Amount,
  Freight/Tax/Misc, Grand Total. Line items with UNSPSC. "Associated Transactions": Purchase Order ID, Buyer,
  Start Date, PO Total, PO Status, Version. "Version History": Version, Modified By, Date Updated, Reason
  (e.g. "Amendment for Time & Money"), Start/End Date, Amount Change.
- Search parameters include Transaction Start Date range and Buyer ID. "Download Detail Information" gives
  Business Unit, Department Name, Purchase Document #, Associated PO #, Start Date, End Date, Grand Total, PO Total,
  line-level fields.
- NOT on the public record: solicitation/event ID, requisition number or date, SCPRS entry (creation) date,
  award date. Start Date is the PO date or the contract term start (FI$Cal manual §6.25 "Date of Purchase").
- The older DGS open-data extract (`data.ca.gov` "Purchase Order Data 2012-2015") DID carry `Creation Date`
  ("Date the entry was entered in Fi$Cal"), `Purchase Date`, `Requisition Number` ("Fi$Cal designated unique
  number of the associated Requisition") and `SCPRS_UserType` (entered from the PO/Contract module vs direct
  SCPRS entry). Header verified from the CSV. So DGS has released entry dates and requisition keys before;
  that is the precedent for a records request.

### 4b. Keys that exist on both sides
| Dated source | Its key | SCPRS-side key | Join type | Status |
|---|---|---|---|---|
| Caltrans "Notices of Intent to Award" (awardee, contract number, intent date, award date; rolling page, 47 monthly Wayback snapshots 2019-08 → 2026-08) | contract number (e.g. 06A3185) | Purchase Document # (Caltrans BU) | exact, if Caltrans registers under the same number | unverified; grep the scrape for `\d{2}A\d{4}` under Caltrans |
| DGS PD Notices of Intent to Award (PDF per event: posting date, Event ID, description, proposed awardee, protest deadline, buyer; year folders 2023–2026; list page keeps ~5 months, no archive) | Event ID, awardee, buyer name | Supplier, Buyer Name, Start Date, description | fuzzy (awardee + buyer + date window) | buyer name is on both sides, which makes this near-exact |
| Cal eProcure/CSCR events (event ID, department, published date, bid due date, status Active/Awarded/Cancelled, category, description; attachments incl. NOI) | department, event name, awardee in NOI attachment | Department, Supplier, Start Date, description | fuzzy; block on department×supplier, Start Date in a window after bid-due | event page may show the PO/contract number after award; not verified (JS page) |
| Solicitation numbers quoted in text | `(IFB|RFP|RFQ|RFO)[ -]?\d+` in event name | same pattern in SCPRS Description / item description | exact where present | hit rate unknown; one regex over the scrape answers it. FI$Cal's own manual (§3.5) uses one number for request, solicitation and purchase document, so some departments will match exactly |
| FI$Cal internal chain requisition → event → PO (timestamps at each) | Requisition Number, Event ID, PO ID | Purchase Document # / Associated PO # | exact | not public; PRA to DGS/FI$Cal; 2012–2015 extract is the precedent |

### 4c. Timing already inside the scrape (no join needed)
- Version History `Date Updated` vs original Start Date: time to first amendment, amendment counts, "time & money"
  reasons. Amendment-heavy contracts are the symptom the State Auditor reads as slow procurement.
- Successor-contract gaps: End Date of one contract vs Start Date of the next for the same department ×
  supplier × UNSPSC. A gap or a back-dated Start Date is a late re-procurement.
- PO IDs are sequential within a business unit (0000001016, 1017, 1018 in DGS's screenshots). Rank of PO ID vs
  Start Date gives an interpolated creation date; Start Date minus interpolated creation date is a rough
  issue-to-term lag. Fragile; use only as a sanity check on the joined intervals.
- Acquisition Method on every row is the treatment label for all of the above (formal competitive vs informal
  vs LPA vs NCB), and the dollar thresholds that switch methods are the discontinuities in §2.

### 4d. What the join buys
- Caltrans: intent-to-award → award → SCPRS Start Date, per contract, 2019 onward, with method and amount.
- DGS PD formal solicitations: NOI posting → Start Date (award-to-execution lag), 2023 onward.
- Any department with CSCR events: publish → bid due → NOI → Start Date for competitively bid purchases, the
  slow formal tail where the time cost lives. Statutory floor: ≥10 days publish-to-due (GC 14827.2).
- None of this reaches the requisition (the start of the clock). That needs the FI$Cal extract.

Sources: DGS SCPRS search walkthrough `https://www.dgs.ca.gov/-/media/Divisions/PD/PTCS/eBISS/eProcurement/ADA-CaleProcureFISCalSCPRSSearch.docx`;
DGS bulletin F-01-18; data.ca.gov Purchase Order Data data dictionary and CSV header; FI$Cal Procurement Manual
(Aug 2014) §§3.5, 6.25, 7.2; DGS Award Notifications page and NIA PDFs; Caltrans Notices of Intent to Award
page and Wayback CDX; Apify Cal eProcure scraper field list.
