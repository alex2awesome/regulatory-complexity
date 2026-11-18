---
pretty_name: Regulatory complexity project data
license: other
language:
- en
tags:
- law
- regulation
- administrative-burden
- permitting
- reddit
- government-records
- synthetic-data
size_categories:
- 100K<n<1M
---

# Regulatory complexity: project data

All the data behind the Stanford RegLab project on regulatory complexity and administrative burden
(Alexander Spangher, Dan Ho, Sanmi Koyejo; the rule-following work is with Isabel). The project asks
what a rule costs the people subject to it: how many steps, how much waiting and how much money a permit
or benefit takes. It then asks which drafting changes would cut that cost while changing outcomes for as
few people as possible.

The code lives in the private GitHub repo
[`alex2awesome/regulatory-complexity`](https://github.com/alex2awesome/regulatory-complexity). This
dataset holds everything that code reads or writes that is too large for git, or is not code:

- the sources we gathered;
- the synthetic worlds we generated;
- every experimental run;
- the project's folders from the RegLab servers.

**At a glance:** {{TOTALS}}

## What the data is for

The project has three research threads. Each uses a different slice of this dataset.

| Thread | Question | Main data here |
|---|---|---|
| Process and burden models | How long does a California rooftop-solar or ADU (accessory dwelling unit) permit take, in how many steps, at what cost, with calibrated uncertainty? | Forum reports (`runs/solar_forum_*`, `runs/adu_forum_*`, `scratch/multi_census`), administrative permit records (`scratch/admin_data_*`, `corpus/counties`), HCD review letters and city ordinances (`runs/adu_hcd_letters_*`, `runs/adu_ordinances_*`), fits (`runs/real_process_*`) |
| Synthetic benchmark | Can the models recover a planted statute, process and burden from rendered evidence? | `benchmark/synth/worlds/`, `runs/bayes_v*`, `runs/w2_v6_*`, `runs/toy_statute*` |
| Rules, readings and loopholes | Which readings does a rule's text admit, which do AI agents act on, and how do definitions change the loophole surface? | `runs/rulegap_*`, `scratch/rulegap_gemma_*` |

A procurement study (`runs/procurement_*`, `scratch/procurement_*`) measures cycle times in California
state purchasing, and the nine-program real-world benchmark (`corpus/realworld`, `runs/rw_*`) covers
CalFresh, CPRA requests, DROS, N-400 and others.

## Kinds of content

| Kind | Where | Notes |
|---|---|---|
| Public government records | `corpus/counties`, `corpus/realworld`, `scratch/admin_data_*`, `scratch/procurement_*`, `runs/adu_hcd_letters_*`, `runs/adu_ordinances_*` | Downloaded as published: CSV, XLSX, PDF, HTML. Each fetch run has a `manifest.jsonl` (url, bytes, sha256, fetched_at) where one was kept. |
| Statute and regulation text | `corpus/ab2533`, `corpus/adu`, `corpus/realworld/*/raw`, `corpus/tax` | Verbatim from official sources (leginfo for California codes). `corpus/tax` is the third-party SARA dataset. |
| Forum text | `corpus/counties/reddit_raw`, `runs/*forum*`, `runs/*census*`, `runs/adu_triage_*`, `runs/houzz_triage_*`, `scratch/adu_*`, `scratch/multi_census` | Reddit posts and comments (from the Arctic Shift archive API), Houzz threads (Internet Archive captures) and other public forums, as collected: text, author names, timestamps, ids. |
| Model outputs | throughout `runs/` | Transcripts, parses and labels from GPT-5.6 (Codex CLI), Claude (Claude Code CLI) and Gemma 4 31B (offline batch on the RegLab GPUs). Outputs quote the forum and government text they read. |
| Synthetic worlds | `benchmark/synth/worlds/` | Generated statutes, processes, cases and rendered evidence, **with their answer keys** (`truth/`, `private/`). |
| Fits and results | `runs/bayes_*`, `runs/w2_v6_*`, `runs/real_process_*`, `runs/toy_*`, `runs/solar_panel_*` | Posteriors, draws (`.npz`, `.json`), diagnostics, comparisons, logs. |

## Layout and format

Each top-level folder is one `.tar.gz`, stored at the path it has in the code repo:

```
corpus/<source>.tar.gz                  gathered sources
benchmark/synth/worlds/<world>.tar.gz   synthetic worlds
runs/<run>.tar.gz                       one archive per run; runs/_files.tar.gz holds runs/README.md
scratch/<folder>.tar.gz                 server folders from sk3:/dfs/scratch0/alexspan
MANIFEST.jsonl                          one row per archive: source, n_files, bytes, sha256
```

- Archives under `corpus/`, `benchmark/` and `runs/` unpack to their full repo path (`runs/<run>/...`).
- Archives under `scratch/` unpack to `<folder>/...`.
- Inside a run, names follow the code repo's conventions:
  - dated folders (`YYYYMMDD`);
  - numbered attempts (`001`, `002`);
  - `README.md`, `RESULTS.md` or `manifest.json` at the top where one was written.
- Most runs are described in a dated doc under `docs/` in the code repo. The docs cite run paths, so
  searching the docs for a run name finds them.

## Download and restore

Everything (needs access to this private dataset):

```sh
hf download alex2awesome/regulatory-complexity-data --repo-type dataset --local-dir data_download
python scripts/archive_to_hf.py restore data_download   # run from the code repo
```

One archive or one group:

```sh
hf download alex2awesome/regulatory-complexity-data --repo-type dataset --local-dir data_download \
    --include "runs/adu_hcd_letters_20260923.tar.gz" "corpus/*"
tar xzf data_download/runs/adu_hcd_letters_20260923.tar.gz -C .   # unpacks to runs/adu_hcd_letters_20260923/
```

`restore` unpacks repo archives to their repo paths and server archives under `scratch/`. Move or
symlink `corpus/`, `runs/` and `benchmark/synth/worlds/` into the code repo root; many tests read them.
To check a download, compare `sha256sum` against `MANIFEST.jsonl`.

## Archive index

Sizes are compressed. "Not uploaded" means the archive was skipped or failed; the reason is in
`runs/hf_archive_20261117/` in the uploader's copy.

{{ARCHIVE_INDEX}}

## Main external sources

| Source | Publisher | What it gives | Where |
|---|---|---|---|
| Annual Progress Reports, Tables A and A2 | California HCD | Housing permits by jurisdiction with application, entitlement, permit and completion dates | `corpus/counties/raw`, `scratch/admin_data_*/hcd_apr` |
| ADU review letters | California HCD | Findings that local ADU ordinances violate state law, with the provision quoted | `runs/adu_hcd_letters_20260923` |
| CA DG Stats interconnection data | CPUC and utilities | Rooftop-solar application, approval and permission-to-operate dates, 1982 to 2026 | `scratch/admin_data_*/ca_dgstats` |
| City and county permit data | DataSF, LADBS, LA County EPIC-LA, San Diego DSD, Sacramento, San Jose | Building permits with filing, issue and completion dates; ADU and solar flags | `scratch/admin_data_*` |
| Tracking the Sun; SolarTRACE; SolarAPP+ reports | LBNL; NREL | Solar install records; permitting and interconnection timelines by jurisdiction | `scratch/admin_data_*`, `runs/rw_parse_20260918/solar_permit/source` |
| CalFresh CF296, CF18, CF256 reports | California CDSS | County caseload, application processing and timeliness | `corpus/counties/raw` |
| Civil grand jury reports | California county grand juries | Reports on local agencies | `corpus/counties/raw/exhaustive_2026_09_17` |
| SCPRS purchase records; CSCR solicitations | FI$Cal; Cal eProcure (DGS) | State purchases with dates; bid events with published and due dates | `scratch/procurement_20261021` |
| Purchase Order Data 2012 to 2015 | data.ca.gov | 344,504 purchase-order lines with creation and purchase dates | `runs/procurement_20261021/data/opendata_po` |
| Notices of intent to award; late-payment reports | Caltrans; DGS | Award and protest dates; payment timing | `runs/procurement_20261021/data` |
| County covariates | USDA ERS, Census Gazetteer, ACS, Secretary of State | Population, area, broadband, votes for 58 counties | `corpus/counties` (column sources in its README) |
| Reddit | via the Arctic Shift archive API | Posts and comments from about 560 California-local, topic and national subreddits | `scratch/multi_census`, `scratch/adu_*`, `corpus/counties/reddit_raw`, forum runs |
| Statute text | California Legislative Information | Government Code and Health and Safety Code sections | `corpus/ab2533`, `corpus/adu`, `corpus/realworld` |
| SARA | Holzenberger et al. | Statutory-reasoning benchmark on US tax law | `corpus/tax/sara` |

## How it was collected

- **Public pages and files** were fetched as a guest: no logins, no CAPTCHA or paywall bypass, at about
  one request per second, with a user agent that names the project. Where a fetcher kept one, each file
  has a manifest row (url, bytes, sha256, fetch time).
- **Reddit** was pulled from the Arctic Shift API on the sk3 server, by subreddit and by keyword, in
  censuses that record which ids are already held (`already_held_reddit_ids.txt`).
- **LLM reading:**
  - Routine parsing ran on GPT-5.6 through the Codex CLI and on Claude through Claude Code.
  - High-volume triage and closed-codebook labelling ran on Gemma 4 31B as offline batch jobs.
  - Quotes in evidence are sliced programmatically from the retained source bytes and replay exactly.
- **Synthetic worlds** come from the generator in `benchmark/synth/generator`. LLMs render the text
  evidence (`benchmark/synth/render`).

## Conventions and caveats

- **Nothing is cleaned or deduplicated across runs.** A run holds what it produced, including failed,
  unconverged and superseded attempts, which are kept on purpose. Check a run's README or its doc before
  reusing its numbers.
- **Runs depend on each other.** A later run often reads an earlier run's outputs by relative path. Restore
  the whole `runs/` tree when you can.
- **Absolute paths:** some manifests and logs record paths on the laptop or on sk2 and sk3. Treat them as
  provenance, not as paths to use.
- **Answer keys sit beside the evidence.**
  - Synthetic worlds hold their truth (`truth/`, `private/`, generator specs).
  - The real-world benchmark holds its gold (`corpus/realworld/_gold`, each `sources.json`).
  - In the project, extractors and fitters never read these. Anyone using the worlds as a held-out test
    must not look at them either.
- **Unsupported is not zero.** A report the parser could not support stays in the ledger. Unknown
  geography is not an exclusion rule.
- **Folders were scanned before upload** for API keys, tokens and private keys. A folder with a hit was
  held back and is marked "not uploaded" in the index above.

## Access and use

- This dataset is **private**.
- Government records in it are public records.
- Reddit and other forum text, and the project's parses of it, are included with the permission the project
  obtained to redistribute it. The text keeps author names and timestamps as collected.
- Model outputs quote that text.
- Third-party datasets (SARA) keep their own terms.

## Citation and contact

Stanford RegLab, regulatory complexity project (Alexander Spangher, Dan Ho, Sanmi Koyejo). There is no
paper yet. Questions go to Alexander Spangher through the GitHub repo.
