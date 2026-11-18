# CCW licensing in the remaining 43 California counties

Collected 2026-09-16 by scoping packet **P2-CCW-REMAINING**. Companion to
[the 15 small and mid-size counties](2026-09-16-ccw-15-small-counties-findings.md),
which covers Shasta, Madera, Kings, Napa, Humboldt, Nevada, Sutter, Mendocino,
Yuba, Lake, Tehama, San Benito, Tuolumne, Calaveras and Siskiyou. Together the
two files cover all 58 counties. Same nine columns, same conventions.

Statute: Penal Code §26150–26225 as amended by SB 2 (2023), with the §26205
90/120-day decision clock. Issuing authority: the county sheriff (and some city
police chiefs).

## Method and caveats

**WebSearch was exhausted (200/200) before this packet started**, so nothing
here came from a search engine. Every fact came from a page fetched directly by
URL pattern: the sheriff's Permitium "start" page
(`https://<slug>.permitium.com/ccw/start`), the county sheriff's own CCW page,
or a policy PDF linked from one of those. Pages were fetched with `curl` (a
browser user-agent) and cached under `corpus/counties/raw/ccw/`; WebFetch was
used as a fallback on 403s.

Two corrections to the pattern the earlier pass established:

1. The slug is **not always `<county>ca`**. Large agencies use their own
   abbreviation: `lasd` (Los Angeles), `sbcsd` (San Bernardino), `scso`
   (Santa Clara), `sfso` (San Francisco), `fresnoso`, `solanoso`, `montereyso`,
   `inyoso`. `<county>ca` and `<county>so` were both probed for all 43.
2. A 200 response is not proof of a live portal. `ocsd.permitium.com` and
   `modocca.permitium.com` both return Permitium's **"Former Customers"** page,
   and `santaclaraca.permitium.com` returns a "Demo Code" gate. These were
   discarded and the real hosts found separately.

**"Not verified" means nothing was found by these means, not that nothing
exists.** In particular, a county with no reachable CCW page is recorded as not
verified across the row, not as having no process.

## Table A — process facts

