# County environmental health: septic LAMPs, wells, and retail food

2026-09-16. Packet `P5-ENV-HEALTH-LAMP`; first pass and continuation by `codex-eh`.
**Audited continuation saved; packet remains partial.** No missing value
means zero, and directory links are not equivalent to verified program documents.

## Result and coverage

The strongest result is a correction to the plan: **counties are not all required
to adopt a LAMP**. Tier 1 permits can operate without one. Septic remains a strong
designed-process domain, but neither 58 approved documents nor complete annual
outcomes are guaranteed. Rural official evidence is demonstrably available; a
rural advantage in evidence volume is **not established** by either pass.

| Evidence layer | Verified/discovered coverage | Meaning |
|---|---:|---|
| LAMP inventory rows | 58 | Pending/unknown retained |
| County-specific approval/status sources | 57 | San Francisco unresolved |
| Listed or historically documented approvals | 48 | Not 48 current adopted PDFs; San Mateo corrected from stale index |
| LAMP document-link candidates | 38 | Includes old drafts, unfetched components, a malformed URL and a program link |
| LAMP documents read for sketches | 3 | Inyo 2018; Placer 2025; San Diego 2025 |
| Full current operative LAMP versions checked | 2 | Placer and San Diego; San Mateo's redlined Section 3 is only a component |
| Published 2019 county septic-count rows | 10 | Regional agency summary, not a complete statewide panel |
| Well-authority directory rows | 58 | Authorities may be districts/cities, not county EH |
| Actual well instructions/applications read | 16 | Excludes directory, generic portal, link-only and search-excerpt evidence |
| Other well leads read | 3 | Colusa application link; Inyo EH portal; Imperial authority referral |
| Historical stricter well clause verified | 1 | SLO 2019 code copy; currentness and shallow-water exception retained |
| Conclusive current county strictness classifications | 0 | Unknown, not “no stricter rule” |
| Actual weekly well report read | 1 | San Bernardino: three records, September 9–15, 2026; no elapsed-time measure |
| County food-agency directory rows | 58 | Four independent city agencies excluded |
| Food program pages/guides read | 27 | Includes three without verified plan-check requirements |
| Food plan-check requirements verified | 24 | 20 instruction/checklist sources plus four program summaries |
| Food grading/placarding systems checked | 7 | Remaining 51 unknown |
| Actual food-inspection report examples read | 2 | Plumas August 2026; Trinity March 2026 |
| Designed-process gold sketches | 3 | Septic; not observed case histories |

Machine-readable rows: [inventory](../../corpus/counties/p5_environmental_health_inventory.json).
Cached sources and extracts use the `p5_` prefix in
[raw sources](../../corpus/counties/raw/); see the
[source manifest](../../corpus/counties/p5_source_manifest.json).

## 1. Correct program scope and reporting obligations

