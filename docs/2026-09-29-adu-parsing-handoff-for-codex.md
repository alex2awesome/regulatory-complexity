# ADU parsing: handoff to Codex (2026-09-29)

Alex asked Codex to take over **ADU parsing/coding**, alongside Solar parsing
(`docs/2026-09-29-solar-parsing-handoff-for-codex.md`). Claude (ADU session) keeps acquisition (sole
Arctic Shift operator, from sk3) and Gemma triage and will keep delivering triaged threads.

ADU root: `runs/adu_forum_20260921/` (paths below relative to `runs/` unless absolute). Read
`adu_forum_20260921/RESUME.md` for the whole collection history.


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

## 1. Where things stand

**Parsed (coded, quote-verified):** 1,166 Reddit episodes in `adu_forum_20260921/parsed/*.json`
(22 slices incl. `gem1`..`gem8` coded 2026-09-24), ~270 BiggerPockets projects, 23 Houzz episodes
(question pages only), top-60 city guidance, ordinances. `python3 adu_forum_20260921/verify_all.py`
replays every quote (last run: all pass).

**Not parsed** (this handoff):

| # | item | size | state |
|---|---|---|---|
| A | new Reddit threads, Gemma-triaged | 14,680 threads, **4,423 kept, 2,458 strong** | ranked packets ready |
| B | Houzz threads recovered from the Internet Archive with ALL answers | **1,113** threads | raw HTML captured, not parsed |
| C | HCD enforcement-letter finding categories | 2,350 findings | **done 2026-09-29** (Gemma for the 647 missing; see section 4) |
| D | overlay hygiene from the 2026-09-24 coding run | ~7 duplicate speakers, ~30 vendor/astroturf candidates | listed, not applied |
| E | pre-2019 ADU threads + ADU-and-California comments in national subreddits | arriving over ~3 days | Claude delivers as triaged batches |

## 2. A: new Reddit threads (the big one)

- Captures: all 14,680 new threads are now in the canonical `adu_forum_20260921/raw_sk3/<id>.json`
  (copied 2026-09-29; same capture format as every earlier slice), so `verify_all.py` and the slice
  builder resolve them unchanged.
- Triage + ranking per batch (each `packets.json` is sorted by `priority_score` and carries Gemma's
  located items: path, speaker, kind, california, acts, summary; "strong" = an `own_project` item
  placed in California):
  `adu_bayarea_20260924/packets.json` (1,102 kept) and `adu_triage_batch{2..9}_2026092*/packets.json`.
  Ledger with every batch's counts: `adu_counties_20260926/TRIAGE_LEDGER.md`.
- Coding method (unchanged; follow exactly): `adu_forum_20260921/CONTRACT.md` (incl. amendments
  §8-12), `adu_forum_20260921/EXTRACTION_BRIEF.md`, `adu_forum_20260921/VOCABULARY.json` (20 action
  ids, verbatim), `adu_forum_20260921/adjudication/speaker_flags.json`. Per slice: a coder reads a
  packet, writes `parsed/<slice>_recoded.json`, builds an independent verifier (quote replay at
  offsets + junk screen + mutation test), incremental atomic writes. Quotes are sliced from the RAW
  capture by `json_path` + offsets, never from packet text.
- Slice builder: `adu_gemma_triage_20260924/make_slices.py` (renders a reading packet: short threads
  <20k chars whole, long threads as Gemma excerpts = post + flagged comments + same speakers +
  parents/replies; validated on 617 coded threads: 97.1% of quoted paths kept at 59% of the text).
  It currently reads `adu_gemma_triage_20260924/packets_new.json`; point it at each batch's
  `packets.json` (add a `--packets` argument) -- raw lookup already works via `raw_sk3/`.
  Coder prompt template: `adu_gemma_triage_20260924/CODER_PROMPT.md`.
- **Order and stopping:** strong threads first, highest `priority_score` first, across batches.
  Last run's yield fell from 75 episodes (top slice) to ~17 per ~100-thread slice by rank ~600
  (`adu_gemma_triage_20260924/RESULTS.md`); stop a batch when a slice yields under ~15 episodes and
  report what was left uncoded. Expected overall: roughly 800-1,200 new episodes.
- Caveat: r/Landlord and r/TinyHouses (batch 9) are national; Gemma's California flag is noisy
  there -- the contract's California gate decides.
- Model routing (CLAUDE.md): coders on GPT-5.6 **Sol**, mechanical checks on Luna.
- Dedup: several threads/speakers overlap earlier slices (the census found comment-only threads in
  the same subreddits). Before emitting, check `parsed/*.json` for already-coded speakers; new
  evidence for them goes in `cross_slice_additions`, as the gem slices did.