| County | Channel | Policy doc | Psych eval | Fees (new / renewal) | Stated processing time | Training | Interview | References |
|---|---|---|---|---|---|---|---|---|
| Los Angeles | Permitium (`lasd`); legacy paper applicants still supported for proficiency forms | "The CCW policy is currently under review, and will be available when updated"; CCW Terms & Conditions PDF (rev. 09-25-25) published | not verified | $43 initial + $173 issuance = **$216** / $17 + $17 = **$34**; nonresident $136 + $173; new fees effective 9/1/2026 | "multiple weeks" (Permitium boilerplate); **monthly counts published** (2026-07: 855 received, 627 issued) | 16h / 8h; training only after the background investigation, and only from the published LASD Authorized Training Providers list (7/21/26); LASD is not accepting new providers | yes; in person at 4700 W Ramona Blvd, Monterey Park, **or virtual, at the applicant's election** | 3 |
| San Diego | not verified | not verified | not verified | not verified | not verified | not verified | not verified | not verified |
| Orange | **CCW Pro** (`ccwpro-ocsheriff.cssa.cloud`), a different vendor; Permitium lists OC as a former customer | **Policy 218 v2024 published**; also CCW Terms of License 2024 | **discretionary** per §26190(e); cost capped at "the rate the Department pays for psychological testing of employees" | initial Live Scan $71/$93/$115 + local $300 (eff. 7/1/2025) = **$393 standard** / renewal DOJ $52 + local $111 = **$163** | Policy 218: 90-day and **120-day** §26205 clocks, extendable 30 days | 16h / 8h; no fee for training before the §26202(d)(1) disqualification determination; provider tuition set privately; instructor list not verified | **yes, required** with CCW Licensing Staff; from 1/1/2026 in person **or** by video, at the applicant's election | 3 |
| Riverside | Permitium only | not on the portal; approved vendor list PDF published | not verified | $113 initial (incl. $93 DOJ Live Scan + $20 sheriff) + $80 issuance = **$193** / **$113**; +$5.25 service fee since 5/1/2025 | "multiple weeks" | 16h / 8h; vendor list PDF | yes for new (appointments Mon–Wed 07:00–15:30; Palm Desert Mon–Tue); **renewal appointments no longer required** unless requested | 3 |
| San Bernardino | Permitium (`sbcsd`) | Terms of Use form PDF; no Lexipol-style policy located | not verified | $188 initial + $95 issuance = **$283** (portal states "TOTAL (Does NOT include Training cost) $283") / **$205**; nonresident $172 + $79 = $251 | "multiple weeks"; FAQ: no earlier interview slots than those shown online | 16h mandatory, **scheduled by the Sheriff's Office**, which runs its own range (range flyer, hold-harmless form, US Postal money order the only accepted payment); renewal 8h from the linked vendor list | yes; reschedule handled through the CCW division | 3 |
| Santa Clara | Permitium (`scso`); sheriff's own site 403 | **SCSO CCW policy PDF published** (hosted on permitium-downloads) | **required** — the portal states the fees "do NOT include LIVESCAN, PSYCHOLOGICAL EVALUATION and TRAINING fees" | $488 initial + $488 issuance = **$976** / **$395**; excludes Live Scan, psych eval, training | "multiple weeks"; new-applicant appointments Tue and Thu 09:00–11:00, initial interviews Thursdays | 16h / 8h; approved **Training Instructor List** published (Approved Training Vendors 2026); training from any other facility refused | yes, Thursdays | 3 |
| Alameda | Permitium | referenced ("Alameda County Sheriff's Department CCW policy") but not linked | **required** — "Psychological Evaluation" is a listed step and carries a **$400 Psychological Service Fee** | $347 initial + $400 psych + $346 issuance = **$1,093** (excl. range costs) / **$157** | "multiple weeks"; any step not completed within 90 days of notification withdraws the application | 16h Range Safety Course + live-fire proficiency test / 8h renewal; "Range Costs" billed separately; instructor list not verified | yes, with an investigator | 3 |
| Sacramento | Permitium only | **CCW Unit Policies and Procedures** linked from the portal | not mentioned | $291 initial + $290 issuance = **$581** (eff. 7/1/2026) / **$267**; DOJ Live Scan $93–$137 extra | "multiple weeks"; **CCW Committee decision "can take up to two months"**; then "most applications are processed within two to four weeks after Contingent Approval"; interview must occur within 12 months of submission, 2 reschedules max | 16h / 8h from a DOJ-certified CCW instructor; certificates valid **180 days**; max 3 firearms; instructor list not verified | yes, Mondays and Wednesdays at 2101 Hurley Way | 3, contacted by the Sheriff's designee |
| Contra Costa | Permitium only ("CCW forms must be uploaded using Permitium, they will not be accepted at the window") | not verified (sheriff site 403) | not verified | $80 initial + $80 issuance = **$160** / **$137** | "multiple weeks" | 16h / 8h; instructor list not verified | not stated on the portal | **3 minimum**, one a §273.5(b) person and one a cohabitant if applicable; reference checks run Wed–Fri; an unreachable reference "may be denied or withdrawn" |
| Fresno | Permitium (`fresnoso`) | not verified | not verified | **$283** administrative cost / **$177**; +$7 service fee; modification $10 | "multiple weeks"; appointments Mon–Thu | 16h / 8h; vendor must be sheriff-approved; list not verified | yes (appointment-based) | 3 |
| Kern | Permitium | not verified | not verified | $169 initial (incl. $93 DOJ Live Scan + $76 sheriff) + $5 service = **$174** / **$155** | "multiple weeks"; fingerprinting by appointment only Mon/Wed 08:00–12:00, Tue/Thu 12:00–16:00 | 16h / 8h; **published course of fire**: 12 rounds, 4 at 5 yd, 2 strong-hand and 2 support-hand at 5 yd, 4 at 7 yd, 75% pass; vendor list PDF published | pickup by appointment; interview not stated | 3 |
| San Francisco | Permitium (`sfso`) | not verified | not verified | $100 initial (incl. $93 DOJ + $7 admin) + $100 issuance = **$200** / **$150** | "multiple weeks" | 16h / 8h; instructor list not verified | not stated on the portal | 3 |
| Ventura | Permitium only ("will not be accepted at the window") | portal points to the sheriff's "current Policies, Fee Structure, Vendor list, and FAQ" page | not verified | $230 initial + $230 issuance + $93 DOJ = **$553 grand total** (published as such) / $105 + $93 = **$198** | "multiple weeks" | 16h / 8h; vendor list on the sheriff site | not stated on the portal | 3 |
| San Joaquin | Permitium | CCW Bureau Policies and Procedures referenced, not linked | not verified | $153 initial (incl. $20 filing + $133 DOJ) + $80 issuance = **$233** / **$77** | **§26205 quoted verbatim: written notice within 120 days of the initial application, or 30 days after the DOJ criminal background check, whichever is later** | 16h (incl. a 16-hour online course for nonresidents from named facilities) / 8h; approved vendor list published | **yes, and conducted virtually** — camera on, face visible, no masks; PST; late arrivals rescheduled at the investigator's discretion | 3 |
| San Mateo | Permitium | not verified | **required** — "The Sheriff's Office will be requiring psychological testing for all NEW applicants effective July 1, 2023" | $128 initial (incl. $93 DOJ + $35 rolling + $82 sheriff) / **$128**; a second published schedule shows $111 + $117 issuance incl. a $35 range fee, renewal $112 | "multiple weeks" | 16h / 8h; a **$35 range fee** appears in the fee table; instructor list not verified | yes | 3 |
| Stanislaus | Permitium; sheriff site 403 | not verified | not verified | **$193** ($113 non-refundable at submission + $80 before issuance) / **$77** | "multiple weeks" | 16h / 8h; instructor list not verified | yes | 3 |
| Sonoma | Permitium | not verified; approved-provider list said to be "on our Sheriff's Office website" | not verified | **$809 total** for a new standard licence (initial non-refundable fee + approval fee, amounts not broken out) / $187 + $93 DOJ = **$280**; modification **$122** | "multiple weeks" | 16h / 8h; **training certificates valid only 90 days**, renewal training must fall in the 90 days before expiry; provider list on the sheriff site | yes | 3 |
| Tulare | Permitium | not verified | not verified | $107 initial + $79 issuance = **$186** / **$107**; duplicate/modification $0 | "multiple weeks" | 16h / 8h; **CCW instructor list published** on the sheriff site | not stated on the portal | 3 |
| Santa Barbara | Permitium | not verified | **required, and priced: "Pyschological Exam – $625 (Paid at the office at the time of appointment)"** in the published fee breakdown | $137 initial (incl. $20 sheriff + $93 DOJ + $24 rolling) + $80 issuance = **$217**, plus the $625 psych exam and training = **$842+** / **$142** ($93 DOJ + $24 rolling + $25 sheriff) | "multiple weeks" | 16h / 8h; "Training Fee – check with Training Instructor"; instructor list not verified | yes, interview appointment scheduled during the application | 3 |
| Solano | Permitium (`solanoso`) | not verified | not verified | $146 initial (incl. $93 DOJ + $53 sheriff) + $212 issuance = **$358** / **$178** | no "multiple weeks" boilerplate and no stated time — **not verified** | 16h / 8h; **Solano County CCW Approved Trainers PDF published** | not stated on the portal | 3 |
| Monterey | Permitium (`montereyso`) | not verified | not verified | **$242** administrative cost / **$95** (renewal requires an $88 non-refundable application fee before issuance); modification $15 | "multiple weeks" | 16h / 8h; **online training vendor list published**; from 9/1/2026 the Sheriff's Office itself Live Scans renewal applicants | yes, interview appointment scheduled during the application | 3 |
| Placer | Permitium | not verified | not verified | **$100** ($20 non-refundable at submission + $80 before issuance) / **$77** — the cheapest new licence in the 43 | "multiple weeks" | 16h / 8h; instructor list not verified | yes | 3 |
| San Luis Obispo | Permitium (`sloca`) | not verified; Approved CCW Qualification Vendors PDF (8/2025) published | not verified | **portal and FAQ disagree**: portal says new total $249.50 ($93 DOJ + $156.50 sheriff) with a notice of an increase to **$406** ($313 county + $93 DOJ); FAQ already states $406. Renewal: portal $293 ($100 + $93), notice and FAQ **$252** ($200 + $52). +$7 service fee | "multiple weeks"; FAQ: after the interview "we must wait for DOJ approval. **This may take up to several months**", then a second review and Chief Deputy sign-off | 16h / 8h; Approved CCW Qualification Vendors PDF | yes | 3 |
| Merced | Permitium | CCW Bureau Policies and Procedures referenced, not linked | not verified | $50 initial (incl. $10 filing) + $50 issuance, with a published breakdown of **$121 DOJ Live Scan + $100 sheriff** / **$82** | "multiple weeks" | 16h / 8h; **CCW Approved Instructor Classes page published** | yes, at a single named location | 3; **city residents must also carry a "CCW Applicant Local Police Agency Records Inquiry" form to their city police department** for signature, except Merced PD, which forwards records directly |
| Santa Cruz | **paper only** — DOJ form BOF 4012 plus county forms; no Permitium subdomain exists under any slug probed; sheriff site itself 403 but `scsheriff.com` serves the documents | **CCW Policy 207 published (4/2025)**; plus a published CCW Licence Checklist (FY 26-27), instructor requirements and minimum course of fire, pre-background interview form | **listed as a step for every new applicant** (checklist step 12), "if necessary" on renewal; Policy 207.4.2(b) makes it the Sheriff's call, cost "shall not exceed the reasonable costs to the Office" (§26190) | **$504** new, 50% ($252) non-refundable at submission and $252 before issuance (eff. 7/1/2026) / **$206** + $93 DOJ; change fee $52 | Policy 207: written notice **within 90 days** for a new licence; **120 days** or 30 days after the DOJ return per §26205 | 16h / 8h with an approved instructor; **Approved CCW Instructors list (06/2026)** published; every firearm must also pass a free safety inspection by the office **Rangemaster**, who administers the proficiency exam | yes — with the **Professional Standards and Conduct Sergeant**, plus a Pre-Background Interview Form filed in advance | not stated in the policy or the checklist — not verified |
| Marin | Permitium only ("will not be accepted at the window") | the CCW page states the office acts "in accordance with applicable law and this policy"; the policy PDF it links (`License_to_Carry_a_Firearm.pdf`) **404s** | **required of everyone** — "All applicants must complete a psychological evaluation"; "your license will not be issued without completion of the psychological evaluation"; cost "to be determined by doctor administrating exam" | $132 initial (incl. DOJ Live Scan, non-refundable) + $125 issuance = **$257**, plus psych exam and training at cost / **$201** | not stated; the page notes "**references not responding to us is the most frequent delay in getting licenses approved**" | 16h / 8h; named instructor list on the CCW page with a designated Chief Instructor; cost set by the instructor | yes, scheduled by an assigned investigator after the Live Scan returns | **3 letters of reference** from separate individuals; a cohabitant must be one; §26202(b)(2) contact is direct |
| Butte | Permitium | not verified | not verified | $18 submission + $117 at the Live Scan appointment (incl. $93 DOJ + $24 rolling) + $283 issuance (incl. $277 issuance + $6 ID card) = **$418** / $18 + $117 + $55 = **$190** | "multiple weeks"; **proof of examination must be filed within 90 days of the approval letter** or the application is treated as abandoned and all fees re-apply | 16h / 8h; instructor list not verified | not stated on the portal | 3 |
| Yolo | Permitium | not verified | not verified | **$325** ($65 non-refundable at submission + $260 before issuance) / **$219** | "multiple weeks"; renewal window opens 90 days before expiry | 16h / 8h; instructor list not verified | yes | 3 |
| El Dorado | Permitium; sheriff site `edso.org` 403 | not verified | not verified | **$218 total** new ($143 incl. $93 DOJ + $25 Live Scan + $25 admin, then a $75 admin issuance fee) / **$158** | "multiple weeks"; Live Scan must be done in person at Placerville or South Lake Tahoe | 16h / 8h; instructor list not verified | yes | 3 |
| Imperial | Permitium only ("will not be accepted at the window") | not verified | not verified | $267 initial (incl. $93 DOJ + $174 sheriff) + $50 issuance = **$317** / **$249**; duplicate/modification **$100** | **"Due to an inordinate amount of CCW applications, the Imperial County Sheriff's Office processing time is currently at 120 days"** — the only county in the 43 to publish a current queue figure; inactivity over 45 days forfeits fees | 16h / 8h; vendor list published | not stated on the portal | 3 |
| Del Norte | Permitium (`delnortesoca`) | not verified | not verified | $166 initial + $63 final = **$229** / $77 + $11 = **$88** | not stated as a duration; sequencing is published: phase-one background and **Sheriff's interview first**, then the 16-hour course by invitation | 16h; the approved vendor list is released only after the interview, not published in advance | yes, with the Sheriff, before training | 3 |
| Glenn | not verified | not verified | not verified | not verified | not verified | not verified | not verified | not verified |
| Colusa | not verified | not verified | not verified | not verified | not verified | not verified | not verified | not verified |
| Plumas | Permitium (`plumassoca`) | not verified | **discretionary** — "Psychological Evaluation fee may be required at the discretion of the Sheriff" | $133 initial (incl. $93 DOJ Live Scan + $20 rolling + $20 processing) + $80 on approval = **$213** / **$138** | no duration given; the portal says "the application process is a long, tedious, and meticulous process" and applicants "move forward ONLY upon notification" | 16h / 8h; **Plumas instructor list PDF published** | **yes, in person with the Sheriff** | 3 |
| Inyo | Permitium (`inyoso`) | not verified | not verified | $150 initial (incl. $93 DOJ + $57 sheriff) + $50 issuance = **$200** (published as a total) / **$178**, rising with the 9/1/2026 Live Scan requirement | "multiple weeks" | 16h / 8h; **2025 CCW Training and Trainers PDF published** on inyocounty.us; online vendor list on the portal | yes | 3 |
| Mono | Permitium | not verified | not verified | $113 initial (incl. $93 DOJ + $20 sheriff) + $80 issuance = **$193** (published as a total) / **$118** | no "multiple weeks" text and no stated duration — **not verified** | 16h / 8h; instructor list not verified | not stated on the portal | 3 |
| Mariposa | Permitium | not verified | not verified | **$105** initial, no separate issuance fee published / **$98** | "multiple weeks" | 16h / 8h; instructor list not verified | yes | 3 |
| Amador | Permitium (`amadorsoca`); county site `amadorgov.org` 403, sheriff CCW page reachable at amadorsheriff.org | not verified | not verified | $25 processing at submission + $133 at the CCW appointment (incl. $95 DOJ + $40 sheriff) = **$158** / **$72** (incl. $52 state + $20 sheriff) | no "multiple weeks" boilerplate and no stated duration; **new-licence appointments only Tuesday and Thursday** | 16h / 8h; **vendor list PDF published** | yes, by appointment | 3 |
| Lassen | Permitium (`lassensoca`) | not verified | not verified | **$84** new (LCSO processing fees) / **$72** — the lowest published new-licence fee in the 43 | no duration; same "long, tedious, and meticulous" language as Plumas, applicants advance only on notification | 16h / 8h; **Aug 2026 instructor list PDF published** | **yes, in person with the Sheriff** | 3 |
| Trinity | **paper** — the only CCW document published is the generic DOJ form BOF 4012 (Rev. 09/2026) in the county document centre; no county-specific instructions found | not verified | not verified | not verified | not verified | not verified (state minimum 16h/8h applies by statute) | not verified | not verified |
| Modoc | not verified — the sheriff's own nav link `/777/Concealed-Carry-Weapons` resolves to a page with no CCW content, and **`modocca.permitium.com` now serves Permitium's "Former Customers" page**, so the county appears to have left the portal | not verified | not verified | not verified | not verified | not verified | not verified | not verified |
| Sierra | **paper** — DOJ form BOF 4012 filed with the Sheriff-Coroner; no portal | **published**: "Concealed Carry Weapon Policy" and a 4-page "CCW License Procedure" (Sep 2024), plus CCW Qualifications and an Approved CCW Instructors list. The policy PDF is a **scanned image with no text layer** | not mentioned | **$148** / **$82**; from 9/1/2026 renewals are **$93 and the licence runs 3 years instead of 2**; modification $25 | not stated | 16h with live-fire / 8h with live-fire, course must be Sheriff-approved, incl. a **1-hour mental-health block** and a written test; qualification certificates over 6 months refused for modifications; instructor list published (4 named providers incl. out-of-county) | not mentioned | 3, one a §273.5(b) person and one a cohabitant if applicable |
| Alpine | Permitium (`alpinesoca`) | not verified | **discretionary** — "A Psychological Evaluation MAY be required by the Sheriff (provider fee ≈ $TBD)"; the applicant books and pays the authorised psychological services agency directly, which reports pass/fail to the Sheriff | **$243** new (incl. $93 DOJ/Live Scan) / **$193** (incl. $93 state); modification and duplicate **$0** | no duration; "starts, but does not end, with the interview"; applicants advance only on notification | 16h / 8h; **CCW instructor list PDF published**, plus a separate nonresident-courses PDF | **yes** — and nonresidents must appear in person with the Sheriff at 99 Water Street, Markleeville | 3 |

