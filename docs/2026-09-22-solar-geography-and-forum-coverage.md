# Solar forum coverage and permissive geography

Work order: search national and California discussions broadly, then locate
individual applicants from context. A named permitting department is **not** a
requirement. This note describes the active rules, not a claim of exhaustive
Internet coverage.

## Retrieval and reading

`pipeline/recon/solar_forum_collect.py` registers national solar/battery forums,
California-local communities and adjacent homeowner/construction communities.
The current registry has 62 communities, including newly discovered Visalia,
Riverside, Stockton, Temecula and the adjacent OffGrid community. National post listings are retained without requiring
California words in the original post. National comment-window searches provide
another route to relevant replies; these windows are not counted as fully read
threads. Deleted or inaccessible content remains an explicit coverage limit.

The lexicon includes California, NorCal/SoCal, counties, municipalities,
California utility aliases, community-energy organizations, local subreddits,
agencies and tariff terminology. These clues prioritize retrieval and reading;
they do not certify location. CA/SF/LA abbreviations and ambiguous place names
are weak clues, not hard assignments. Related equipment or vendor discussions
can contain real permitting and interconnection histories.

A scheduling bug was corrected in the September 22 pass: venue attempt counters
previously restarted for each discovery invocation. Repeated rate-limit stops
could therefore keep later local communities waiting while earlier venues were
retried. Discovery now derives cumulative attempts, including failed requests,
from the saved request log. New or under-searched communities move forward across
restarts; the API's cooldown still applies. This changes queue order, not evidence.

Each captured thread is read with its replies and later updates. Different
commenters are separate applicants. The original poster's state is not copied
to everyone. Cross-thread linking requires a compatible installation history,
not only the same username. A later completed report replaces, rather than
independently replicates, the same clock's earlier pending update.

Examples already recovered:

- A New Jersey-origin thread (`1nhvbpp`) contains a Northern California
  commenter's September application-to-PTO dates; that commenter is included.
- `138x5lh` had an old California-not-established exclusion. Its own timing is
  now retained with unresolved geography.
- A Bay Area battery-addition thread (`16219fb`) contains a later three-week
  application-to-PTO update. It is adopted for the next timing input.
- A four-month San Diego account (`15nru61`) is retained with unspecified
  process boundaries; uncertainty about the step is not a reason to erase the
  elapsed report or label it definitely municipal permit review.

## Location and process identity

| Evidence | Representation |
|---|---|
| Own explicit county/city | County assignment; city AHJ remains distinct from county-government AHJ |
| Own regional location | Candidate counties with explicit working weights and, where appropriate, unknown mass |
| Local subreddit or same-account contextual clue | Probable location, not automatic certainty |
| PG&E/SCE/SDG&E etc. | Utility identity/context; not one invented county or department |
| State only or no usable location | Retained unknown-county account; not 58 fabricated local observations |
| Explicit out-of-California account | Preserved in descriptive/national material, separate from the California fit |

Current soft weights are **uncalibrated working assumptions**, not measured LLM
accuracy. The compiler preserves unassigned mass and source references. A vendor
called “LA Solar,” or a list of its offices, does not locate each customer.
When geography is unknown, the conditional national/unknown report frame must
not be presented as a California population estimate.

Clock identity is a separate uncertainty. A whole-project duration, installation
wait, permit-review duration, inspection interval and PTO interval are not
interchangeable. Unknown-boundary reports remain typed evidence. Administrative
endpoint matching permits a particular comparison; it is not a universal
eligibility test for forum evidence.

## Honest accounting and next handoff

Update15:55UTC: the historical frontier now reaches January2005. The earlier
2015-bounded frontiers are archived; page counters are preserved so older
comment batches cannot overwrite recent ones. Seven national post frontiers
have returned empty at the extended boundary, while four are still paging.
This establishes neither complete comment capture nor full Internet coverage.
Latest completed acquisition:67,607 posts,2,352 trees,56,118 tree comments.
There are426 reviewed captured-text Reddit threads plus three external roots;
linked images are not counted as read where explicitly noted in the manifest.
Timing019 completed406claims/233contributors/165passing separateclockfits.
Timing021 is prepared, NOT fitted:441claims/258contributors/176clocks, including
two new local/national threads and SOL028 plus a linked duplicate correction.

An explicit-unknown-mass compiler bug is corrected in evidence_v10 and later:
candidate names no longer erase a declared unresolved probability. Earlier
evidence versions remain frozen. Evidence_v11/source_alignment_v11 bind prepared
timing021 for a new joint input; this does not claim completed conditionalfits.
Anonymous building-staff accounts are separately typed in root_practitioner011;
typical estimates/fee policies do not become fictitious individual applicants.

September 22, 15:43 UTC checkpoint: 419 Reddit trees read; completed timing017
uses 351 claims from 212 installations. Evidence_v9 preserves all351, including
249 without county weights and eight with partially unresolved county mass.
Timing019 adds55 claims and is still running. The exact acquisition frontier is
in the status file below, not this dated snapshot. Local recall searches now
include photovoltaic, Powerwall and PTO as well as solar; national listings
remain unscreened. The current API date window begins January2015; earlier
material is not exhaustively enumerated. Search leads are not completed reads.

Collection state: `runs/solar_forum_20260922/acquisition/forum/status.json`
(updated after each collection pass or by the collector's `status` mode).
Query/listing/comment frontiers live beside the captures. A registry entry is
not an exhausted search, and a post body is not a captured comment tree.

Reading/adoption: `queue_latest/reviewed_coverage_manifest.json` under the solar
run directory. The manifest distinguishes complete-tree reading, semantic
adoption, timing consumption and structure consumption. Reservations are not
completed reading. `queue_current12` is an immutable earlier coverage snapshot,
not the live acquisition total.

Latest completed numerical checkpoint at writing: `timing_combined016`, 330
measurements, 204 timing contributors and 124 usable **separate conditional
clock fits**. The earlier `county_model/evidence_v7.json` binds run015's 296,
including 208 with no county weights; a new compiled binding is pending.
The limited joint forum/administrative fit004 now passes numerical gates on
its frozen 32-observation pilot. This is not a full county process or identified
intrinsic-capability posterior. See [the county-model note](2026-09-22-solar-county-model.md).

The remaining work is real: capture queued trees, read them, adopt their usable
claims into model inputs, finish joint-model integration and report what the
data actually identify. Source checks are finite per batch—reference resolution,
endpoint/censoring interpretation, geography and same-installation linkage—not
a repeating full-corpus verification campaign.