## 3. B: Houzz full answers (1,113 threads)
Live Houzz pages carry only the question + featured answer; Internet Archive `id_` snapshots carry
all answers in the same `hz-ctx` JSON payload. Recovered 2026-09-28 by
`adu_forum_20260921/external/houzz_contractortalk_archinect/work/houzz_wb_all.py`:
registry `work/registry_houzz_wb_all.json` (5,067 looked up: 1,113 `archived_page_captured`,
3,936 `not_archived`, 18 fetch failures), pages in `raw/houzz__<id>__wb<timestamp>__p1.html`
(+ 10 earlier ones via `registry_houzz_wb.json`). The existing Houzz parser/renderer in that
`work/` dir (`build_v2.py`, `capture.py` page_record meta `answers_in_page`) extracts answers from
`hz-ctx`; reuse it. Suggested flow: render -> Gemma triage (same ADU prompt pattern; see
`adu_gemma_triage_20260924/build_jobs.py`) -> code the kept threads under the same contract (Houzz
quotes address the archived HTML/JSON by path + offsets as the earlier Houzz slice did). Each archived
page is a snapshot at its timestamp: answers posted later are absent; say so in coverage.

## 4. C: HCD enforcement letters -- DONE by Claude (2026-09-29), no action needed
The 647 uncategorized findings were coded with Gemma 4 31B (validation on 150 frontier-coded items:
is_finding 96.0%, primary category 85.8%) into NEW files `work/llm_cats/cats_NN.gemma.out.json`
(every entry has `coded_by`; frontier `cats_NN.out.json` untouched; union = one entry per packet key
for all 12 batches). A pre-existing bug in `scripts/merge_v2.py` dropped two codebook categories
(processing_timeline_60_day, discretionary_review_or_hearing -> 'other'); fixed (old copy
`merge_v2.before_regex_fix_20260929.py`), `letters.json` rebuilt (old copy
`letters.before_gemma_and_regex_fix_20260929.json`). Optional for Codex: frontier spot-check of the
Gemma-coded items, especially is_finding.

## 5. D: overlay hygiene (cheap, do before new coding)
From `adu_gemma_triage_20260924/RESULTS.md`: concurrent-slice duplicates to reconcile in
`adjudication/episode_merges.json` (Nate_Esq gem1 vs gem4; hereforthenow gem2/gem1;
idtoaskredditque + throwaway12380404 gem5/gem6 crossposts; happy_pandaz + perfecthippie gem6/gem8;
Tactical_Thug gem3/gem1; edmunchies gem7/gem5; BuyingDetroitRE = PlungeLikeLivermore alias) and
~30 vendor/astroturf candidates for `adjudication/speaker_flags.json` (Probuildersx, ilovedoggos_8,
advisingvisor, everylineitem, buildoly_jeff, allenblack086, myrealmco, Realm_Score, sonnycastil,
Live_Solution7101, BuildADULA, ADUloans, Whitney_ADUExpert, Comfortable_Cut_419, KandLBuilders,
throwaway827492959, JonBuildz, GDComp, flyinghanes, VeterinarianSoft130, GnarMuffins,
RamsinJacobRealty, Citivest-Capital, Pacific-Proworks-Inc, ModernADUPlans, ArchitectArtist, ...).
Overlays only -- never edit coded slices.

## 6. E: arriving batches
The sk3 multi-topic census (`solar_census_20260928/README.md`) also carries ADU topics
`adu_pre2019` (2016-2018, California subreddits) and `adu_ca` (ADU + California in 16 national
home/real-estate subreddits). Claude will fetch, Gemma-triage and log them as ADU batches in
`adu_counties_20260926/TRIAGE_LEDGER.md` with the same `raw` + `packets.json` layout; code them
like section 2.

## 7. After coding
`python3 adu_forum_20260921/verify_all.py` (all slices); apply section-5 overlays; refresh
`adu_forum_20260921/analysis/county_breakdown.py` (episodes by county) and the findings doc
`docs/2026-09-22-adu-three-layer-findings.md`. Report threads, episodes, action rows, distinct
speakers and verified quotes as separate denominators.

## 8. Do not
Call the Arctic Shift API; modify or delete coded slices, overlays' history, raw captures or HCD
outputs (add, never overwrite); read benchmark `truth/`, `corpus/realworld/**/sources.json` or any
`process_draft.json`; commit; start synthetic/CalFresh work.