## Table B — CCW page, portal host and fetch status

Column 1 of the nine. "Blocked" means a 403 or Cloudflare challenge to a
scripted fetch with a browser user-agent; "404" means the guessed or linked path
did not resolve.

| County | Official CCW page | Portal host | Fetch status |
|---|---|---|---|
| Los Angeles | https://lasd.org/ccw/ | lasd.permitium.com | 200 both |
| San Diego | not verified | none found | **sdsheriff.gov 403 to curl and to WebFetch on every path; sandiegocounty.gov/sheriff 404** |
| Orange | https://www.ocsheriff.gov/commands-divisions/professional-services-command/professional-standards/ccw-licensing | ccwpro-ocsheriff.cssa.cloud | 200; two guessed paths 404 first; process and fee graphics are **JPEG images**, so the process is not machine-readable on the page |
| Riverside | http://www.riversidesheriff.org | riversideca.permitium.com | portal 200 |
| San Bernardino | https://wp.sbcounty.gov/sheriff/ccw-faq/ | sbcsd.permitium.com | 200 (the obvious `/sheriff/ccw/` path 404s) |
| Santa Clara | https://countysheriff.sccgov.org/home | scso.permitium.com | **sheriff.santaclaracounty.gov 403, sccgov.org 403**; portal 200 |
| Alameda | https://www.alamedacountysheriff.org/index.php | alamedaca.permitium.com | portal 200 |
| Sacramento | https://www.sacsheriff.com/pages/ccw_gun_permit.php | sacramentoca.permitium.com | portal 200 |
| Contra Costa | not verified | contracostaca.permitium.com | **cocosheriff.org 403**; portal 200 |
| Fresno | http://www.fresnosheriff.org/ | fresnoso.permitium.com | portal 200; `/ccw.html` 404 |
| Kern | http://www.kernsheriff.org/ | kernca.permitium.com | portal 200; `/ccw` 404 |
| San Francisco | https://www.sfsheriff.com/ | sfso.permitium.com | 200 both |
| Ventura | https://sheriff.venturacounty.gov/public-resources/carry-a-concealed-weapon-ccw/ | venturaca.permitium.com | portal 200 |
| San Joaquin | https://www.sjgov.org/sheriff/ | sanjoaquinca.permitium.com | portal 200; sjsheriff.org does not resolve |
| San Mateo | http://www.smcsheriff.com/ | sanmateoca.permitium.com | portal 200; `/ccw` 404 |
| Stanislaus | not verified | stanislausca.permitium.com | **scsdonline.com 403**; portal 200 |
| Sonoma | https://www.sonomasheriff.org | sonomaca.permitium.com | portal 200 |
| Tulare | https://tularecounty.ca.gov/sheriff/community/ccw-instructor-list | tulareca.permitium.com | portal 200 |
| Santa Barbara | not verified | santabarbaraca.permitium.com | portal 200 |
| Solano | https://www.solanocounty.com/depts/sheriff/pubinfo/weaponslicense.asp | solanoso.permitium.com | portal 200 |
| Monterey | https://mcso.countyofmonterey.gov/concealed-carry | montereyso.permitium.com | portal 200 |
| Placer | http://www.placer.ca.gov/departments/sheriff/concealed-weapon-permits/ccwfaq | placerca.permitium.com | portal 200 |
| San Luis Obispo | https://www.slosheriff.org/concealed-carry-weapon/ and /faq/ccw-faq/ | sloca.permitium.com | 200 all three |
| Merced | https://www.co.merced.ca.us/3266/CCW-Approved-Instructor-Classes | mercedca.permitium.com | portal 200 |
| Santa Cruz | https://www.scsheriff.com/SheriffHome/INeedTo/ConcealedCarryWeapon(CCW).aspx | none — paper | **santacruzsheriff.org 403 to curl and WebFetch; the alternate host scsheriff.com served everything** |
| Marin | https://www.marinsheriff.org/services/ccw | marinca.permitium.com | 200; the policy PDF the page links **404s** |
| Butte | https://www.buttecounty.net/sheriffcoroner/1722/Apply-for-a-CCW | butteca.permitium.com | 200 |
| Yolo | https://yolocountysheriff.com/services-resources/concealed-weapons-permit-info/ | yoloca.permitium.com | portal 200 |
| El Dorado | not verified | eldoradoca.permitium.com | **edso.org 403**; portal 200 |
| Imperial | https://icso.imperialcounty.org/ | imperialca.permitium.com | 200 both |
| Del Norte | https://www.co.del-norte.ca.us/departments/Sheriff/CCW | delnortesoca.permitium.com | 200 both |
| Glenn | not verified | none found | **countyofglenn.net 403 on the homepage and on every sheriff path** |
| Colusa | not verified | none found | countyofcolusa.org 200 but **no CCW page exists in its navigation**; colusasheriff.com / .org / colusacountysheriff.com do not resolve |
| Plumas | https://www.plumascounty.us/2492/Concealed-Weapons-Permit | plumassoca.permitium.com | portal 200 |
| Inyo | https://www.inyocounty.us/ | inyoso.permitium.com | 200 both |
| Mono | http://monosheriff.org/sheriff/ | monoca.permitium.com | portal 200 |
| Mariposa | http://www.mariposacounty.org/622/Concealed-Weapons-Permits | mariposaca.permitium.com | portal 200 |
| Amador | https://www.amadorsheriff.org/administration-division/public-information/concealed-weapons-permits | amadorsoca.permitium.com | **amadorgov.org 403**; portal 200 |
| Lassen | https://www.lassencounty.org/dept/sheriffs-office/carry-permits-ccw | lassensoca.permitium.com | 200 both |
| Trinity | https://www.trinitycounty.org/Sheriff (no CCW sub-page found) | none — paper | 200, but the only CCW document is the generic DOJ BOF 4012; `/1012/Concealed-Weapons-Permits` 404 |
| Modoc | not verified | **formerly Permitium** (`modocca.permitium.com` → "Former Customers") | modocsheriff.us 200 but `/777/Concealed-Carry-Weapons` returns a page with no CCW content; co.modoc.ca.us sheriff paths 404 |
| Sierra | https://sierracounty.ca.gov/835/Concealed-Carry-Weapon-CCW | none — paper | 200, found only through the county site's own search; the linked policy PDF is a **scanned image with no text layer** |
| Alpine | https://www.alpinecountyca.gov/204/Sheriff | alpinesoca.permitium.com | portal 200 |

