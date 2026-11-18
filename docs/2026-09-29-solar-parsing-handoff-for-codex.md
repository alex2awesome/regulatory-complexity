# Solar parsing: handoff to Codex (2026-09-29)

Codex execution/status: [takeover record](2026-09-29-solar-adu-codex-execution.md).
The §2a packets were completed as `CODEX_SOLAR_0001`–`0009`; original Claude
reservation states are preserved with reassignment metadata, not new unread work.
S1 reading completed at 16:28 UTC on September 29: 230 packets, 4,055 threads,
64,902 held comments, 6,851 staged episode records. Canonical unread trees and
future arrivals remain open; the historical counts below describe the handoff.

**Ownership update, explicitly approved by Alex on September 29:** Codex now
owns Gemma screening of the **existing held canonical backlog**, starting at
wave 73. Claude retains acquisition and screening of new-arrival S2/S3/etc.
The existing-pool snapshot will bound this split. **Solar readers must read
every held comment, including long threads; no ADU-style excerpts.** Gemma is
only a prefilter, never a substitute for contextual extraction. No Arctic Shift
calls by Codex. Historical instructions/counts below otherwise remain intact.

**Wave73 screening is complete (20:15 UTC checkpoint):** 9,593 frozen held
threads / 9,671 screening chunks, no aborted, truncated or unparseable responses.
There are 7,247 retained threads plus 117 blind audit threads selected from
2,346 screen-outs. The resulting **391 full-reader packets contain 7,364
threads and 134,603 held comments**, `CODEX_SOLAR_0240`–`0630`. These are queued,
not yet read. All screen-outs remain explicitly unread. The frozen pool and
screen results are under `parse/claude_bulk/gemma_screen/wave73/`; canonical
reservations use separate Codex queue/index files, not Claude's.

Alex asked Codex to take over **Solar parsing (reading/extraction)**. Claude (ADU session) keeps
**Solar acquisition** (sole Arctic Shift operator, from sk3) and Gemma triage, and will keep
delivering new, triaged threads. This note says what exists, what to parse in what order, how, and
what not to touch.


## PRIORITY SHIFT (2026-09-30) -- read this first
Per-project administrative data now exists for the agency-recorded clocks
(`runs/admin_data_20260929/`, integration plan `docs/2026-09-29-admin-data-integration-plan.md`):
DG Stats (2.2M solar interconnections: received -> complete -> PTO), SF / LA City / LA County /
San Diego / Sacramento / San Jose permits (filed -> issued -> final, ADU and solar flags), HCD APR.
For those clocks forum reports cannot move population estimates; their remaining role there is
calibration (how reports differ from recorded dates in the same city/utility/year). So:

1. **Extraction priority is burden, not agency timing.** When reading, spend effort on what permit
   records cannot see: pre-application / pre-submittal time and steps (design, zoning checks,
   pre-app meetings); deterrence and abandonment before applying; correction/plan-check rounds,
   failed inspections, resubmissions and what triggered them; money (fees, required upgrades such
   as panel/sewer/meter, consultants) and effort (hours, visits, calls); installer/HOA/utility-side
   steps (contract -> permit submission, HOA approval, meter swap); whole-journey linkage of one
   project's phases; and the rule or practice the speaker says caused a delay.
2. **Timing claims are still recorded, with events.** Every timing claim records `start_event` and
   `end_event` from the fixed list (application_submitted, application_complete, permit_issued,
   construction_start, final_or_co, interconnection_submitted, pto, plus pre-application events:
   design_start, contract_signed, preapp_meeting, hoa_approval) -- no new free-form clock names.
   This makes forum claims joinable to the admin cells.
3. **Reading order.** Rank remaining threads by burden signals in Gemma's located items (ADU acts
   issue_corrections, respond_to_corrections, fail_inspection_or_require_reinspection,
   withdraw_or_abandon, pre_submittal/check_zoning; Solar failed_inspection_or_correction,
   cancel_or_abandon, delay_or_waiting, hoa_approval) and stop a batch when burden yield drops.
4. **Modeling.** Do not grow timing-only fits for clocks the admin data covers; those become
   admin-anchored with a forum reporting offset (plan steps 8-10). Forum-only modeling effort goes
   to step counts, correction rounds, costs, pre-submittal time and abandonment.

## 1. Where things stand (numbers from `parse/claude_bulk/bulk_status.py`, 2026-09-29)

Solar root: `runs/solar_forum_20260922/` (all paths below are relative to it unless absolute).

