# Solar mass download and reading: Codex / Claude handoff

September 22, 2026. Execution plan requested by Alex. Real Solar only.

**Yes, we can download the available archived discussions and read them at
scale.** We have enumerated many more posts than we have fetched comment trees
for. This is an unfinished acquisition job, not evidence that those discussions
are inaccessible or irrelevant. More reader agents help parsing; they do not
remove the archive's network limits.

Claude is the proposed bulk-download and bulk-reading owner. Codex retains
model integration, statistical learning, and the fair baseline experiment.
This document does not claim Claude has accepted or started the assignment.

**Ready for takeover, 18:10 UTC:** Codex's last listing job exited successfully.
It increased the inventory to **93,627 posts, 2,621 trees, 91,006 pending tree
captures** (status at 18:06:19 UTC). Codex has released the archive API and will
not launch another archive job without an explicit handback. Claude can check
the handoff record/cooldown, accept ownership, and start the command below.

## 1. What the 86,035 number actually means

The completed acquisition status at **2026-09-22 17:46:17 UTC** reports:

| Stage | Count | Meaning |
|---|---:|---|
| Distinct enumerated posts | 86,035 | Post records, often including title/body; not full discussions |
| Captured archive comment trees | 2,621 | Available archive response held locally, not guaranteed live completeness |
| Comments in those trees | 63,396 | Comment records, not independent applicants |
| Posts awaiting a tree request | 83,414 | Actual acquisition backlog at this snapshot |
| Explicit collapsed-tree gaps | 0 | No such flags then; not proof that all live/deleted comments were archived |

Source: `runs/solar_forum_20260922/acquisition/forum/status.json`.
Listing continued after that checkpoint, so these are **dated counts**, not a
promise that the final corpus has exactly 86,035 threads.

The immutable working queue `queue_current17/thread_queue.json` has 86,034
posts (one fewer because it was built at a different instant), 2,621 trees,
632 read Reddit threads and 1,989 unread held trees. Its SHA-256 is
`da549faeb5c0a632070368e32e9bc4119e36d6308e1c5091e8991e5a17f2e6c8`.
SOL040 subsequently read five threads and SOL041 read 25; subtract those
reservations even before their coverage has reached the consolidated manifest.
SOL041's proposed measurements are not yet adopted.

The acquisition scope currently registers 63 communities: 11 national solar /
battery, 34 California/local and 18 adjacent communities. A registered venue is
not a completed search. Read the lists in
`pipeline/recon/solar_forum_collect.py`, not a manually retyped subset.
The separate national-comment index overlaps the trees; never sum those counts.

## 2. Ownership: do these tasks in parallel, not the same API job twice

| Work | Claude | Codex |
|---|---|---|
| Archive network requests | Sole operator after takeover | Finish existing request budget, then yield all Arctic Shift requests |
| All-post tree backlog | Drain in resumable batches; preserve failures | Repair a demonstrated collector defect if assigned; no competing downloader |
| National listing/comment pagination and local searches | Finish declared windows after prioritizing the held-post backlog | Add leads to a handoff file, not launch another API loop |
| Independent public forums | Capture missing pages where ordinarily accessible; log blocks | Supply prior leads and consume evidence |
| Bulk reading | Own unreserved threads; delegate bounded batches to inexpensive readers | Finish existing reservations; thereafter take only explicitly assigned batches |
| Permit-level administrative data | Avoid duplicate retrieval; coordinate a named source first | Continue the already assigned public-data acquisition |
| Semantic integration | Emit source-bound packets and batch coverage | Merge cases/actions, route every claim, update canonical consumption manifest |
| Inference / evaluation | Independently label held-out outcomes in the later evaluation assignment | Fit the shared model; implement frozen comparisons and report all results |

**Handoff condition:** inspect `docs/scoping/SOLAR_BULK_HANDOFF.json` and
`ps -Ao pid,etime,command | rg '[s]olar_forum_collect.py'` before taking the API.
Codex has released after its last `list_national` invocation exited. Claude
records acceptance in that handoff file before starting requests. A stale
PID alone is not an ownership protocol: include owner, UTC time, invocation,
and last checkpoint. No new code is needed just to start the existing downloader.

Only one archive operator across both sessions, including `seed`, discovery,
listing, comment trees, and tie resolution. The collector shares cursors,
failure records, cooldowns and status files and has **no interprocess lock**.
Two copies are neither safe nor a legitimate way around rate limiting.

Codex does not re-read every Claude batch before accepting it. The batch checks
below are the bounded handoff, not a second full parse or a verification project.

## 3. Download execution

Run from the repository root. The existing script uses the Python standard
library; no model process or special scientific environment is required.

### A. Drain known posts first

After accepting API ownership:

```sh
python3 pipeline/recon/solar_forum_collect.py comments --request-budget 200 --pause 10
```

Repeat bounded invocations while recording progress. Existing canonical tree
files are skipped. Priority clues change order, **not inclusion**: every known
national post remains eligible even when its author is not Californian. Read
California commenters inside national and non-California OP threads.

The current implementation does not accept a shard or an explicit ID-list
argument. Do not invent those flags. It reads the canonical held-post universe;
the queue snapshot is an accounting denominator, not an enforced CLI filter.
Report progress for that snapshot and separately report newly discovered IDs.

Keep requests serial. Respect `api_cooldown.json`; a 429 is a pause, not an empty
thread. The script returns on a 429 or three consecutive errors. Record why a
batch stopped, schedule the next attempt after the permitted time, and keep
reading already downloaded files meanwhile. Do not spin immediate retries.

Status and receipts:

- `acquisition/forum/posts/<thread_id>.json`: canonical post plus captured comments.
- `acquisition/forum/responses/`: hashed raw responses.
- `acquisition/forum/requests.jsonl`: request receipts.
- `acquisition/forum/comment_fetch_failures.json`: retryable failures.
- `acquisition/forum/api_cooldown.json`: earliest permitted retry.
- `acquisition/forum/status.json`: last completed status calculation.

All these paths are under `runs/solar_forum_20260922/`. A successfully returned
empty archive tree is not proof that the live discussion never had comments.

### B. Close acquisition gaps without silently calling partial trees complete

The current collector records `collapsed_comment_ids`, `limit_reached`, declared
and returned comment counts. However, it **skips any existing tree file**, even
a partial one. Its queue also calls a captured file `full_tree` based on where it
lives. Treat that label as “tree capture exists,” not a completeness certificate.

Claude should add one small resumable gap-recovery path when a flagged case is
encountered: retrieve the known missing comment IDs / subtrees, preserve the old
capture and its hash, merge by comment ID, then produce a versioned successor.
Update the canonical pointer only in a coordinated batch boundary. Do not edit
bytes already bound into a fit or a reader's reservation. A count shortfall is
a review flag, not evidence that a known list of missing IDs can be recovered.

There is also an older-metadata hazard: `Collector.posts()` uses first-seen
precedence (legacy before current discovery), not the freshest post revision.
Preserve explicit version provenance for edited OPs; do not silently overwrite
an earlier snapshot or assume its old declared comment count is current.