## Cross-county observations

**Channel.** 35 of 43 are on Permitium. Three are paper only — **Santa Cruz**
(DOJ BOF 4012 plus five county forms), **Sierra** (BOF 4012) and **Trinity**
(BOF 4012, with nothing county-specific published). **Orange County is on a
different vendor**, CCW Pro at `ccwpro-ocsheriff.cssa.cloud`, and Permitium now
serves a "Former Customers" page at `ocsd.permitium.com`. **Modoc also appears
to have left Permitium** the same way. San Diego, Glenn and Colusa could not be
determined. Combined with the earlier 13-of-15, Permitium runs the CCW intake
for **48 of the 58 counties** that could be verified — a single private vendor
is the de facto author of the public-facing process text in California.

**The vendor text is the process description.** "Appointment times and
processing times can take multiple weeks" appears verbatim on **32 of the 35**
live portals (not on Amador, Mono or Solano). So do the character-references
paragraph and the SB 2 training paragraph. When a county says something
different, it is because a human wrote over the template — and those are exactly
the counties that publish a policy.

**Psychological evaluation — the sharpest divergence found anywhere in the
58.** The earlier 15 found no county requiring one of everybody. Here five require it
of every new applicant, and a sixth lists it as a step for all new applicants
while its policy makes it discretionary:

| County | Status | Published cost |
|---|---|---|
| Marin | required of all applicants; "your license will not be issued without completion of the psychological evaluation" | set by the examining doctor |
| San Mateo | required of all **new** applicants since 7/1/2023 | not published |
| Santa Clara | required — policy: "every applicant shall satisfactorily complete a psychological exam"; nonresidents may do it virtually | not published (excluded from the fee table) |
| Santa Barbara | listed in the published fee breakdown | **$625**, paid at the office at the appointment |
| Alameda | a numbered step with its own line in the fee table | **$400** |
| Santa Cruz | checklist step 12 for new applicants, "if necessary" on renewal; Policy 207.4.2(b) makes it the Sheriff's call | capped at "the reasonable costs to the Office" |

Discretionary, consistent with §26190(e), in **Orange** (capped at the rate the
Department pays for employee testing), **Plumas** and **Alpine**. The remaining
**34 of 43 never mention it**. So the same statute produces a $0 step in most
counties and a $400–$625 mandatory examination in four of the state's wealthiest.

**Fees.** New standard licence, sheriff plus DOJ fees only, excluding training
and psychological testing: **Lassen $84** to **Santa Clara $976** — a factor of
**11.6**. Including Alameda's mandatory $400 psychological fee its total is
**$1,093**, a factor of 13. Renewal: **Los Angeles $34** to **Santa Clara $395**,
a factor of 11.6. The two extremes are both in the Bay Area and 20 miles apart:
Santa Clara $976 new, San Mateo $128, San Francisco $200. Los Angeles County,
the largest, is also among the cheapest at $216 new and $34 renewal.

A ranked list of new-licence totals: Lassen 84, Placer 100, Amador 158, Contra
Costa 160, Kern 174, Tulare 186, Mono 193, Riverside 193, Stanislaus 193,
Inyo 200, San Francisco 200, Plumas 213, Los Angeles 216, Santa Barbara 217
(before the $625 psych exam), El Dorado 218, Del Norte 229, San Joaquin 233,
Monterey 242, Alpine 243, Marin 257 (before psych and training), San Bernardino
283, Fresno 283, Merced 221 (published breakdown: $121 DOJ + $100 sheriff), Imperial 317, Yolo 325,
Solano 358, Orange 393, San Luis Obispo 406, Butte 418, Santa Cruz 504,
Ventura 553, Sacramento 581, Sonoma 809, Santa Clara 976, Alameda 1,093.
Mariposa publishes only a $105 initial fee. San Diego, Glenn, Colusa, Modoc,
Sierra (paper, $148) and Trinity are outside the portal set.

**Published processing times.** Only nine of 43 say anything beyond the vendor
boilerplate:

- **Imperial**: "Due to an inordinate amount of CCW applications, the Imperial
  County Sheriff's Office processing time is **currently at 120 days**" — the
  only live queue figure found in either file.
- **Orange**, **Santa Clara**, **San Joaquin**, **Santa Cruz**: the §26205
  120-day clock quoted from a policy or the statute; Santa Cruz also states a
  90-day clock for new licences.
- **Sacramento**: the CCW Committee "meets once or twice per month… can take up
  to two months", then "most applications are processed within two to four weeks
  after Contingent Approval".
- **San Luis Obispo**: after the interview, DOJ approval "may take up to several
  months", then a second review and Chief Deputy sign-off.
- **Butte** and **Alameda**: 90-day applicant-side deadlines, not agency times.
- **Marin** names the binding constraint instead of a duration: "references not
  responding to us is the most frequent delay in getting licenses approved."

Disclosure of timing again tracks disclosure of process, exactly as the 15-county
pass found.

**Training.** 16h/8h everywhere, as SB 2 requires. What varies is who may teach
and who inspects:

- **Published instructor or vendor lists**: Los Angeles, Riverside, Kern,
  Santa Clara, Solano, Monterey, Inyo, Tulare, Merced, San Luis Obispo,
  Imperial, Plumas, Lassen, Alpine, Sierra, Santa Cruz, Marin, Amador.
- **The county trains or tests its own applicants**: San Bernardino schedules
  the 16-hour course itself and runs the range (US Postal money order only);
  San Mateo charges a **$35 range fee** inside the licence fee; Santa Cruz's
  **Rangemaster** inspects every firearm free of charge and administers the
  proficiency examination; Alameda's 16 hours is a "Range Safety Course and
  Live-Fire Proficiency Test" with range costs billed separately.
- **Published courses of fire**: Kern (12 rounds, 75% pass), Santa Cruz,
  Sierra (live fire plus a written test and a one-hour mental-health block).
- **Del Norte inverts the sequence**: the approved vendor list is released only
  after the background check and the Sheriff's interview, so an applicant cannot
  price the training before committing.
- **Certificate shelf life** differs by a factor of two: Sacramento 180 days,
  Sonoma 90 days, Sierra 6 months for modifications.

**Interview.** Confirmed required in 28 of the 43. Notable: **Plumas, Lassen and
Alpine require it in person with the Sheriff personally**; **Santa Cruz** with
the Professional Standards and Conduct Sergeant, plus a Pre-Background Interview
Form filed in advance; **San Joaquin conducts them virtually** with published
camera rules; **Los Angeles and Orange give the applicant the choice** of
in person or video (Orange from 1/1/2026); **Riverside has dropped renewal
interviews** unless requested. Sacramento allows two reschedules and withdraws
on a third; San Bernardino's FAQ refuses any request for an earlier slot.

**References.** Three, everywhere it is stated — the §26175 / §273.5(b) formula
from the vendor template. Three counties describe the enforcement, which is
where the burden actually sits: **Contra Costa** runs reference checks only
Wednesday to Friday and may deny or withdraw an application if a reference
cannot be reached; **Marin** calls unresponsive references its most frequent
delay; **Santa Clara**'s policy interviews every reference and will not accept a
set drawn entirely from the applicant's subordinates or direct reports. Santa
Cruz's policy and checklist do not mention references at all.

## City police chiefs that issue instead of, or alongside, the sheriff

The earlier pass found Madera PD and Napa PD. In the large counties this is the
normal arrangement, not the exception, and it multiplies the number of distinct
processes well beyond 58:

- **Los Angeles**: first-time applicants must live in an LASD contract city or
  an unincorporated community. "Applicants residing in a municipality other than
  those served by the LASD shall apply for a CCW license with their local police
  department." Existing LASD licensees may still renew with LASD.