| item | count |
|---|---:|
| Claude reader packets created (`parse/claude_bulk/CLAUDE_SOLAR_*`, `CLAUDE_EXT_*`, `CLAUDE_INDEP_*`) | 741 |
| &nbsp;&nbsp;state `completed_staged_pending_root_review` | 729 |
| &nbsp;&nbsp;state `reserved_unassigned` (built, **never read**) | 9 |
| &nbsp;&nbsp;state `withdrawn_superseded` | 3 |
| threads with a completed coverage disposition | 14,293 (7,942 `process_evidence_extracted`, 6,351 `read_no_process_evidence`) |
| staged contributor episodes | 18,764 (distinct authors <= 11,002; 2,657 authors in >1 packet -- candidate links, NOT merged) |
| staged action / timing / cost / effort claims | 23,139 / 15,063 / 4,952 / 712 |
| **model-consumed claims** | **0** -- every Claude packet is `staged_not_model_consumed` |
| canonical comment trees held (`acquisition/forum/posts/`) | 26,863 |
| national posts with no tree yet | ~88,600 (see section 2c) |

**Codex lineage clarification:** the zero above describes the packet-level
staging flags, not all historical model use. The 2026-09-23 bulk adoption has
115 distinct claims reaching usable fits; see the linked execution record and
`runs/solar_bulk_adoption_20260923/result001/`. New takeover packets are still
staged, and the 2026-09-29 older-Claude candidate compilation has not been fitted.

The Claude reader session is idle (weekly model cap). Its readers are finished; nothing is running.

## 2. What to parse, in priority order

### 2a. The 9 built-but-unread packets
`parse/claude_bulk/CLAUDE_SOLAR_0721` ... `CLAUDE_SOLAR_0729` (state `reserved_unassigned`; each has
`reservation.json` and a rendered `source_text.txt`). Read them first. Record the reassignment by
adding a field to `reservation.json` (e.g. `"reassigned_to": "codex", "reassigned_at": ...`); do not
delete or rewrite the Claude fields.

### 2b. Solar batch S1: 4,055 new threads, already Gemma-screened (highest value)
`runs/solar_census_20260928/batch_s1/`:
- `raw/<thread_id>.json` -- 5,792 full comment trees fetched 2026-09-28 from sk3 (the top three
  post-triage tiers of the national posts that had no tree; see `../pending_posts_ranked.json`).
  Capture format: `post` (Arctic post record), `comments` (flat list of Arctic comment records with
  `id`, `parent_id`, `author`, `body`, `created_utc`, `author_flair_text`), `n_comments`,
  `comment_status`, `collapsed_more_stubs`, `found_via_topics`. It lacks the Solar archive's
  `declared_num_comments` / `returned_comment_count` / `limit_reached` / `california_screening_clues`;
  `render_packet.py` renders these files correctly (missing fields print as None).
- `packets.json` -- the **4,055 threads Gemma kept**, sorted by `priority_score`, each with Gemma's
  located items (`gemma_items`: path, speaker, kind, california, acts, summary). 2,523 are
  "strong" (an `own_installation` item placed in California). Read strong ones first.
- Screening prompt and validation: `runs/solar_census_20260928/build_solar_gemma.py`,
  `validation/` (recall 96.2% on threads Solar readers placed in California; it deliberately drops
  out-of-state installs and equipment-only threads, so it is narrower than the readers' nationwide
  lifecycle scope). **Do not re-screen S1**; the 1,737 threads Gemma did not keep are recorded as
  screened out in `batch_s1/triage_report.json` / `packets.json` absence -- if you want an audit
  sample (the existing `gemma_wave.py` uses 5%), pack a random 5% of them without telling readers.
- Build packets with sources pointing at these files (`source_path` =
  `runs/solar_census_20260928/batch_s1/raw/<id>.json`, `sha256` of the file bytes), then
  `render_packet.py`. These threads are NOT in `acquisition/forum/posts/`; none was read before.

### 2c. Held canonical trees not yet read
Unread trees in `acquisition/forum/posts/` (26,863 held minus reviewed, reserved and Gemma-screened-
out). The existing flow handles exclusion and screening; continue its wave numbering (last wave: 72):
```
cd runs/solar_forum_20260922
python3 parse/claude_bulk/gemma_wave.py prepare 73
<repo>/pipeline/procbench/infra/gemma/gemma_remote.sh run parse/claude_bulk/gemma_screen/wave73/input.jsonl solar_screen_wave73_<date> --max-model-len 16384
<repo>/pipeline/procbench/infra/gemma/gemma_remote.sh fetch solar_screen_wave73_<date> parse/claude_bulk/gemma_screen/wave73/
python3 parse/claude_bulk/gemma_wave.py apply 73
```
Gemma runbook (GPUs, gotchas, the `GEMMA_GPU` pin, aborted-request handling): `docs/gemma-runbook.md`.