The archive documents tree expansion and comment-ID lookup; use those normal
public interfaces. The implementation gap is ours, not an invitation to bypass
access controls. See the [archive API reference](https://github.com/ArthurHeitmann/arctic_shift/blob/master/api/README.md).

For permanently unavailable text, retain a terminal gap record explaining the
attempts and evidence available. Deleted, removed, private, blocked and unarchived
material cannot be promised. No login circumvention, proxy rotation, or outreach.

### C. Finish discovery without starving downloads and readers

These existing commands are supported, **serially under the same API owner**:

```sh
python3 pipeline/recon/solar_forum_collect.py list_national --request-budget 100 --pause 10
python3 pipeline/recon/solar_forum_collect.py list_comments --request-budget 100 --pause 10
python3 pipeline/recon/solar_forum_collect.py discover --request-budget 100 --pause 10
python3 pipeline/recon/solar_forum_collect.py resolve_ties --request-budget 30 --pause 10
```

Use roughly four tree-download batches per discovery batch initially; this is
a scheduling preference, not a data filter. Finish the declared historic windows
and give new IDs an incremental queue. `refine` can split recorded timeout
queries locally; do not repeatedly restart a huge blocked time range unchanged.
`timestamp_boundary_saturated_unresolved` needs an explicit gap entry, not an
“exhausted” label. Some same-second boundaries cannot be closed by the existing
one-page tie resolver.

National comment listings can acquire many comments per request and expose
California replies without an OP clue. They do not automatically make complete
trees: join by `link_id`, deduplicate comment IDs, recover parent context and
record which date windows are covered. Retain those listings, then compare their
measured useful bytes/request with tree downloads before changing strategy.

For independent forums, the unit is an entire thread with explicit page counts.
Examples already held include SolarPanelTalk, DIY Solar Forum, Tesla Motors
Club, HOA Talk, InterNACHI and AppraisersForum. An accessible page 1 of 24 is
one captured page, not a completed thread. Read accessible material; carry the
remaining page gap rather than repeatedly challenging the same blocked endpoint.

### D. Throughput and storage: measure, do not promise overnight completion

The last uninterrupted 90 successful tree requests took about 624 seconds
between first and last starts: roughly one tree every seven seconds. At a
7–10 second spacing, 83,414 first attempts take **about 6.8–9.7 continuous days**
before errors, gaps, new discoveries, or downtime. A 200-request batch at the
conservative ten-second setting is about 33 minutes plus slow responses.
This is the current serial-route estimate, not a claim that all routes take a week.
For the newly completed 91,006-post backlog, the same calculation is about
**7.4–10.5 continuous days** before those overheads.

Check the archive's [bulk/export options](https://github.com/ArthurHeitmann/arctic_shift#downloads)
for community-specific downloads as a potential accelerator. Do one bounded
availability/size/coverage check before implementation. A compatible export may
replace many tree calls; a national comment-page join may also help. Neither
speedup has been demonstrated here. Do not download a whole-Reddit dump onto this
nearly full laptop. Larger storage/another host needs a concrete agreed location.

At this checkpoint only about **25 GiB** is free. Held canonical trees average
18.5 KB, suggesting approximately 1.54 GB for another 83,414 at the same size;
that is a biased pilot extrapolation, excluding raw responses, rendered copies,
images, model draws and unusually long threads. Stop acquisition before less
than 10 GiB remains and report the storage need. Do not delete existing work.
Stream/compress new bulk exports where supported; preserve hash-bound originals.

## 4. Reading: one full pass, then structured extraction in that same pass

Claude owns new, unreserved reading. Subtract:

1. `queue_latest/reviewed_coverage_manifest.json`;
2. all `parse/*reservation*.json`, including completed-but-not-yet-merged batches;
3. Claude's own reservations and completed packets.

Use the ordered `queue_current17/batches/` as a starting point, not the raw
lexicographically sorted `.threads` list. Build a new versioned queue after a
material download batch; do not overwrite the frozen queues. Existing tool:
`pipeline/recon/solar_thread_queue.py` (`--help` lists required input paths).
`queue_latest/thread_queue.json` is an older, smaller inventory and must not be
used as the acquisition denominator; only its reviewed coverage manifest is
maintained. New output directories also avoid stale higher-number batch files.
Rendering is optional: parsers can read canonical JSON directly. The lossless
renderer is `pipeline/recon/solar_thread_render.py`; avoid repeatedly rendering
the entire corpus merely to process one batch.

Reserve whole threads, usually 20–30 ordinary threads or approximately 40,000
source characters per worker packet; a long thread gets its own packet. Do not
split authors' updates across workers without a final whole-thread reconciliation.
Several inexpensive readers can work concurrently because they do not call the
archive or mutate shared model files.

**No title-only or lexicon-only rejection.** Read all held comment bodies in a
reserved thread. Most non-process discussion needs only a thread-level
`read_no_process_evidence` disposition, not detailed extraction. Whenever there
is an applicant journey, action, elapsed-time claim, effort, fee, or informative
process description, extract it during this pass. No second screening queue
that silently leaves the majority unread.

### Semantics that must survive the handoff

- Use local subreddits, California language, cities, neighborhoods, utility,
  flair and reply context as evidence. A named department is **not required**.
  The OP's location does not automatically locate every commenter. Preserve the
  clue, candidate set, rationale and unresolved mass instead of rejecting a case.
- City/AHJ, county, utility, installer and HOA are different entities. A county
  assignment does not turn a city permit into a county-agency performance case.
- Preserve whole-process claims even when individual steps are missing. Keep
  uncertain start descriptions as uncertain; do not relabel “start to finish”
  as “installation to PTO.” Link dated events and cross-thread updates.
- Separate observed elapsed time, pending lower bounds, approximate/ranged
  reports, policy deadlines, future appointments, active labor and money.
  An unresolved endpoint stays in the evidence, not an invented exact phase.
- One installation may have many updates and overlapping clocks. Link them;
  they are neither independent applicants nor independent algebraic totals.
- Record performed actions and genuinely explicit negatives. Silence is not
  absence. Availability, participation and number of repeated visits differ.
- Keep unlocated and outside-California evidence with explicit scope. Do not
  silently pool it into a California-population or county estimate.
- Extract installer/applicant/utility tasks and new action names, not just the
  existing narrow AHJ vocabulary. Actor + act is the unit; no arbitrary step cap.

## 5. Deliverables and format: compatible packets, not another ledger architecture

Claude writes each packet under a unique directory, for example
`runs/solar_forum_20260922/parse/claude_bulk/CLAUDE_SOLAR_0001/`.
Do not overwrite `root_adopted_*`, model inputs, or the shared coverage manifest.

| File | Required contents |
|---|---|
| `reservation.json` | Packet/owner/state/UTC time, thread IDs, exact source paths and SHA-256s |
| `decisions.json` | Existing `solar-semantic-decisions/1` layout: threads, contributor episodes, case links, location evidence, actions, quotes, timing/cost/effort claims, non-episode dispositions |
| `timing_staged.json` | Existing `solar-reviewed-timing/1` layout; episodes and original timing facts, actual source file paths in `source_packets` |
| `coverage.json` | One row per reserved thread: source hash, held comments, read comments, gap flags, completed/not-completed state, disposition and packet path |
| `manifest.json` | Inputs/output hashes, reader/model, timestamps, counts, assumptions, no synthetic truth access, explicit `staged_not_model_consumed` |

The reservation/coverage/manifest details are a handoff contract; they are not
already implemented as a bulk-runner CLI. Start with the existing packet shapes:
`parse/sol_decisions040.json` and
`parse/root_adopted_new_clocks040_adopted.json` are useful concrete examples.
SOL041 demonstrates richer dated journeys but is still staged, not a semantic
gold standard. Preserve original quotations, not only their summaries.

Timing fields already consumed include `thread`, `author`, `same_installation_as`,
`utility`, `location`, `county_weights`, `unassigned_geography_mass`, `context`,
and `timing`. Within `timing`, keep `clock`, `refs`, original `unit`, `value` or
`lower`/`upper`, `censoring`, and supported event dates. A `refs` comment ID binds
to its canonical source; `post` binds to that thread's post text. Preserve exact
quoted text and its locator/hash in decisions/coverage. Unsupported ambiguity
belongs in descriptive evidence or explicit alternatives, not fabricated values.
Candidate weights, if authored, must be labeled assumptions unless calibrated.

**Known handoff trap:** `source_packets: ["SOL041"]` is not a file path and breaks
preparation. Use the actual `.../decisions.json` path. Do not claim a schema-only
check proves the measurement's meaning.

## 6. Bounded acceptance, progress and completion

One mechanical check per completed packet: readable schema, IDs/hashes resolve,
quote replay, valid dates/units, coverage totals, within-packet duplicates and
case-link fields. One small semantic spot-check of a new worker's first packet,
then targeted checks only for contradictions, low-confidence labels or failed
compilation. A systematic error triggers a class-specific fix, not a restart of
every previously reviewed thread. Archive and itemize corrections.

Codex integrates accepted batches at useful milestones, with an explicit route
for every claim: used by a named component; retained descriptive; ambiguous;
out-of-scope; or awaiting a specific adapter. Missing county alone is not a
reason to discard timing. Receiving a packet is not the same as fitting it.
Do not run hundreds of independent clock fits after each tiny batch.

Each progress note reports enumerated posts, requested trees, captured trees,
known partial/blocked trees, comments, fully read threads, unique installations,
extracted claims, and model-consumed claims **separately**. Reconcile by stable
IDs, not the sum of overlapping batch totals.

Completion has three separate denominators:

1. **Frozen backlog accounted for:** each enumerated ID has a capture or an
   explicitly unresolved/unavailable record. Report acquisition success and gaps
   separately; “accounted for” does not mean downloaded.
2. **Captured text read:** every held thread/comment has a coverage disposition;
   inaccessible/deleted text is a named limitation, never “read.”
3. **Evidence integrated:** every extracted claim has a recorded model route;
   current unsupported structures remain visible rather than silently lost.

Declared search-frontier exhaustion is a fourth, independent claim. None proves
that we found every solar discussion on the Internet.

## 7. What Codex works on while Claude downloads and reads

Complete the current 50-action availability fit and the shared-case journey
bridge; connect useful new evidence to the same model, preserving agency/utility
identity, clock boundaries and case dependence. At handoff, timing024 is fitted
(576 claims); timing025 is prepared, **not fitted** (620 claims, 359 contributing
identities, 259 clock frames). `county_model/shared_journeys004/` is a five-journey
native V6 preflight, **not a fitted or population-calibrated result**.

Start the [same-evidence evaluation](2026-09-22-solar-same-evidence-evaluation-plan.md)
on a frozen usable subset **before** all 83,414 remaining trees arrive. Retrieval
completion is not a prerequisite for learning whether the model adds value.

### Copy-paste assignment for Claude

> Read this handoff and accept the download lease only after Codex releases it.
> Take sole ownership of the resumable Solar archive download, then delegate
> complete-thread reading batches after subtracting every existing reservation.
> Prioritize draining the known backlog, but retain every enumerated national
> post and account for the remaining discovery windows. Use permissive location
> evidence, retain whole-process and ambiguous claims, and write compatible,
> source-bound packets under `parse/claude_bulk/`. One bounded mechanical check,
> targeted semantic review, no whole-corpus verification loop. Do not edit model
> core, shared fitted inputs, or canonical adoption manifests. Report captures,
> gaps, reads, installations and claims separately. Codex handles integration,
> fitting and the same-evidence evaluation.
