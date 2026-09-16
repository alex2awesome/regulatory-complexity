# Benchmark 1 — real-world process reconstruction (draft 2026-09-15)

**Task unit**: `(process slug, implementer, information condition)`. The solver must produce a process model in `pipeline/schemas/process_model.schema.json` form (+ `visibility`, `timing`, `fee`, `confidence`, `evidence` per activity, and an `unknowns` list) for the named implementer, from the permitted information only.

**Gold** (per task, `gold/<slug>__<implementer>.json`): the best *designed-tier* document we hold, extracted into `process_truth`-like form with `evidence` spans (e.g., Hayward's 16-activity design from handouts+questionnaire; an auditor's flowchart; a DOJ dealer manual; the USCIS Policy Manual chapter), plus `timing_gold` from official statistics where they exist (USCIS per-office times; CSLB processing dates; DOL first-payment timeliness; MuckRock per-agency response times; NREL SolarAPP+ performance). Gold is itself an artifact (error source #5): each gold file carries `gold_tier` (designed | observed) and `gold_date`, and scores are reported *per tier*.

**Information conditions** (mirror the synthetic benchmark so numbers are comparable):
| condition | solver sees |
|---|---|
| `declared_only` | statute + program page + one-hop documents (from `corpus/realworld/<slug>/raw/`, kinds statute/regulation/local_ordinance/program_page/form/checklist/faq/fee_schedule) |
| `declared_plus_users` | + reddit/forum posts (`reddit/`, user_report tier) |
| `oracle_docs` | + designed-tier documents (staff reports, SOPs, audits) — measures reconciliation capacity |
| `search` | live web via WebSearch/WebFetch + `pipeline/recon/reddit_fetch.py`, nothing pre-supplied — measures retrieval |

**Metrics**: `pipeline/procbench/score.py` (aligned activity P/R/F1 over all gold and over applicant-visible gold; actor accuracy; order agreement; rework recall; fee error; timing log-ratio vs. official; hallucination; disentanglement failures against sibling processes — e.g., CalFresh vs. Medi-Cal, CPRA vs. FOIA, ADU permit vs. AB 2533 amnesty; k-run reliability).

**Building tasks from Wave 1**: `tasks.json` is generated from each slug's `sources.json` (which lists sources by tier) and `_gold/gold_candidates.json`; a task exists only where a gold document with `gold_quality ≥ 3` AND a declared-tier footprint both exist for the same implementer. Expected v1: 8–14 tasks.

**What this benchmark cannot tell us** (and the synthetic one can): the true information ceiling — for a real process we never know what the public footprint *provably* omits, only what our gold document omits.