### 2d. Arriving over the next ~3 days (Claude delivers; Codex parses)
A multi-topic Reddit census is running on sk3 (`runs/solar_census_20260928/README.md`): every
2016-2025 post+comment in 528 California subreddits (topic `solar`) and California-naming items in
15 national solar + 16 national home subreddits (`solar_ca`). Claude will fetch the hit threads
(skipping everything already held), Gemma-triage them, and add each batch as
`runs/solar_census_20260928/batch_s2/`, `batch_s3/`, ... with the same `raw/` + `packets.json`
layout, logged in `runs/solar_census_20260928/SOLAR_TRIAGE_LEDGER.md`. Parse them like 2b as they land.

## 3. How to read (unchanged method)
- Follow `parse/claude_bulk/READER_BRIEF.md` exactly (521 lines; the "If you read nothing else",
  "Semantics that must survive", field rules, `censoring` vocabulary, geography invariant,
  utility-name traps, `lifecycle_stage`, `non_registry_actions` field names, the four outputs, and
  "write output as you go" sections are all enforced downstream), plus every
  `parse/claude_bulk/known_issue_*.json`, `lifecycle_crosswalk.json`,
  `censoring_crosswalk.json`, `action_polarity_crosswalk.json`, and `parse/SOLAR_PARSE_HANDOFF_RULES.md`.
- Per packet: reserve (write `reservation.json` before reading), render, read every held comment,
  write `decisions.json`, `coverage.json`, `timing_staged.json`, `manifest.json`, then run
  `python3 parse/claude_bulk/check_packet.py <packet>` once (one bounded mechanical check, not a
  verification campaign). Commenters' own installations are separate episodes; California
  commenters inside national/non-California OP threads count; no title-only or keyword-only rejection.
- **Packet ids:** use your own prefix (e.g. `CODEX_SOLAR_0001`) in the same directory layout so ids
  never collide with Claude packets, and so `bulk_status.py`-style tallies can include both. If your
  existing Codex reservation convention (SOL0xx/LUNA0xx) is preferable, keep it, but check both
  reservation sets before reserving a thread -- a thread is read once.
- **Cross-packet people:** readers see one packet; `cross_packet_author_index.json` lists authors in
  more than one packet. Linking the same installation across packets is an integration decision
  (yours), never an automatic merge on username.
- **Model routing** (CLAUDE.md, Alex 2026-09-20): readers on GPT-5.6 **Sol** (contextual
  multi-comment parsing); Luna for mechanical checks; Astra only for consequential ambiguity.
- **Excerpts vs full reads:** `packets.json` carries Gemma's located paths. The ADU project
  validated reading short threads whole and long ones (>20k chars) as Gemma excerpts (97% of the
  quotes coders used were inside), but READER_BRIEF says read all held comments. Default to full
  reads; switch to excerpts for long threads only if Alex approves it for cost.

## 4. The bigger Codex job this unlocks
All 729 completed Claude packets (18,764 episodes) are `staged_not_model_consumed`. Root review and
adoption into the Solar model inputs -- dedup of cross-packet authors, geography weighting, clock
alias adoption, admission into the timing/structure fits -- is Codex's integration work, and the
new packets from 2a-2d feed the same path. Nothing from the bulk reading reaches a fit until that
happens.

## 5. Do not
- Call the Arctic Shift API (Claude is the single operator; the laptop collector was stopped
  2026-09-28 and must stay stopped -- `acquisition/forum/claude_driver/STOP`).
- Modify or delete Claude packets `CLAUDE_*_0001`..`0729`, their coverage, or the captures in
  `acquisition/forum/` or `runs/solar_census_20260928/*/raw/` (read-only; bind by sha256).
- Commit, delete, or start synthetic/CalFresh work (standing rules in CLAUDE.md).
- Treat Gemma's labels as extraction: Gemma only ranks and screens; readers extract everything.

## 6. Contacts / files
- Acquisition + triage status: `runs/solar_census_20260928/README.md`, `SOLAR_TRIAGE_LEDGER.md`.
- Reading status: `python3 runs/solar_forum_20260922/parse/claude_bulk/bulk_status.py`.
- Earlier handoffs: `docs/2026-09-22-solar-download-and-reading-handoff.md`,
  `docs/scoping/SOLAR_BULK_HANDOFF.json`.