- **Contra Costa**: the sheriff's own portal routes residents of **Antioch,
  Brentwood, Concord, Martinez, Oakley, Pinole, Pittsburg, Richmond, San Ramon
  and Walnut Creek** to those cities' police departments, each with its own
  page and process (Antioch's is at antiochca.gov/police/concealed-carry-weapon/).
- **San Luis Obispo**: residents of **Arroyo Grande, Atascadero, Paso Robles,
  Pismo Beach and the City of San Luis Obispo** must apply to their city agency
  under §26155; existing sheriff licensees may keep renewing with the sheriff.
- **Merced**: the sheriff still issues, but a city resident must take a "CCW
  Applicant Local Police Agency Records Inquiry" form to their city police
  department for signature and upload it. Merced PD is the only one that
  forwards records directly, so residents of the other cities carry the paper
  themselves.
- **Plumas, Lassen, Del Norte, Alpine and San Francisco** portals all use the
  §26155 "Sheriffs/Police Chiefs" variant of the boilerplate, and the Plumas and
  Lassen pages quote §26155 (the municipal chief) rather than §26150. The
  **Plumas** portal also refers to "the LCSO CCW Unit" — Lassen's initials — in
  text that otherwise prices PCSO fees, i.e. one county's page is a partly
  unedited copy of another's.

## Published per-county statistics

- **Los Angeles County Sheriff's Department publishes monthly CCW counts** on
  its CCW page, for 2025 and 2026: applications received and licences issued per
  month. 2025 totals 7,309 received and 8,152 issued; 2026 through July,
  5,200 received and 5,935 issued (July 2026: 855 received, 627 issued). A
  footnote records a definitional change — from April 2026 the received figure
  includes modification applications — which is the kind of seam the benchmark
  cares about.
- **Santa Cruz** advertises "Monthly Agency Statistics" on the same navigation
  as its CCW material; the page returned an empty 300-byte body to a scripted
  fetch, so whether it carries CCW counts is **not verified**.
- **No per-county DOJ dataset was located.** `openjustice.doj.ca.gov/data`
  returns a 3-KB client-side application shell with no content, and
  `oag.ca.gov/firearms/ccw` 404s. This matches the earlier pass: CCW counts
  exist in individual sheriff reports, not in a central table.

## Retrieval findings

Of 43 counties, **8 returned a 403 or Cloudflare challenge** from an official
county or sheriff host: San Diego, Santa Clara, Contra Costa, Stanislaus,
El Dorado, Santa Cruz, Amador and Glenn — **19%**, against 40% (6 of 15) in the
small-county pass. Across all 58 counties that is **14 of 58, 24%**. The rate is
lower here largely because the Permitium portal is a second, unprotected copy of
the same information: for Santa Clara, Contra Costa, Stanislaus, El Dorado and
Amador the portal answered every question the blocked sheriff site would have.
Only **San Diego and Glenn are total blocks**, where no host served anything.

Four further failure modes, none of them a 403, all of them fatal to an
automated reader:

1. **A 200 that is not the thing you asked for.** `ocsd.permitium.com`,
   `modocca.permitium.com` ("Former Customers") and
   `santaclaraca.permitium.com` ("Demo Code") all return 200. A fetcher that
   checks status codes and not content would have recorded Orange and Modoc as
   Permitium counties and Santa Clara as unreachable. All three are wrong.
2. **The process published as an image.** Orange County's application process,
   required training and fee schedule are JPEGs on the page; the fee schedule
   exists as HTML on a separate sub-page, the process does not. Sierra County's
   CCW policy is a 405-KB scanned PDF with no text layer.
3. **Dead links inside live pages.** Marin's CCW page links its own
   `License_to_Carry_a_Firearm.pdf`, which 404s — the same pattern the earlier
   pass found in Mendocino and Yuba.
4. **Unguessable paths.** Sierra's CCW page was reachable only through the
   county site's own search; San Bernardino's is at `/sheriff/ccw-faq/` while
   `/sheriff/ccw/` 404s; Orange's is three levels deep under
   `commands-divisions/professional-services-command/professional-standards/`.
   Guessing `<sheriff-host>/ccw` failed for Fresno, Kern, Ventura, San Mateo,
   Contra Costa and Stanislaus. **The Permitium slug is more predictable than any
   county's own URL**, which is a finding about who is actually maintaining the
   public interface.

## What this adds to the benchmark design

1. **The declared tier is thin in the large counties too, and thin in a
   different way.** Policy documents were found for only 6 of 43 — Orange
   (Policy 218 v2024), Santa Clara, Santa Cruz (Policy 207), Sierra (scanned),
   Sacramento (policies and procedures) and, as an unreachable link, Marin.
   Los Angeles says in as many words that "the CCW policy is currently under
   review". Population does not buy disclosure.
2. **One vendor is the author of the declared tier.** 48 of 58 counties publish
   Permitium's text. The mock web should model a shared template with local
   overrides, because that is what exists: the boilerplate is the prior and the
   local edit is the signal.
3. **The psychological evaluation is a clean natural experiment.** Identical
   statute, §26190(e); five counties require it of everyone at $400–$625, three
   make it discretionary with a cost cap, and 35 never mention it. That is a
   decision node with a large, observable, county-level cost.
4. **Who does the work is a route choice, not a parameter.** San Bernardino and
   Alameda run their own ranges; Santa Cruz's Rangemaster inspects every firearm
   and administers the test; Del Norte withholds the vendor list until after the
   interview; Lake (in the earlier file) teaches the course itself. These change
   the applicant's sequence, not just the price.
5. **City chiefs mean the unit of analysis is not the county.** Contra Costa
   alone routes to ten city departments and San Luis Obispo to five. A 58-row
   table understates the number of distinct processes by at least an order of
   magnitude, and the earlier file's Madera PD and Napa PD cases were not
   anomalies.
6. **Content-checking is a required retrieval behaviour.** Three of the 200-OK
   pages in this sweep were not what their URLs promised. Any agent that treats
   HTTP 200 as success will silently record false facts about Orange, Modoc and
   Santa Clara.

## Every URL used

**Permitium portals confirmed live** (all `https://<slug>.permitium.com/ccw/start`):
lasd · riversideca · sbcsd · scso · alamedaca · sacramentoca · contracostaca ·
fresnoso · kernca · sfso · venturaca · sanjoaquinca · sanmateoca · stanislausca ·
sonomaca · tulareca · santabarbaraca · solanoso · montereyso · placerca · sloca ·
mercedca · marinca · butteca · yoloca · eldoradoca · imperialca · delnortesoca ·
plumassoca · inyoso · monoca · mariposaca · amadorsoca · lassensoca · alpinesoca

**Permitium hosts that resolve but are not live county portals**:
ocsd.permitium.com and modocca.permitium.com ("Former Customers") ·
santaclaraca.permitium.com ("Demo Code")

**Permitium slugs probed and non-existent** (DNS failure, both `<county>ca` and
`<county>so` and, for the gaps, `<county>soca` and agency abbreviations):
losangelesca/so · sandiegoca/so/sheriff/soca · sdso · sdsoca · orangeca/so ·
ocsheriff · sanbernardinoca/so · sanfranciscoca/so · sfsheriff ·
santaclaraso/sccso/sccsoca/scsoca/sccsheriff · sanluisobispoca/so ·
slosheriff/sloso/slocounty/sanluisobispoco · santacruzca/so/soca/sheriff/county ·
delnorteca/so · dnso · delnortesheriff · glennca/so/soca/sheriff ·
colusaca/so/soca/sheriff · plumasca/so · plumassheriff · amadorca/so ·
amadorsheriff · lassenca/so · lassensheriff · trinityca/so/soca/sheriff ·
modocso/soca · sierraca/so/soca/sheriff · alpineca/so · alpinesheriff · kernso ·
fresnoca · solanoca · montereyca · inyoca · monoso · placerso · marinso ·
butteso · yoloso · eldoradoso · imperialso · mariposaso · mercedso ·
sanjoaquinso · sanmateoso · santabarbaraso · sonomaso · stanislausso ·
tulareso · venturaso · riversideso · alamedaso · sacramentoso · contracostaso

**Los Angeles**: lasd.org/ccw/ · lasd.org/ccw-contact/ · lasd.org/ccw/modify/ ·
lasd.permitium.com/ccw/start ·
lasd.org/wp-content/uploads/2026/02/Transparency_CCW_Terms_Conditions_updated_per_SB2_modified_09-25-25_online_a.pdf ·
lasd.org/wp-content/uploads/2026/07/Transparency_LASD_Authorized_Training_Providers_7.21.26.pdf ·
lasd.org/wp-content/uploads/2026/02/CCW_020426_LASD_Initial_Nonresident_Instructions.pdf ·
lasd.org/wp-content/uploads/2023/04/CCW_Shooting_Standards_093022.pdf ·
www.lasd.org/pdf/ccw_amendment_application.pdf ·
permitium-downloads.s3.amazonaws.com/LASD/LASD_AUTHORIZED_TRAINING_PROVIDERS.pdf

**San Diego** (all blocked): www.sdsheriff.gov/ · sdsheriff.gov/ ·
www.sdsheriff.gov/resources/concealed-weapons-license ·
www.sdsheriff.gov/bureaus/court-services-bureau/licensing-division ·
www.sandiegocounty.gov/sheriff/ · www.sandiegocounty.gov/content/sdc/sheriff.html

**Orange**: ocsheriff.gov/ ·
www.ocsheriff.gov/commands-divisions/professional-services-command/professional-standards/ccw-licensing ·
.../ccw-home/fee-schedule · .../ccw-home/reporting-law ·
www.ocsheriff.gov/page/ccw-application-process ·
ccwpro-ocsheriff.cssa.cloud/ ·
www.ocsheriff.gov/sites/ocsd/files/2024-10/Policy%20218%20v2024.pdf ·
.../2024-10/CCW%20Terms%20of%20License%20-%202024.pdf ·
.../2024-02/Lost%20Carry%20Concealed%20Weapons%20CCW%20License.pdf

**Riverside**: riversideca.permitium.com/ccw/start ·
permitium-downloads.s3.us-east-1.amazonaws.com/Riverside/RSO_VendorList.pdf ·
.../Riverside/RSO_Nonresident_Applicaton_Instructions.pdf ·
.../Riverside/26202+PC.pdf · permitium-downloads.s3.amazonaws.com/Riverside/RSO_LIVESCAN_info.pdf

**San Bernardino**: wp.sbcounty.gov/sheriff/ · /sheriff/ccw-faq/ ·
/sheriff/divisions/administration/records/ccw/ (same page) ·
sbcsd.permitium.com/ccw/start ·
wp.sbcounty.gov/sheriff/wp-content/uploads/sites/17/Flyers/1-CCW-RANGE-FLYER-new.pdf ·
.../sites/17/2-Range-Hold-harmless-Form.pdf · .../3-Range-map.pdf ·
.../5-Firearms-form.pdf · .../Domestic-Violence-Statement_v3.pdf ·
permitium-downloads.s3.amazonaws.com/sbcsd/SBCSD_renewal_vendorList.pdf ·
.../sbcsd/sbcsd_TermsofUseform.pdf

**Santa Clara**: sheriff.santaclaracounty.gov/ (403) ·
www.sccgov.org/sites/sheriff/Pages/home.aspx (403) · countysheriff.sccgov.org/home ·
scso.permitium.com/ccw/start ·
permitium-downloads.s3.us-east-1.amazonaws.com/SCSO_POLICY.pdf ·
permitium-downloads.s3.us-east-1.amazonaws.com/Approved+Training+Vendors+2026.pdf

**Alameda**: alamedaca.permitium.com/ccw/start · www.alamedacountysheriff.org/index.php

**Sacramento**: sacramentoca.permitium.com/ccw/start ·
www.sacsheriff.com/pages/ccw_gun_permit.php

**Contra Costa**: contracostaca.permitium.com/ccw/start · www.cocosheriff.org/ccw (403) ·
permitium-downloads.s3.amazonaws.com/CCCSO/CCCSO_CCW_PROOFOFTRAINING.pdf ·
.../CCCSO/BOF+4502.pdf · city pages: www.antiochca.gov/police/concealed-carry-weapon/ ·
www.brentwoodca.gov/government/police · www.ci.richmond.ca.us/82/Police-Department ·
www.cityofmartinez.org/departments/police · www.oakleyca.gov/243/Police ·
www.pinole.gov/departments/police/ · www.pittsburgca.gov/services/police ·
www.sanramon.ca.gov/our_city/departments_and_divisions/police/faq-police ·
www.walnutcreekpdca.gov/home-policenew · phillca.gov/FAQ.aspx?QID=90

**Fresno**: fresnoso.permitium.com/ccw/start · www.fresnosheriff.org/ccw.html (404) ·
permitium-downloads.s3.us-east-1.amazonaws.com/FresnoSO/fresno_nonresident_instructions.pdf

**Kern**: kernca.permitium.com/ccw/start · www.kernsheriff.org/ccw (404) ·
permitium-downloads.s3.us-east-1.amazonaws.com/kern/ccw_vendor_list.pdf

**San Francisco**: sfso.permitium.com/ccw/start · www.sfsheriff.com/ ·
www.sfsheriff.com/concealed-carry-weapons-license

**Ventura**: venturaca.permitium.com/ccw/start · www.venturasheriff.org/ccw/ (404) ·
sheriff.venturacounty.gov/public-resources/carry-a-concealed-weapon-ccw/

**San Joaquin**: sanjoaquinca.permitium.com/ccw/start · www.sjgov.org/sheriff/ ·
www.sjsheriff.org/ccw/ (does not resolve)

**San Mateo**: sanmateoca.permitium.com/ccw/start · www.smcsheriff.com/ccw (404)

**Stanislaus**: stanislausca.permitium.com/ccw/start · www.scsdonline.com/ccw (403)

**Sonoma**: sonomaca.permitium.com/ccw/start · www.sonomasheriff.org

**Tulare**: tulareca.permitium.com/ccw/start ·
tularecounty.ca.gov/sheriff/community/ccw-instructor-list

**Santa Barbara**: santabarbaraca.permitium.com/ccw/start

**Solano**: solanoso.permitium.com/ccw/start ·
www.solanocounty.com/depts/sheriff/pubinfo/weaponslicense.asp ·
content.solanocounty.gov/sites/default/files/2026-07/Solano_County_CCW_Approved_Trainers.pdf

**Monterey**: montereyso.permitium.com/ccw/start · mcso.countyofmonterey.gov/concealed-carry ·
www.montereysheriff.org/

**Placer**: placerca.permitium.com/ccw/start ·
www.placer.ca.gov/departments/sheriff/concealed-weapon-permits/ccwfaq · www.placersheriff.org

**San Luis Obispo**: sloca.permitium.com/ccw/start ·
www.slosheriff.org/ · /concealed-carry-weapon/ · /faq/ccw-faq/ ·
www.slosheriff.org/wp-content/uploads/2025/08/Approved-CCW-Qualification-Vendors.pdf ·
www.slocounty.ca.gov/departments/sheriff-coroner ·
permitium-downloads.s3.us-east-1.amazonaws.com/SLOSO/NONRESIDENT+INSTRUCTIONS.pdf

**Merced**: mercedca.permitium.com/ccw/start · www.co.merced.ca.us/87/Sheriffs-Office ·
www.co.merced.ca.us/3266/CCW-Approved-Instructor-Classes

**Santa Cruz**: www.santacruzsheriff.org/ (403) ·
www.santacruzsheriff.org/services/concealed-carry-weapons-ccw (403) ·
www.santacruzcountyca.gov/ · www.scsheriff.com/ ·
www.scsheriff.com/SheriffHome/INeedTo/ConcealedCarryWeapon(CCW).aspx ·
/Portals/1/County/sheriff/formsdocs/CCW%20policy%204_25.pdf ·
/formsdocs/CCW Checklist, FY 26-27.pdf ·
/formsdocs/1%20Approved%20CCW%20Instructor%20list%20062026.pdf ·
/formsdocs/SCSO%20CCW%20Instructor%20requirments2%203_17.pdf ·
/formsdocs/PBIQ_v2.pdf · /formsdocs/CCW-Employment_Residence-History.pdf ·
/formsdocs/BOF%204012%20%28FINAL%29%20-%20Rev_%2008_05_2026.pdf ·
/formsdocs/nonresident-ccw-application-bof-4013-2026-updated.pdf ·
/formsdocs/Sensitive%20places%20outline%20for%20website%20042025.pdf ·
www.scsheriff.com/SheriffHome/AboutUs/MonthlyAgencyStatistics.aspx (empty body)

**Marin**: marinca.permitium.com/ccw/start · www.marinsheriff.org/services/ccw ·
www.marinsheriff.org/assets/downloads/License_to_Carry_a_Firearm.pdf (**404**) ·
instructor sites linked from the CCW page: 2afirearmsacademy.com/marin-county-ccw/ ·
daccw.com/ccw-classes · execushield.com/ccwcourse/ · ggccw.biz

**Butte**: butteca.permitium.com/ccw/start · www.buttecounty.net/sheriffcoroner ·
www.buttecounty.net/sheriffcoroner/1722/Apply-for-a-CCW

**Yolo**: yoloca.permitium.com/ccw/start · www.yolocountysheriff.com/ ·
yolocountysheriff.com/services-resources/concealed-weapons-permit-info/

**El Dorado**: eldoradoca.permitium.com/ccw/start · www.edso.org/ccw (403)

**Imperial**: imperialca.permitium.com/ccw/start · icso.imperialcounty.org/

**Del Norte**: delnortesoca.permitium.com/ccw/start (and /entry) ·
www.co.del-norte.ca.us/departments/sheriff · /departments/Sheriff/CCW · /dnso ·
delnortesheriff.org (does not resolve)

**Glenn** (all blocked): www.countyofglenn.net/ ·
/dept/sheriff/welcome · /dept/sheriff/ccw · /dept/sheriff/concealed-weapons-permit

**Colusa**: www.countyofcolusa.org/151/Sheriff · /152/Sheriffs-Office ·
/407/Concealed-Weapons-Permit (404) · /459/Sheriffs-Office (404) ·
/search?searchPhrase=CCW (no CCW result) · colusasheriff.com, colusasheriff.org,
colusacountysheriff.com, sheriff.countyofcolusa.org (none resolve)

**Plumas**: plumassoca.permitium.com/ccw/start ·
www.plumascounty.us/158/Sheriffs-Office · www.plumascounty.us/2492/Concealed-Weapons-Permit ·
permitium-downloads.s3.us-east-1.amazonaws.com/PlumasInstructorList.pdf ·
www.plumassheriff.org (does not resolve)

**Inyo**: inyoso.permitium.com/ccw/start · www.inyocounty.us/ ·
www.inyocounty.us/sites/default/files/2025-04/2025%20CCW%20TRAINING%20AND%20TRAINERS_0.pdf

**Mono**: monoca.permitium.com/ccw/start · monosheriff.org/sheriff/

**Mariposa**: mariposaca.permitium.com/ccw/start ·
www.mariposacounty.org/622/Concealed-Weapons-Permits · /82/Sheriffs-Office

**Amador**: amadorsoca.permitium.com/ccw/start · www.amadorgov.org/departments/sheriff (403) ·
www.amadorsheriff.org/administration-division/public-information/concealed-weapons-permits ·
permitium-downloads.s3.us-east-1.amazonaws.com/Amador_CA/ccw_vendor_list.pdf

**Lassen**: lassensoca.permitium.com/ccw/start ·
www.lassencounty.org/dept/sheriff/sheriff-home · /dept/sheriffs-office/carry-permits-ccw ·
permitium-downloads.s3.us-east-1.amazonaws.com/LassenAug26InstructorList+.pdf ·
lassensheriff.org (does not resolve)

**Trinity**: www.trinitycounty.org/Sheriff · /193/Sheriff ·
/DocumentCenter/View/4295/CCW-Application-PDF (generic DOJ BOF 4012 Rev. 09/2026) ·
/1012/Concealed-Weapons-Permits (404) · trinitysheriff.org (does not resolve)

**Modoc**: modocsheriff.us/ · modocsheriff.us/777/Concealed-Carry-Weapons (no CCW content) ·
www.co.modoc.ca.us/departments/sheriff (404) · /sheriff (404) ·
/departments/sheriff-coroner (404) · modocca.permitium.com ("Former Customers")

**Sierra**: sierracounty.ca.gov/175/Sheriffs-Office · /835/Concealed-Carry-Weapon-CCW ·
/Search/Results?searchPhrase=concealed · /documentcenter/view/9652 (CCW License Procedure) ·
/DocumentCenter/View/72/Concealed-Carry-Weapon-Policy- (scanned, no text layer) ·
/DocumentCenter/View/11816/Approved-CCW-Instructors ·
/DocumentCenter/View/4397/CCW-Qualifications ·
/DocumentCenter/View/10700/BOF-4012... · /DocumentCenter/View/11570/BOF-4013... ·
/DocumentCenter/View/11622/Requirements-for-an-Out-of-State-CCW ·
/DocumentCenter/View/3359/CCW-License-Amendment · /188/Sheriff (404) ·
/176/Concealed-Weapons-Permits (wrong page) · sierracountysheriff.org (does not resolve)

**Alpine**: alpinesoca.permitium.com/ccw/start · www.alpinecountyca.gov/204/Sheriff ·
/159/Sheriff · /151/Sheriff (404) ·
permitium-downloads.s3.us-east-1.amazonaws.com/Alpine+PD/CCW_Instructors.pdf ·
permitium-downloads.s3.us-east-1.amazonaws.com/AlpineSOCA/AlpineSOCA_CCW_NonResidentCourses.pdf

**State**: openjustice.doj.ca.gov/data (3-KB app shell, no content) ·
oag.ca.gov/firearms/ccw (404) ·
oag.ca.gov/system/files/media/Firearms-Prohibited-Categories.pdf ·
oag.ca.gov/sites/all/files/agweb/pdfs/firearms/forms/prohibcatmisd.pdf

All HTML and PDF retrieved for this packet is cached under
`corpus/counties/raw/ccw/` so none of it needs refetching.