Tier 0 covers qualifying existing systems; Tier 1 is the conservative statewide
route for qualifying new/replacement systems without an approved LAMP. Tier 2
allows approved locally developed standards. Tier 3 addresses specified impaired
waters, and Tier 4 corrective action. The state implementation page distinguishes
the 3,500-gallon/day Tier 1 threshold from the 10,000-gallon/day limit for systems
within the policy's broader scope. LAMP coverage is not synonymous with every
septic system or every part of a county.
[State OWTS guidance](https://www.waterboards.ca.gov/water_issues/programs/owts/owts_policy.html).

OWTS Policy §3.3 requires annual permit/enforcement reporting by local permitting
agencies; §§9.3.1–9.3.3 add approved-LAMP monitoring and assessment requirements.
The explicit February 1 deadline appears in Tier 2 §9.3.3; §3.3 itself specifies
annual reporting without that date. Lahontan's guidance applies February 1 to its
reporting agencies. These are **agency reporting duties,
not applicant permit-processing clocks**, and an obligation to submit is not
proof of public availability or compliance. [2023 OWTS Policy](https://www.waterboards.ca.gov/water_issues/programs/owts/docs/owts_policy_ii.pdf).

### LAMP inventory: 58 counties

`NV` means not verified. Approval status, approval date, document accessibility,
and current operative version are separate fields in the JSON. Sources are
regional-board tables unless a more informative county document or board report
was found. Annual-count links below lead to a regional summary, not necessarily
the county's original annual report.

| County | Designated board | Approval/status as reported | LAMP/document lead | Published annual evidence |
|---|---:|---|---|---|
| Alameda | R2 | [approved historical evidence; May 2018](https://www.waterboards.ca.gov/sanfranciscobay/board_info/agendas/2022/April/4_ssr.pdf) | [linked candidate](https://deh.acgov.org/landwater-assets/docs/OWTS-LAMP.PDF) | NV |
| Alpine | R6 | [approved historical evidence; 07/10/2019](https://www.waterboards.ca.gov/rwqcb6/publications_forms/available_documents/e_o_reports/2020/april_2020_eo_report.pdf) | [old draft; current PDF NV](https://www.waterboards.ca.gov/lahontan/water_issues/programs/owts/docs/lamp_tracking/alpine_lamp_11_2_2016.pdf) | [2019 counts](https://www.waterboards.ca.gov/rwqcb6/publications_forms/available_documents/e_o_reports/2020/april_2020_eo_report.pdf) |
| Amador | R5 | [approved listed; 2/24/2017](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [linked candidate](https://www.amadorgov.org/home/showpublisheddocument/42026/637849278438800000) | NV |
| Butte | R5 | [approved listed; 6/24/2016](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [linked candidate](https://www.buttecounty.net/DocumentCenter/View/4109/Local-Agency-Management-Program---Onsite-Wastewater-Ordinance-and-Manual-PDF) | NV |
| Calaveras | R5 | [approved listed; 8/11/2017](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [program](https://ema.calaverasgov.us/On-Site-Wastewater) | NV |
| Colusa | R5 | [approved listed; 6/9/2017](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [linked candidate](https://www.countyofcolusa.org/DocumentCenter/View/8764/Colusa-County-Local-Agency-Management-Program-?bidId=) | NV |
| Contra Costa | R2 | [draft historical evidence current not verified](https://www.waterboards.ca.gov/sanfranciscobay/board_info/agendas/2022/April/4_ssr.pdf) | NV | NV |
| Del Norte | R1 | [No draft submitted](https://www.waterboards.ca.gov/northcoast/water_issues/programs/owts/) | NV | NV |
| El Dorado | R5 | [approved listed; 6/9/2017](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [linked candidate](https://www.edcgov.us/Government/emd/environmentalhealth/Documents/LAMP%20FINAL.pdf) | [2019 counts](https://www.waterboards.ca.gov/rwqcb6/publications_forms/available_documents/e_o_reports/2020/april_2020_eo_report.pdf) |
| Fresno | R5 | [approved listed; 4/6/2017](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [linked candidate](https://www.fresnocountyca.gov/files/sharedassets/county/vision-files/files/39300-fresno-county-lamp-2019.pdf) | NV |
| Glenn | R5 | [approved listed; 4/7/2017](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [linked candidate](https://www.countyofglenn.net/sites/default/files/Behavioral_Health/Glenn%20County%20LAMP.pdf) | NV |
| Humboldt | R1 | [approved listed; 2/8/2018](https://www.waterboards.ca.gov/northcoast/water_issues/programs/owts/) | NV | NV |
| Imperial | R7 | [approved listed; 06/30/2016](https://www.waterboards.ca.gov/coloradoriver/water_issues/programs/owts/) | [linked candidate](https://www.icphd.org/media/managed/environmentalhealth/Imperial_County_Local_Agency_Management_Program.pdf) | NV |
| Inyo | R6 | [approved listed; 07/19/2018](https://www.waterboards.ca.gov/lahontan/water_issues/programs/owts/) | [read document](https://www.waterboards.ca.gov/lahontan/water_issues/programs/owts/docs/lamp_tracking/inyolamp_final_20180918.pdf) | [2019 counts](https://www.waterboards.ca.gov/rwqcb6/publications_forms/available_documents/e_o_reports/2020/april_2020_eo_report.pdf) |
| Kern | R5 | [approved listed; 6/9/2017 6/17/2021](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [linked candidate](https://www.kernpublichealth.com/home/showpublisheddocument/14513/638518144143570000) | [2019 counts](https://www.waterboards.ca.gov/rwqcb6/publications_forms/available_documents/e_o_reports/2020/april_2020_eo_report.pdf) |
| Kings | R5 | [approved listed; 5/31/2018](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [linked candidate](https://www.countyofkings.com/home/showpublisheddocument/20170/636947273620400000) | NV |
| Lake | R5 | [Tier 1 / LAMP pending](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [program](https://www.lakecountyca.gov/211/Environmental-Health) | NV |
| Lassen | R6 | [approved historical evidence; May 2020](https://www.waterboards.ca.gov/board_info/exec_dir_rpts/pol_per_view.html) | [old draft; current PDF NV](https://www.waterboards.ca.gov/lahontan/water_issues/programs/owts/docs/lamp_tracking/lassen_lamp_12_16.pdf) | [submission status only](https://www.waterboards.ca.gov/lahontan/publications_forms/available_documents/e_o_reports/2025/april2025eoreport.pdf) |
| Los Angeles | R4 | [approved listed; 05/21/2018](https://www.waterboards.ca.gov/lahontan/water_issues/programs/owts/) | [linked candidate](https://www.waterboards.ca.gov/lahontan/water_issues/programs/owts/docs/lamp_tracking/la_lamp_20180517.pdf) | [2019 counts](https://www.waterboards.ca.gov/rwqcb6/publications_forms/available_documents/e_o_reports/2020/april_2020_eo_report.pdf) |
| Madera | R5 | [approved listed; 4/7/2017](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [linked candidate](https://www.maderacounty.com/Home/ShowDocument?id=10376) | NV |
| Marin | R2 | [development 2026](https://www.marincounty.gov/news-releases/public-invited-west-marin-community-meetings-septic-systems) | [program](https://www.marincounty.gov/departments/cda/env-health-svcs/lamp) | NV |
| Mariposa | R5 | [approved listed; 4/7/2017](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [linked candidate](https://www.mariposacounty.org/DocumentCenter/View/53698/LAMP-Final-2017?bidId=) | NV |
| Mendocino | R1 | [approved listed; 11/4/2018](https://www.waterboards.ca.gov/northcoast/water_issues/programs/owts/) | NV | NV |
| Merced | R5 | [approved listed; 4/7/2017](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [linked candidate](https://www.countyofmerced.com/DocumentCenter/View/12618/Local-Agency-Management-Plan-LAMP?bidId=) | NV |
| Modoc | R5 | [approved listed; 2/24/2017](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [linked candidate](https://environmentalhealth.co.modoc.ca.us/LAMP%20PDF.pdf) | [2019 counts](https://www.waterboards.ca.gov/rwqcb6/publications_forms/available_documents/e_o_reports/2020/april_2020_eo_report.pdf) |
| Mono | R6 | [approved listed; 07/19/2018](https://www.waterboards.ca.gov/lahontan/water_issues/programs/owts/) | [linked candidate](https://www.waterboards.ca.gov/lahontan/water_issues/programs/owts/docs/lamp_tracking/mono_county_lamp_final.pdf) | [submission status only](https://www.waterboards.ca.gov/lahontan/publications_forms/available_documents/e_o_reports/2025/april2025eoreport.pdf) |
| Monterey | R3 | [approved listed; May 10-11, 2018](https://www.waterboards.ca.gov/centralcoast/water_issues/programs/septics/local_ag_mgnmt_plan.html) | [linked candidate](http://www.co.monterey.ca.us/home/showdocument?id=64073) | NV |
| Napa | R2 | [draft historical evidence current not verified](https://www.waterboards.ca.gov/sanfranciscobay/board_info/agendas/2022/April/4_ssr.pdf) | NV | NV |
| Nevada | R5 | [approved listed; 4/7/2017](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [linked candidate](https://www.nevadacountyca.gov/DocumentCenter/View/24677/LAMP-OWTS-For-Printing-2018?bidId=) | [2019 counts](https://www.waterboards.ca.gov/rwqcb6/publications_forms/available_documents/e_o_reports/2020/april_2020_eo_report.pdf) |
| Orange | R8 | [under review listed](https://www.waterboards.ca.gov/santaana/water_issues/programs/septic_tanks/) | NV | NV |
| Placer | R5 | [approved listed; 10/10/2025 (revised); original 4/7/2017](https://www.placer.ca.gov/DocumentCenter/View/102553/California-Regional-Water-Quality-Control-Board-Notice-of-Adoption-of-LAMP-for-Placer-County-Environmental-Health-PDF) | [read document](https://www.placer.ca.gov/DocumentCenter/View/102552/Placer-County-LAMP-Sewage-Manual-PDF) | [2019 counts](https://www.waterboards.ca.gov/rwqcb6/publications_forms/available_documents/e_o_reports/2020/april_2020_eo_report.pdf) |
| Plumas | R5 | [approved listed; 2/24/2017](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [linked candidate](https://www.plumascounty.us/DocumentCenter/View/17977/LAMP-Final?bidId=) | NV |
| Riverside | R7 | [approved listed; 11/17/2016](https://www.waterboards.ca.gov/coloradoriver/water_issues/programs/owts/) | [linked candidate](https://rivcoeh.org/sites/g/files/aldnop361/files/users/user136/2024%20Riverside%20LAMP.pdf) | NV |
| Sacramento | R5 | [approved listed; 12/11/2015](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [linked candidate](https://emd.saccounty.gov/EC/HM/Documents/LAMP%20COMBINED%20DOC%20v.2%20-%2011.29.17%20revision.pdf) | NV |
| San Benito | R3 | [in progress listed](https://www.waterboards.ca.gov/centralcoast/water_issues/programs/septics/local_ag_mgnmt_plan.html) | NV | NV |
| San Bernardino | R6 | [approved listed; 05/13/2025 revised; original 07/13/2017](https://www.waterboards.ca.gov/lahontan/board_decisions/adopted_orders/2025/docs/r6-2025-0018-resolution-sbco-lamp.pdf) | [linked candidate](https://www.waterboards.ca.gov/lahontan/water_issues/programs/owts/docs/lamp_tracking/sb_county_lamp.pdf) | [2019 counts](https://www.waterboards.ca.gov/rwqcb6/publications_forms/available_documents/e_o_reports/2020/april_2020_eo_report.pdf) |
| San Diego | R9 | [approved listed; 11/13/2024 revised; effective 02/01/2025; original 04/29/2015](https://www.sandiegocounty.gov/content/dam/sdc/deh/lwqd/finalLAMPeffective02012025.pdf) | [read document](https://www.sandiegocounty.gov/content/dam/sdc/deh/lwqd/finalLAMPeffective02012025.pdf) | NV |
| San Francisco | R2 | NV | NV | NV |
| San Joaquin | R5 | [approved listed; 4/7/2017](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [linked candidate](https://www.sjgov.org/docs/default-source/environmental-health-documents/liquid-waste/lamp-local-agency-management-plan.pdf?sfvrsn=ec3b4b0c_3) | NV |
| San Luis Obispo | R3 | [approved listed; September 25, 2020](https://www.waterboards.ca.gov/centralcoast/water_issues/programs/septics/local_ag_mgnmt_plan.html) | [linked candidate](https://www.slocounty.ca.gov/Departments/Planning-Building/Forms-Documents/Septic-System-%28Onsite-Wastewater-Treatment-Systems/County-of-San-Luis-Obispo-LAMP-2020.pdf) | NV |
| San Mateo | R2 | [approved historical evidence; 03/28/2022](https://www.waterboards.ca.gov/sanfranciscobay/board_info/agendas/2022/April/4_ssr.pdf) | [2016 component; not fetched](https://www.smchealth.org/sites/main/files/file-attachments/20160511_san_mateo_county_lamp_final_with_added_table_2-2.pdf?1642521404) | NV |
| Santa Barbara | R3 | [approved listed; November 20, 2015](https://www.waterboards.ca.gov/centralcoast/water_issues/programs/septics/local_ag_mgnmt_plan.html) | Malformed source href; see JSON | NV |
| Santa Clara | R2 | [approved historical evidence; December 2015](https://www.waterboards.ca.gov/sanfranciscobay/board_info/agendas/2022/April/4_ssr.pdf) | [linked candidate](https://www.sccgov.org/sites/cpd/programs/LU/Documents/LU_SCC_LAMP.pdf) | NV |
| Santa Cruz | R3 | [approved listed; October 14, 2021](https://www.waterboards.ca.gov/centralcoast/water_issues/programs/septics/local_ag_mgnmt_plan.html) | [linked candidate](https://scceh.com/NewHome/Programs/LandUse/LocalAgencyManagementProgram.aspx) | NV |
| Shasta | R5 | [approved listed; 10/20/2017](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [program](https://www.shastacounty.gov/environmental-health/page/onsite-wastewater-treatment-systems) | NV |
| Sierra | R5 | [approved listed; 8/2/2018](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [linked candidate](https://www.sierracounty.ca.gov/DocumentCenter/View/3830/2018-County-of-Sierra-Local-Agency-Management-Program-LAMP?bidId=) | [2019 counts](https://www.waterboards.ca.gov/rwqcb6/publications_forms/available_documents/e_o_reports/2020/april_2020_eo_report.pdf) |
| Siskiyou | R1 | [Draft reviewed by regional board staff, returned to county for revision](https://www.waterboards.ca.gov/northcoast/water_issues/programs/owts/) | NV | NV |
| Solano | R5 | [approved listed; 8/19/2016](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [linked candidate](https://www.solanocounty.gov/archival-document?document=https://content.solanocounty.gov/sites/default/files/2025-05/LAMP%20%28Final%29041816%20%281%29.pdf&ad=aHR0cHM6Ly9jb250ZW50LnNvbGFub2NvdW50eS5nb3Yvc2l0ZXMvZGVmYXVsdC9maWxlcy8yMDI1LTA1L0xBTVAlMjAlMjhGaW5hbCUyOTA0MTgxNiUyMCUyODElMjkucGRm&title=Archival%20document:%20Liquid%20Waste%20LAMP) | NV |
| Sonoma | R1 | [approved listed; 6/16/2026](https://www.waterboards.ca.gov/northcoast/water_issues/programs/owts/) | NV | NV |
| Stanislaus | R5 | [approved listed; 6/9/2017](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [linked candidate](https://www.stancounty.com/er/environmentalhealth/pdf/local-agency-management-program.pdf) | NV |
| Sutter | R5 | [approved listed; 8/11/2017](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [program](https://www.suttercounty.org/government/county-departments/development-services/environmental-health/septic-system-information) | NV |
| Tehama | R5 | [approved listed; 6/9/2017](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [program](https://www.co.tehama.ca.us/government/departments/environmental-health/) | NV |
| Trinity | R1 | [No draft submitted](https://www.waterboards.ca.gov/northcoast/water_issues/programs/owts/) | NV | NV |
| Tulare | R5 | [approved listed; 4/5/2018](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [program](https://tularecountyeh.org/eh/our-services/liquid-waste/) | NV |
| Tuolumne | R5 | [approved listed; 4/5/2018](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [linked candidate](https://www.tuolumnecounty.ca.gov/DocumentCenter/View/21757/Tuolumne-Co-LAMP) | NV |
| Ventura | R4 | [approved listed; May 4, 2018](https://www.waterboards.ca.gov/centralcoast/water_issues/programs/septics/local_ag_mgnmt_plan.html) | [linked candidate](https://docs.vcrma.org/images/pdf/eh/septic/LAMP_Approved_08072018.pdf) | NV |
| Yolo | R5 | [approved listed; 8/19/2016](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [program](https://www.yolocounty.org/government/general-government-departments/community-services/environmental-health-division/land-use-programs/onsite-wastewater-treatment-system-program) | NV |
| Yuba | R5 | [approved listed; 5/31/2018](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/) | [program](https://www.yuba.org/departments/community_development/environmental_health/land_use/sewage_disposal/index.php) | NV |

Important vintage checks:

- R5's cross-region table is headed **Date Received**, not approval date. Draft
  receipt dates must not be coded as approvals.
  [R5 LAMP index](https://www.waterboards.ca.gov/rwqcb5/water_issues/owts/lamp_reviews/).
- The R6 web tracker leaves Alpine/Lassen approval cells blank and links old
  drafts. Later reports establish Alpine approval on July 10, 2019 and list both
  counties under approved Tier 2 programs in April 2025. The State Board's
  [policy-status page](https://www.waterboards.ca.gov/board_info/exec_dir_rpts/pol_per_view.html)
  separately identifies Lassen approval at the May 2020 board meeting; the exact
  day remains unverified. County adoption is a different event.
  [2020 report, Table 2](https://www.waterboards.ca.gov/rwqcb6/publications_forms/available_documents/e_o_reports/2020/april_2020_eo_report.pdf); [2025 report, Table 3.1](https://www.waterboards.ca.gov/lahontan/publications_forms/available_documents/e_o_reports/2025/april2025eoreport.pdf).
- Placer's revised LAMP was approved October 10, 2025; the regional index still
  displays the original 2017 date. The approval notice is scanned and was checked
  visually. [Placer approval notice](https://www.placer.ca.gov/DocumentCenter/View/102553/California-Regional-Water-Quality-Control-Board-Notice-of-Adoption-of-LAMP-for-Placer-County-Environmental-Health-PDF).
- San Diego's current document is effective February 1, 2025, following regional
  approval November 13, 2024; the older index shows 2015.
  [San Diego LAMP](https://www.sandiegocounty.gov/content/dam/sdc/deh/lwqd/finalLAMPeffective02012025.pdf).
- R3's January 30, 2023 table is stale for San Mateo: the lead R2 board reports
  approval on **March 28, 2022**, plus Santa Clara approval in **December 2015**
  and Alameda in **May 2018**. The earlier R3 “July 2014” Santa Clara entry is
  not used as its approval event. This raises approval evidence from 47 to 48;
  San Benito's listed pending status remains historical/unconfirmed.
  [R2 April 2022 report, pp. 5–6](https://www.waterboards.ca.gov/sanfranciscobay/board_info/agendas/2022/April/4_ssr.pdf).
- Contra Costa and Napa were still under review in the same 2022 report; that
  does not establish their September 2026 status. Marin's separate 2026 county
  outreach indicates continued development. No missing current result is coded
  as “no LAMP.” [R2 status report](https://www.waterboards.ca.gov/sanfranciscobay/board_info/agendas/2022/April/4_ssr.pdf).
- San Bernardino's revised LAMP approval is **May 13, 2025**, using the final
  certification, not a tentative May 13-or-14 meeting label. The complete revised
  LAMP was not read. [Final Resolution R6-2025-0018](https://www.waterboards.ca.gov/lahontan/board_decisions/adopted_orders/2025/docs/r6-2025-0018-resolution-sbco-lamp.pdf).
- San Mateo currently links an October 2025 update to manual Section 3, but the
  cached PDF contains visible tracked edits and covers only conventional design
  requirements. Its approval record describes a multi-component LAMP including
  a 2021 addendum. Neither the old 2016 component nor one revised section alone
  verifies the complete current operative program.
  [County land-use documents](https://www.smchealth.org/landuse).

### Annual counts exist, but coverage is incomplete

The April 2020 Lahontan report publishes the following **2019** counts. Totals
represent reporting local agencies and can span regional-board boundaries;
they are not counts restricted to the Lahontan portion. City agencies are omitted
here. Inyo has numerical counts despite “Not Submitted” in its submission-date
column; both facts are preserved. Mono is N/R and Lassen is a pending-LAMP note,
not zero. [2020 report, Table 3, printed pp. 9–10](https://www.waterboards.ca.gov/rwqcb6/publications_forms/available_documents/e_o_reports/2020/april_2020_eo_report.pdf).

| County | New permits | Repaired/replaced systems | Submission date/status as printed |
|---|---:|---:|---|
| Alpine | 2 | 1 | 01/22/2020 |
| El Dorado | 248 | 350 | 02/14/2020 |
| Inyo | 6 | 10 | Not Submitted |
| Kern | 88 | 183 | 02/06/2020 |
| Los Angeles | 77 | 65 | 02/14/2020 |
| Modoc | 1 | 9 | 02/27/2020 |
| Nevada | 25 | 48 | 01/22/2020 |
| Placer | 182 | 48 | 02/27/2020 |
| San Bernardino | 136 | 331 | 01/24/2020 |
| Sierra | 5 | 9 | 01/31/2020 |

As of April 2025, Lahontan reported **8 of 11 local agencies** had not submitted
their 2024 annual reports and seven had not submitted five-year assessments.
These are agencies including cities, not eleven counties. Its county rows list
Inyo and Alpine's last reports as 2022, Mono and San Bernardino as 2024, and Lassen
as not submitted. Thus mandatory reporting does not produce a complete observed
panel. Original annual reports were not fetched in this pass.
[2025 report, Table 3.2, printed p. 6](https://www.waterboards.ca.gov/lahontan/publications_forms/available_documents/e_o_reports/2025/april2025eoreport.pdf).

## 2. Water wells: authority coverage is not workflow coverage

DWR's directory supplies a lead for every county. Alameda has multiple agencies;
Santa Clara and San Benito include water districts, and Ventura includes a
watershed-protection district. The county is therefore a geographic join key,
not automatically the issuing organization. All listed authorities are retained
in JSON; the table shows the first lead and flags additional entries.
[DWR permitting-agency directory](https://water.ca.gov/Well-Permitting-Agencies).

| County | DWR listed lead(s) | Checked well evidence | Above-Bulletin-74 construction comparison |
|---|---|---|---|
| Alameda | [Alameda County Environmental Health Department](https://www.acpwa.org/programs-services/water/well-program.page); +3 listed authorities | NV | NV |
| Alpine | [Alpine County Health and Human Services, Environmental Health](https://www.alpinecountyca.gov/index.aspx?NID=200) | [read instructions/application](https://www.alpinecountyca.gov/308/Well-Permits) | NV |
| Amador | [Amador County Environmental Health Department](http://www.co.amador.ca.us/departments/environmental-health) | NV | NV |
| Butte | [Butte County Public Health](http://www.buttecounty.net/ph/Environmental-Health/DrinkingWater/PrivateWaterWells) | NV | NV |
| Calaveras | [Calaveras County Environmental Management Agency](http://ema.co.calaveras.ca.us/) | [read instructions/application](https://ema.calaverasgov.us/Environmental-Health/Well-Program) | NV |
| Colusa | [Colusa County Environmental Health](http://www.countyofcolusa.org/index.aspx?NID=101) | [application link only](https://www.countyofcolusaca.gov/725/Water-Wells) | NV |
| Contra Costa | [Contra Costa Environmental Health](http://cchealth.org/eh/) | NV | NV |
| Del Norte | [Del Norte County Health & Human Services](http://www.co.del-norte.ca.us/departments/health-human-services) | NV | NV |
| El Dorado | [El Dorado County Environmental Management](https://edcgov.us/emd) | NV | NV |
| Fresno | [City of Fowler](https://fowlercity.org/water/); +4 listed authorities | [read instructions/application](https://www.fresnocountyca.gov/Departments/Public-Health/Environmental-Health/Water-Surveillance-Program/Well-Permitting-Program) | NV |
| Glenn | [Glenn County Environmental Health Department](https://www.countyofglenn.net/dept/public-health/health-human-services/environmental-health/welcome) | NV | NV |
| Humboldt | [Humboldt County Division of Environmental Health](https://humboldtgov.org/564/Environmental-Health) | [read instructions/application](https://humboldtgov.org/DocumentCenter/View/3260/Water-Well-Permit-Application-PDF) | NV |
| Imperial | [Imperial County Planning and Development Services](http://www.icpds.com/) | [authority referral only](https://www.icphd.org/environmental-health/water-programs) | NV |
| Inyo | [Inyo County Department of Environmental Health Services](http://www.inyocounty.us/EnvironmentalHealth/) | [EH portal only](https://www.inyocounty.us/services/environmental-health) | NV |
| Kern | [Kern County Department of Environmental Health Services](http://kernpublichealth.com/environmental-health/) | NV | NV |
| Kings | [Kings County](https://www.countyofkings.com/departments/community-development-agency); +1 listed authorities | NV | NV |
| Lake | [Lake County Environmental Health](http://www.co.lake.ca.us/Government/Directory/Environmental_Health.htm) | [read instructions/application](https://www.lakecountyca.gov/DocumentCenter/View/1195) | NV |
| Lassen | [Lassen County Environmental Health Department](http://www.lassencounty.org/dept/environmental-health/environmental-health) | NV | NV |
| Los Angeles | [Los Angeles County](http://publichealth.lacounty.gov/eh/AreasofInterest/waterwell.htm); +4 listed authorities | NV | NV |
| Madera | [Madera County Environmental Health Department](http://www.madera-county.com/index.php/departments-of-the-rma/environmental-health) | NV | NV |
| Marin | [Marin County Environmental Health Services](https://www.marincounty.org/depts/cd/divisions/environmental-health-services) | NV | NV |
| Mariposa | [Mariposa County Environmental Health](http://www.mariposacounty.org/index.aspx?NID=235) | [read instructions/application](http://www.mariposacounty.gov/382/Water-Wells) | NV |
| Mendocino | [Mendocino County Division of Environmental Health](https://www.mendocinocounty.org/government/health-and-human-services-agency/environmental-health) | NV | NV |
| Merced | [Merced County Department of Public Health, Division of Environmental Health](https://www.co.merced.ca.us/597/Environmental-Health); +3 listed authorities | NV | NV |
| Modoc | [Modoc County Environmental Health Department](http://www.eh.co.modoc.ca.us/) | [read instructions/application](https://www.countyofmodoc.gov/834/Wells) | NV |
| Mono | [Mono County Environmental Health Department](https://monohealth.com/environmental-health) | NV | NV |
| Monterey | [Monterey County Health Department, Environmental Health Bureau](http://www.co.monterey.ca.us/government/departments-a-h/health/environmental-health) | Official search excerpt only | NV |
| Napa | [Napa County Environmental Health Division](http://www.countyofnapa.org/PBES/Environmental/) | NV | NV |
| Nevada | [Nevada County Environmental Health Department](https://www.mynevadacounty.com/1470/Environmental-Health) | NV | NV |
| Orange | [Orange County Department of Public Health, Division of Environmental Health](http://www.ochealthinfo.com/eh); +5 listed authorities | [read instructions/application](https://www.ochealthinfo.com/services-programs/environmental-health/land-and-water/well-permitting) | Read bulletin is statewide advisory |
| Placer | [Placer County Environmental Health Department](http://www.placer.ca.gov/departments/environmental-health); +1 listed authorities | [read instructions/application](https://www.placer.ca.gov/3129/Drilling-a-Water-Well) | NV |
| Plumas | [Plumas County Environmental Health](http://www.countyofplumas.com/index.aspx?NID=174) | [read instructions/application](https://www.plumascounty.us/DocumentCenter/View/47696/well-permit-05Sep23) | NV |
| Riverside | [Riverside County Department of Environmental Health](http://www.rivcoeh.org/); +1 listed authorities | NV | NV |
| Sacramento | [Sacramento County Environmental Management Department](https://emd.saccounty.gov/) | NV | NV |
| San Benito | [San Benito County Water District](https://www.sbcwd.com/) | NV | NV |
| San Bernardino | [San Bernadiono County Environmental Health Services](http://wp.sbcounty.gov/dph/programs/ehs/) | [read instructions/application](https://ehs.sbcounty.gov/programs/safe-drinking-water/) | NV |
| San Diego | [San Diego County Department of Environmental Health](http://www.sandiegocounty.gov/content/sdc/deh/lwqd/lu_water_wells.html) | [read instructions/application](https://www.sandiegocounty.gov/content/sdc/deh/lwqd/lu_water_wells.html) | NV |
| San Francisco | [San Francisco Department of Public Health](https://www.sfdph.org/) | NV | NV |
| San Joaquin | [San Joaquin County Environmental Health Department](http://www.sjcehd.com/) | NV | NV |
| San Luis Obispo | [San Luis Obispo County Public Health Department, Environmental Health Services Division](http://www.slocounty.ca.gov/Departments/Health-Agency/Public-Health/eh.aspx) | [2019 code copy](https://supreme.courts.ca.gov/sites/default/files/supremecourt/default/documents/17-s251709-ac-county-san-luis-obispo-et-al-req-jud-notice-052019.pdf) | 2019 clause yes; current NV |
| San Mateo | [San Mateo County Environmental Health Services Division](http://www.smchealth.org/eh) | [read instructions/application](https://www.smchealth.org/sites/main/files/file-attachments/20190423_water_well_construction_procedures_final.pdf?1556046298) | 50 ft conditional/preferred; not blanket |
| Santa Barbara | [Santa Barbara County Environmental Health Services](http://cosb.countyofsb.org/phd/environmentalhealth.aspx) | NV | NV |
| Santa Clara | [Santa Clara Valley Water District](http://www.valleywater.org/) | Official search excerpt only | District indexed candidate; full source NV |
| Santa Cruz | [Environmental Health Services of Santa Cruz County](http://scceh.com/); +1 listed authorities | NV | NV |
| Shasta | [Shasta County Environmental Health Department](https://www.co.shasta.ca.us/index/drm_index/eh_index.aspx) | NV | NV |
| Sierra | [Sierra County Environmental Health Department](http://www.sierracounty.ca.gov/231/Environmental-Health) | [read instructions/application](http://sierracounty.ca.gov/645/Domestic-Wells) | NV |
| Siskiyou | [Siskiyou County Environmental Health Department](http://www.co.siskiyou.ca.us/page/environmental-health-division) | [read instructions/application](https://www.siskiyoucounty.gov/sites/default/files/fileattachments/environmental_health/page/2301/20260630_domesticwellpermitapplication.pdf) | NV |
| Solano | [Solano County Environmental Health](https://www.solanocounty.com/depts/rm/environmental_health/default.asp) | NV | NV |
| Sonoma | [Sonoma County Permit and Resources Management Agency](http://sonomacounty.ca.gov/Permit-and-Resource-Management/); +1 listed authorities | NV | NV |
| Stanislaus | [Stanislaus County Department of Environmental Resources](http://www.stancounty.com/er/); +1 listed authorities | NV | NV |
| Sutter | [Sutter County Environmental Health Services](https://www.co.sutter.ca.us/doc/government/depts/ds/ehs/cs_ehs_home) | NV | NV |
| Tehama | [Tehama County Environmental Health Department](https://www.co.tehama.ca.us/environmental-health) | NV | NV |
| Trinity | [Trinity County Environmental Health Department](http://www.trinitycounty.org/index.aspx?page=181) | [read instructions/application](https://www.trinitycounty.org/495/Water-Wells) | NV |
| Tulare | [Tulare County Environmental Health Services Division](https://tularecountyeh.org/eh/) | NV | NV |
| Tuolumne | [Tuolumne County Environmental Health](https://www.tuolumnecounty.ca.gov/244/Environmental-Health) | NV | NV |
| Ventura | [County of Ventura Watershed Protection District](https://www.onestoppermits.vcrma.org/departments/groundwater) | NV | NV |
| Yolo | [Yolo County Environmental Health Division](https://www.yolocounty.org/government/general-government-departments/community-services/environmental-health-division) | NV | NV |
| Yuba | [Yuba County Environmental Health](http://www.co.yuba.ca.us/Departments/Community%20Development/EH/) | NV | NV |

The checked pages demonstrate actual workflow variation without proving a
statewide strictness ranking:

- Placer requires a C-57 driller to apply with site/parcel maps, annular-seal
  specifications and fees; Roseville has separate permitting and Lincoln an
  additional city step. Its linked ordinance is dated **1990**, adopts Bulletin
  74 and allows special seals in designated groundwater-protection areas.
  Current codification and a like-for-like stricter numeric threshold were not
  established. [Permit page](https://www.placer.ca.gov/3129/Drilling-a-Water-Well);
  [linked ordinance, §§4.820–4.830](https://www.placer.ca.gov/DocumentCenter/View/8895/Placer-County-Well-Ordinance-PDF).
- San Diego's page describes a July 2026 policy restricting new permits for
  drillers/consultants with overdue completion reports. This is an enforcement
  condition, not evidence of slower permit review or stricter seal depths.
  [Water-well program](https://www.sandiegocounty.gov/content/sdc/deh/lwqd/lu_water_wells.html).
- Inyo's EH page links a new online permit system for wells, bores and septic;
  San Mateo's land-use page links its well procedures and ordinance. Neither
  implies the portal contains a public case-history export.
  [Inyo](https://www.inyocounty.us/services/environmental-health);
  [San Mateo](https://www.smchealth.org/landuse).


The continuation separates actual instructions (16 counties) from Colusa's
program-specific application link, Inyo's portal, Imperial's authority referral,
and official search-only leads for Monterey and Santa Clara. The latter two are
not credited as documents read.

Concrete additional workflow differences:

- **Humboldt, July 2026:** the supplemental application routes Planning review
  and, in priority basins, GSA review. It requests proposed screening interval,
  water-bearing layer, stream distances and monthly demand. Proposed use above
  two acre-feet/year calls for a geologic/hydrogeologic report, with a Public
  Water System exception; site-specific reports may also be required.
  [Current-linked supplement](https://humboldtgov.org/DocumentCenter/View/123056/Water-Well-Permit-Application---Supplemental-Attachment-PDF).
- **Lake vs. Plumas:** Lake's linked instructions require the original wet
  driller signature and reject fax/email applications; Plumas' well application
  explicitly accepts faxed signatures/authorization letters and routes intake
  to Planning and Building. These are distinct submission paths, not measured
  burden or proof one county is generally stricter.
  [Lake instructions](https://www.lakecountyca.gov/DocumentCenter/View/1195);
  [Plumas application](https://www.plumascounty.us/DocumentCenter/View/47696/Well-Permit).
- **Sierra:** EH approval precedes issuance by Building. **Trinity:** nearby
  parcel-boundary situations trigger neighbor-septic research and possibly
  additional site work; the application requires at least 72-hour seal notice.
  [Sierra workflow](http://sierracounty.ca.gov/645/Domestic-Wells);
  [Trinity application](https://www.trinitycounty.org/DocumentCenter/View/1771).
- **Siskiyou, June 2026 application:** minimum 24-hour seal notice, one-year
  permit validity and a county well-log deadline of 20 days after completion.
  The Public Trust checklist adds a Natural Resources review branch for
  production/stock wells above two acre-feet/year or with casing over six inches.
  County reporting duties are separate from DWR's 60-day filing rule, and neither
  is permit-processing duration. [Application and checklist](https://www.siskiyoucounty.gov/sites/default/files/fileattachments/environmental_health/page/2301/20260630_domesticwellpermitapplication.pdf).
- **Fresno:** GSA water-use review is a separate authority from county well
  construction. The page's historical 2021 drought inspection waiver is not
  presumed current. **Orange:** “minimum 10 business days,” depending on
  complexity, is published guidance. **San Bernardino:** “strives” for ten
  business days after complete application/payment is an aspiration. None is
  an observed duration or a common statewide deadline.
  [Fresno](https://www.fresnocountyca.gov/Departments/Public-Health/Environmental-Health/Water-Surveillance-Program/Well-Permitting-Program);
  [Orange](https://www.ochealthinfo.com/services-programs/environmental-health/land-and-water/well-permitting);
  [San Bernardino](https://ehs.sbcounty.gov/programs/safe-drinking-water/).

For **physical-standard comparisons**, DWR's general individual-domestic
annular-seal minimum is 20 feet. SLO's court-filed county-code copy dated
May 8, 2019 gives 50 feet in §8.40.060(b), but expressly exempts shallow-water
situations, never allowing less than ten feet. This is one verified **historical,
clause-specific** comparison, not a current county ranking.
[DWR §9](https://water.ca.gov/Programs/Groundwater-Management/Wells/Well-Standards/Combined-Well-Standards/Water-Construction);
[SLO code exhibit, PDF pp. 20–21](https://supreme.courts.ca.gov/sites/default/files/supremecourt/default/documents/17-s251709-ac-county-san-luis-obispo-et-al-req-jud-notice-052019.pdf).

San Mateo's actual 2019 procedures instead set 20 feet and **prefer or
conditionally require** 50 feet; coding a blanket 50-foot county minimum would
be wrong. Orange's seal bulletin expressly implements a statewide DWR advisory.
Greater protection in a specific aquifer/site, permit-routing steps and general
construction minima must remain different variables.
[San Mateo procedures](https://www.smchealth.org/sites/main/files/file-attachments/20190423_water_well_construction_procedures_final.pdf);
[Orange advisory implementation](https://www.ochealthinfo.com/sites/hca/files/import/data/files/118510.pdf).

A newly cached **actual activity source** is San Bernardino's weekly report for
September 9–15, 2026: three issued-permit records, with ENTERED date,
permit/record identifiers, location, well/work type and contractor. ENTERED is
not identified as an application date, so no processing-time interval can be
computed. The footer's “5031” is not interpreted as a permit total. One live
weekly PDF does not establish an accessible historical series.
[Weekly report](https://ehs.sbcounty.gov/wp-content/uploads/sites/97/Programs/WaterAndWaste/weekly-well-report.pdf).

DWR's Well Completion Reports are a promising statewide **construction/activity**
source, not an application-to-decision timing table. DWR identifies incomplete,
duplicate and erroneous records and often approximate locations; county joins
need coordinate/agency checks. The 60-day report-filing requirement follows
construction, alteration or destruction and is not an approval service level.
The linked public lab mirror returned HTTP 500; the underlying data were not
downloaded or counted. [DWR WCR page](https://water.ca.gov/Programs/Groundwater-Management/Wells/Well-Completion-Reports);
[mirror attempted](https://lab.data.ca.gov/dataset/well-completion-reports).

## 3. Retail food: 58 agency leads, 24 verified plan-check sources

CDPH identifies 62 local retail-food enforcement agencies: 58 county entries
(including the consolidated City and County of San Francisco) plus Berkeley,
Long Beach, Pasadena and Vernon. The four city agencies are not extra county rows.
The PDF directory contains agency home-page leads, not 58 plan-check guides.
[CDPH contact directory](https://www.cdph.ca.gov/Programs/CEH/DFDCS/CDPH%20Document%20Library/FDB/FoodSafetyProgram/RetailFood/LocalEHContacts.pdf).

| County | CDPH agency lead | Checked plan-check evidence | Grading or placarding checked |
|---|---|---|---|
| Alameda | [EH directory lead](https://deh.acgov.org/index.page) | [instructions/checklist](https://health.alamedacountyca.gov/unit/plan-check/) | [green/yellow/red plus numeric score](https://health.alamedacountyca.gov/frequently-asked-questions-food-safety/) |
| Alpine | [EH directory lead](https://www.alpinecountyca.gov/200/Environmental-Health) | [program only; plan check NV](https://www.alpinecountyca.gov/295/Food-Safety) | NV |
| Amador | [EH directory lead](https://www.amadorgov.org/departments/environmental-health) | NV | NV |
| Butte | [EH directory lead](https://www.buttecounty.net/755/Environmental-Health) | NV | NV |
| Calaveras | [EH directory lead](https://ema.calaverasgov.us/Environmental-Health) | [requirement summary](https://ema.calaverasgov.us/Environmental-Health/Food-Facility-Program) | NV |
| Colusa | [EH directory lead](https://countyofcolusa.org/101/Environmental-Health) | [instructions/checklist](https://www.countyofcolusaca.gov/425/Retail-Food-Safety) | NV |
| Contra Costa | [EH directory lead](https://cchealth.org/eh/) | NV | NV |
| Del Norte | [EH directory lead](https://www.co.del-norte.ca.us/departments/EnvironmentalHealth) | [instructions/checklist](https://www.co.del-norte.ca.us/media/CDD/Environmental%20Health/Food%20Facility%20Plan%20Check%202016.pdf) | NV |
| El Dorado | [EH directory lead](https://www.edcgov.us/Government/emd/environmentalhealth/Pages/environmental_health_main_info.aspx) | NV | NV |
| Fresno | [EH directory lead](https://www.co.fresno.ca.us/departments/public-health/environmental-health?locale=en) | [instructions/checklist](https://www.fresnocountyca.gov/Departments/Public-Health/Environmental-Health/Consumer-Food-Program/Consumer-Food-Plan-Check) | NV |
| Glenn | [EH directory lead](https://www.countyofglenn.net/government/departments/planning-community-development-services/environmental-health) | NV | NV |
| Humboldt | [EH directory lead](https://humboldtgov.org/564/Environmental-Health) | [instructions/checklist](https://humboldtgov.org/DocumentCenter/View/113445/Food-Facility-Plan-Check-Guidelines-PDF) | NV |
| Imperial | [EH directory lead](https://www.icphd.org/environmental-health/) | [requirement summary](https://www.icphd.org/environmental-health/food/food-establishments) | NV |
| Inyo | [EH directory lead](https://www.inyocounty.us/services/environmental-health) | [instructions/checklist](https://www.inyocounty.us/sites/default/files/2026-05/Food%20facility%20guidance%20document%202%20pages.pdf) | NV |
| Kern | [EH directory lead](https://kernpublichealth.com/) | NV | NV |
| Kings | [EH directory lead](https://www.kcdph.com/ehs) | [instructions/checklist](https://www.kcdph.com/_files/ugd/432956_a33f8fec7b0e4f7d83f1480b6df6845b.pdf) | NV |
| Lake | [EH directory lead](https://www.lakecountyca.gov/211/Environmental-Health) | [instructions/checklist](https://www.lakecountyca.gov/DocumentCenter/View/1146/Plan-Check-Process-PDF) | NV |
| Lassen | [EH directory lead](http://www.lassencounty.org/dept/environmental-health/environmental-health) | [instructions/checklist](https://www.lassencounty.gov/DocumentCenter/View/832) | NV |
| Los Angeles | [EH directory lead](http://publichealth.lacounty.gov/eh/) | [instructions/checklist](https://publichealth.lacounty.gov/eh/inspection/retail-plan-check.htm) | [letter grades and numeric below 70](https://publichealth.lacounty.gov/eh/inspection/grading-posting-requirements-retail-food-facilities.htm) |
| Madera | [EH directory lead](https://www.maderacounty.com/government/community-economic-development-department/divisions/environmental-health-division) | NV | NV |
| Marin | [EH directory lead](https://www.marincounty.org/depts/cd/divisions/environmental-health-services) | NV | NV |
| Mariposa | [EH directory lead](https://www.mariposacounty.org/235/Environmental-Health) | [instructions/checklist](https://www.mariposacounty.gov/DocumentCenter/View/40659) | NV |
| Mendocino | [EH directory lead](https://www.mendocinocounty.gov/departments/public-health/environmental-health) | NV | NV |
| Merced | [EH directory lead](https://www.co.merced.ca.us/597/Environmental-Health) | NV | NV |
| Modoc | [EH directory lead](https://environmentalhealth.co.modoc.ca.us/) | [requirement summary](https://www.countyofmodoc.gov/812/Food-Sanitation-Program) | NV |
| Mono | [EH directory lead](https://www.monohealth.com/environmental-health) | [program only; plan check NV](https://www.monocounty.ca.gov/1982/Food-Safety) | NV |
| Monterey | [EH directory lead](https://www.co.monterey.ca.us/government/departments-a-h/health/environmental-health) | NV | NV |
| Napa | [EH directory lead](https://www.countyofnapa.org/1904/Environmental-Health-Division) | NV | NV |
| Nevada | [EH directory lead](https://www.mynevadacounty.com/1470/Environmental-Health) | NV | NV |
| Orange | [EH directory lead](https://www.ochealthinfo.com/about-hca/public-health-services/environmental-health-division/environment-food-safety) | [instructions/checklist](https://www.ochealthinfo.com/services-programs/environmental-health/plan-check) | NV |
| Placer | [EH directory lead](https://www.placer.ca.gov/3105/Environmental-Health) | [instructions/checklist](https://www.placer.ca.gov/3357/Plan-Check) | [green yellow red placards](https://www.placer.ca.gov/5964/Placard-Program---Food-Safety) |
| Plumas | [EH directory lead](https://www.plumascounty.us/174/Environmental-Health) | [instructions/checklist](https://www.plumascounty.us/371/Opening-a-Restaurant) | NV |
| Riverside | [EH directory lead](https://www.rivcoeh.org/) | NV | NV |
| Sacramento | [EH directory lead](https://emd.saccounty.net/Pages/default.aspx) | [instructions/checklist](https://emd.saccounty.gov/content/dam/emd/docs/archive2/food-programs/How%20to%20Obtain%20Plan%20Approval%20and%20Health%20Permit%20for%20a%20Food%20Facility.pdf) | [green yellow red placards](https://emd.saccounty.gov/us/en/faqs/business-owner-operator-food-facility.html) |
| San Benito | [EH directory lead](https://hhsa.cosb.us/environmental-health/) | NV | NV |
| San Bernardino | [EH directory lead](https://wp.sbcounty.gov/dph/programs/ehs/) | [instructions/checklist](https://ehs.sbcounty.gov/programs/plan-check/) | [A90–100; B80–89; C70–79; closure0–69](https://ehs.sbcounty.gov/wp-content/uploads/sites/97/Programs/Food/FoodFacilities/abc-retail-food-inspection-guide.pdf) |
| San Diego | [EH directory lead](https://www.sandiegocounty.gov/content/sdc/deh.html) | [instructions/checklist](https://www.sandiegocounty.gov/content/sdc/deh/fhd/food/foodplancheck.html) | [letter grades](https://www.sandiegocounty.gov/content/sdc/deh/fhd/food/food_faq.html) |
| San Francisco | [EH directory lead](https://www.sf.gov/departments/department-public-health/environmental-health) | [instructions/checklist](https://www.sf.gov/sites/default/files/2023-08/ConstructGuide.pdf) | [green yellow red placards](https://www.sf.gov/information--restaurant-health-inspection-posters-and-what-they-mean) |
| San Joaquin | [EH directory lead](https://www.sjgov.org/department/envhealth/) | NV | NV |
| San Luis Obispo | [EH directory lead](https://www.slocounty.ca.gov/Departments/Health-Agency/Public-Health/eh.aspx) | NV | NV |
| San Mateo | [EH directory lead](https://www.smchealth.org/eh) | [instructions/checklist](https://www.smchealth.org/sites/main/files/file-attachments/20251230_plan_check_process.pdf?1767137649) | NV |
| Santa Barbara | [EH directory lead](https://www.countyofsb.org/414/Environmental-Health) | NV | NV |
| Santa Clara | [EH directory lead](https://deh.santaclaracounty.gov/about-us/who-we-are) | NV | NV |
| Santa Cruz | [EH directory lead](http://scceh.com/) | NV | NV |
| Shasta | [EH directory lead](https://www.co.shasta.ca.us/index/drm/ehd) | NV | NV |
| Sierra | [EH directory lead](http://sierracounty.ca.gov/231/Environmental-Health) | [program only; plan check NV](http://sierracounty.ca.gov/232/Food-Safety) | NV |
| Siskiyou | [EH directory lead](https://www.co.siskiyou.ca.us/environmentalhealth) | [requirement summary](https://www.siskiyoucounty.gov/environmentalhealth/page/food) | NV |
| Solano | [EH directory lead](https://www.solanocounty.com/depts/rm/environmental_health/default.asp) | NV | NV |
| Sonoma | [EH directory lead](https://sonomacounty.ca.gov/Health/Environmental-Health-and-Safety/) | NV | NV |
| Stanislaus | [EH directory lead](http://www.stancounty.com/er/environmentalhealth/) | NV | NV |
| Sutter | [EH directory lead](https://www.suttercounty.org/government/county-departments/development-services/environmental-health) | NV | NV |
| Tehama | [EH directory lead](https://www.co.tehama.ca.us/government/departments/environmental-health/) | NV | NV |
| Trinity | [EH directory lead](https://www.trinitycounty.org/Environmental-Health) | [instructions/checklist](https://www.trinitycounty.org/486/Food-Facilities) | NV |
| Tulare | [EH directory lead](https://tularecountyeh.org/eh/) | NV | NV |
| Tuolumne | [EH directory lead](https://www.tuolumnecounty.ca.gov/244/Environmental-Health) | NV | NV |
| Ventura | [EH directory lead](https://vcrma.org/divisions/environmental-health) | NV | NV |
| Yolo | [EH directory lead](https://www.yolocounty.org/government/general-government-departments/community-services/environmental-health-division) | NV | NV |
| Yuba | [EH directory lead](https://www.yuba.org/departments/community_development/environmental_health/index.php) | NV | NV |

Same label does not mean the same inspection outcome:

| County | Verified rule distinction |
|---|---|
| Placer | Green if major violations are absent or all corrected/mitigated by inspection end; yellow if one remains or a compliance agreement is violated. |
| Sacramento | Green permits at most one observed major violation, corrected; two or more produce yellow with a stated 24–72-hour follow-up. |
| San Francisco | Also uses green/yellow/red placards: green 0–1 major violations corrected, yellow 2+ corrected. The plan's “SF scores” description is not current. |
| Los Angeles | A 90–100; B 80–89; C 70–79; below 70 a numeric score card. |
| San Diego | A 90–100; B 80–89; C 79 or below, designated failing. |
| San Bernardino | Linked 2018 guide: A 90–100; B 80–89; C 70–79 requiring re-score; 0–69 closure. |
| Alameda | Green pass, yellow conditional pass, red closed; numeric score also reported. Exact thresholds not verified. |

Sources are the seven county grading links in the table above. Inspection grade,
closure and follow-up are distinct outcomes; none is an observed plan-check
turnaround. Placer's corrected violations could yield green when the same number
of observed-and-corrected major violations yields yellow in Sacramento or SF.
A shared color/letter must therefore retain its county-specific rule.

Inyo's two-page food guide is image-only; page 1 was rendered and read. It
requires plan check for new construction/remodels, approval before the
pre-opening inspection, specified documents, and fees. Its hourly billing
statement is **not observed staff hours**. [Inyo guide](https://www.inyocounty.us/sites/default/files/2026-05/Food%20facility%20guidance%20document%202%20pages.pdf).


Coverage is deliberately layered: **27** county food program pages/guides were
read, **24** explicitly address plan check, and **20** provide instructions or
checklists rather than a short requirement summary. Alpine, Mono and Sierra
program pages were read but did not establish plan-check instructions. They are
unknowns, not evidence that plan review does not exist.

Useful direct checklists and clocks include:

- San Mateo's **December 30, 2025 flowchart**: complete documents plus payment
  trigger a published 20-business-day initial review; revisions have a
  ten-business-day review statement. Approval lasts two years; agency approvals,
  an approximately 80%-complete pre-final inspection, final inspection and
  operating-permit steps follow. These are designed clocks, not measured cases.
  [Flowchart](https://www.smchealth.org/sites/main/files/file-attachments/20251230_plan_check_process.pdf).
- Kings invoices review-time fees with its approval/rejection letter, whereas
  Fresno requires payment before the review queue; Orange also describes an
  upload/intake/payment sequence. Billing rules are not observed staff-hours data.
  [Kings checklist](https://www.kcdph.com/_files/ugd/432956_a33f8fec7b0e4f7d83f1480b6df6845b.pdf);
  [Fresno plan check](https://www.fresnocountyca.gov/Departments/Public-Health/Environmental-Health/Consumer-Food-Program/Consumer-Food-Plan-Check);
  [Orange plan check](https://www.ochealthinfo.com/services-programs/environmental-health/plan-check).
- Del Norte's current-linked **2016** form asks for one plan set and coordinates
  Building/Planning or Crescent City; Lassen's checklist references **2023**
  CalCode and requires EH and Building approvals before work. These are real
  instructions, but publication/link currency does not certify every old fee.
  [Del Norte form](https://www.co.del-norte.ca.us/media/CDD/Environmental%20Health/Food%20Facility%20Plan%20Check%202016.pdf);
  [Lassen checklist](https://www.lassencounty.gov/DocumentCenter/View/832).
- Humboldt's guide has a February 2009 cover and a “Rev 2024” footer; Sacramento's
  guide says one plan set at intake but two returned in its flowchart. Such source
  inconsistencies are retained rather than silently normalized.
  [Humboldt guide](https://humboldtgov.org/DocumentCenter/View/113445/Food-Facility-Plan-Check-Guidelines-PDF);
  [Sacramento guide](https://emd.saccounty.gov/content/dam/emd/docs/archive2/food-programs/How%20to%20Obtain%20Plan%20Approval%20and%20Health%20Permit%20for%20a%20Food%20Facility.pdf).

**Actual rural inspection evidence is available.** The cached Plumas index
contains 1,646 distinct document links, not 1,646 facilities; a linked August 28,
2026 routine inspection was visually read. Trinity's index has 119 distinct
document links including reference/template files; its March 31, 2026 sample
contains inspection findings and corrective-action fields. Neither count is a
cleaned complete inspection census, a permit total or plan-review timing.
[Plumas index](https://www.plumascounty.us/608/Food-Facility-Inspections);
[Plumas sample](https://www.plumascounty.us/DocumentCenter/View/53894/7-Eleven-8-28-26);
[Trinity index](https://www.trinitycounty.org/488/Food-Facility-Inspections);
[Trinity sample](https://www.trinitycounty.org/DocumentCenter/View/1626/Strawhouse-PDF).

## 4. Rural-inversion verdict: not established

**Official designed evidence reaches small rural counties; greater rural evidence
volume does not follow.** Alpine, Modoc, Inyo and Sierra have published numerical
2019 septic rows; their new permits range from 1 to 6. Los Angeles has 77 and
Placer 182 in the same table. These are activity counts, not document counts,
and their jurisdictional boundaries differ. Missing reports remain an observed
disclosure problem, not no activity. Neither pass supports a monotonic
county-size/rurality relationship. Plumas/Trinity inspection archives strengthen
rural availability evidence, not a rural-versus-urban volume comparison.
[Regional comparison](https://www.waterboards.ca.gov/rwqcb6/publications_forms/available_documents/e_o_reports/2020/april_2020_eo_report.pdf).

**User-generated evidence was tested only with four matched discovery queries**:
`site:reddit.com "[County] County" septic permit`, on 2026-09-16. Inclusion:
a deduplicated thread explicitly locating a septic/well construction, permitting
or replacement question in that county. General maintenance advice, unrelated
environmental complaints and wildfire right-of-entry paperwork were excluded.
The search engine returned a bounded set, not an exhaustive corpus or calibrated
sample. Direct Reddit/API fetches were not attempted; these are search-rendered
thread excerpts, and no content was added to the protected Reddit corpus.

| County probe | Qualifying threads discovered, lower bound | Example |
|---|---:|---|
| Alpine | None returned; total unknown | No relevant hit in returned batch |
| Modoc | ≥1 | [Land purchase/cabin and septic/well questions](https://www.reddit.com/r/Homesteading/comments/167u2sd/i_bought_some_land_in_modoc_county_california/) |
| Los Angeles | ≥2 | [Unincorporated desert build](https://www.reddit.com/r/RealEstate/comments/qghacv); [previously burned parcel with septic/well](https://www.reddit.com/r/Homebuilding/comments/tsoxoa) |
| San Diego | ≥4 | [County building-permit question](https://www.reddit.com/r/Homebuilding/comments/1buj25o); [Escondido replacement options](https://www.reddit.com/r/escondido/comments/1jcx94w); [civil/perc costs](https://www.reddit.com/r/barndominiums/comments/1fruoev); [septic lot size](https://www.reddit.com/r/northcounty/comments/11agj8z) |

This small comparison gives **no positive support for rural counties having more
discoverable user evidence**. It does not establish the opposite population
effect either. Urban-classified counties contain rural unincorporated parcels;
San Diego discussions include a reported DEHQ consultation about replacement
options. A county rurality code cannot substitute for parcel sewer access or the
permitting authority.

Recommended test: septic first for designed-process coverage and boundary-aware
permit counts; wells second after extracting/cleaning WCR activity; food as the
urban exposure/control domain. Predefine rurality, year and inclusion rules;
measure distinct official documents, usable permit records and first-hand
threads separately; include unsewered households/system stock or eligible parcels
as exposure denominators. No statewide correlation or per-capita claim was
estimated here.

## 5. Three source-grounded designed-process gold sketches

These are bounded **normative workflow candidates**, not validated latent
ground-truth case paths or elapsed-time observations. Each retains actor,
artifact, conditional branch, completion event and clock type.

### A. Inyo: new OWTS, 2018 LAMP, currentness unresolved

Owner/licensed contractor submits signed application, plot plan and fee → county
REHS checks completeness and evaluates the site → soil profiles/percolation
evidence supports review → approval or denial → applicant arranges staged
construction inspections → county finalizes and distributes copies.

The REHS can set/waive testing requirements. Simple-site testing may use an
approved contractor; alternative-system cases require an engineer, geologist or
REHS. The approved signed application authorizes construction. Required
inspections cover tank integrity, excavated trenches before rock/pipe, and
installed lines; alternatives may need electrical/alarm checks.

The stated **ten-working-day** decision period follows site evaluation and
submission of required information; the director may waive/extend it. It excludes
the unresolved intake/site-work duration. The document's numbered list mixes
approval and testing discussions, so the arrows express prerequisites, not a
claim that every numbered paragraph is chronological.
[Inyo LAMP, printed pp. 20–21](https://www.waterboards.ca.gov/lahontan/water_issues/programs/owts/docs/lamp_tracking/inyolamp_final_20180918.pdf).
The live EH page also indicates a later online intake transition, so the 2018
submission interface must be revalidated before calling this current gold.

### B. Placer: new/alternative OWTS, October 2025 manual

Applicant/consultant obtains approved site evaluation → submits installation
application, fee and scaled plans including 100% replacement area → county
issues, conditionally approves or denies → preconstruction meeting unless waived
→ installation and inspections → correction/reinspection if needed →
as-builts/certification where required → satisfactory-completion certificate.

Alternative systems add a signed/wet-stamped consultant design and calculations.
Changed site conditions or a design inconsistent with the site evaluation can
cause rework or denial. The published **20-working-day** decision clock begins
at a complete application; the manual identifies incomplete/incorrect submissions
and changed designs/sites as delay conditions. Inspection requests must arrive
before 7 a.m. for the requested business day. Backfill requires written approval.

The certificate is the completion artifact, not the initial permit. No case-level
review times or staff effort were observed.
[Placer manual, construction permits and inspections, printed pp. 12–16](https://www.placer.ca.gov/DocumentCenter/View/102552/Placer-County-LAMP-Sewage-Manual-PDF).

### C. San Diego: new OWTS, effective February 2025 LAMP

Applicant/qualified professional obtains testing authorization and site evidence
→ submits OWTS Layout Report → DEHQ review/additional-information loop →
layout approval, potable-water evidence and building-application prerequisites
→ installer/owner-builder installation-permit application and fee → DEHQ decision
→ installation → inspection/corrections → final permit with required supporting
records.

Case-specific studies and supplemental-treatment requirements can add branches.
DEHQ can deny a health/water-quality risk even where minimum dimensions are met.
Work starts only after the installation permit. Inspection requires **at least
24 hours' advance notice**, but actual scheduling depends on staff availability.
A failed inspection triggers corrections and a **reinspection request within ten
business days**—an applicant obligation, not a county turnaround guarantee.
As-builts, certifications, maintenance contracts or an operating permit may be
required before finalization. No backfill before inspection/approval unless
authorized. [San Diego LAMP §3.8, printed pp. 41–51](https://www.sandiegocounty.gov/content/dam/sdc/deh/lwqd/finalLAMPeffective02012025.pdf).

## 6. Access, provenance and remaining work

Research used **60/60 search queries and 170/180 direct-source fetch attempts**
(including failed attempts, retries and uncached web opens), within the
180-minute packet budget. Tool-returned discovery evidence is cached in
`p5_web_evidence_01.txt`, `p5_web_evidence_02.txt` and
`p5_web_evidence_03.txt`; original HTML/PDFs and selected text/OCR/image
derivatives are separate. The continuation manifest retains each request URL,
HTTP outcome and source hash. No authentication, accounts, emails, access-control
bypass, covariate edits or model-code changes were used.

The manifest covers 254 cached files (144 downloaded originals; the remainder
are tool evidence or text/OCR/image derivatives), approximately 59 MB. All three
program tables reconcile to the same 58 unique counties. These are lightweight
provenance/count checks, not software/unit tests or verification of publisher
accuracy. The second-pass date corrections are also retained in JSON audit notes.

| Attempt/problem | Interpretation and disposition |
|---|---|
| Initial ordinary-shell downloads failed DNS in the restricted network context | Authorized network-enabled public downloads succeeded; not evidence county sources were unavailable. |
| [CA lab WCR mirror](https://lab.data.ca.gov/dataset/well-completion-reports) HTTP 500 | Data not fetched; DWR's official landing page still accessible. |
| LA grading `www.publichealth.lacounty.gov` TLS/SNI error, curl 35 | Canonical `publichealth.lacounty.gov` succeeded; not an access-control block. |
| R3 Santa Barbara document href begins `http:/` | Source link preserved in JSON; not silently repaired or counted fetched. |
| Placer approval notice and Inyo food guide have no usable extracted text | First pages rendered and visually read; images cached. |
| Amador, Glenn, Kern, Mendocino, Riverside, Santa Clara EH and Monterey well URLs returned HTTP 403 | No access-control bypass; county/program existence remains unknown from these failures. Exact URLs/outcomes in manifest. |
| Alameda DWR-listed well URL and old Trinity EH URL returned HTTP 404 | Alameda instructions unresolved; Trinity recovered from a current official county path. |
| Valley Water full PDF blocked by web-tool robots restriction | Official indexed excerpts are search-only; no alternate-tool bypass or full-source credit. |
| Old Lassen, Mono, Orange and San Bernardino EH URLs redirected broadly | Broad home-page success was not counted as program verification; actual linked programs fetched separately where found. |
| Del Norte food guide, SLO court exhibit and Plumas sample inspection are image-only | OCR used for navigation; cited Del Norte p. 1, SLO pp. 20–21 and Plumas sample p. 1 visually checked. |
| Plumas old well-ordinance PDF is image-only | Selected ending pages concern sewage rules; no unverified well threshold inferred from filename. |
| Numerous county links remain directory-only | Unattempted, failed, link-only, summary-only and instructions-read are distinct evidence levels. |

Acceptance audit: **58 LAMP rows, an evidence-qualified rural verdict, and three
sketches are delivered**. The continuation materially expands well/food evidence
and corrects stale approval claims. Full packet tasks remain incomplete: actual
well instructions for 42 counties, current comparable construction standards,
plan-check evidence for 34 counties, grading for 51 counties, full current LAMP
validation and original annual-report harvesting. Four of the 24 plan-check
sources are short program summaries. The packet is released rather than marked
done. Remaining retrieval should target saved program/checklist links and
unresolved agencies, not repeat broad discovery. Search budget is exhausted;
10 fetch attempts remain within the original cumulative cap.
