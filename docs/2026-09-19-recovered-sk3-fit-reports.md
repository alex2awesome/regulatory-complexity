# Recovered SK3 fit reports

At 2026-09-19 18:46 UTC the configured `sk3` SSH alias succeeded, through its
`whale` proxy. The earlier direct-host network failure is not a current blocker.
No matching running inference process was observed on SK3, and no remote job was
started, stopped or restarted. The laptop's separate solar extension remains live.

The read-only collector saved 16 completed input/report/manifest bundles under
`runs/sk3_fit_reports_20260919_1145/`. `collection.json` records transport hashes,
original input hashes, equality of parsed original and reserialized snapshot
inputs, and posterior hashes matching their run manifests. Large draws have not
been copied and diagnostics have not yet been independently recomputed. The
collector is `runs/rw_parse_20260919/collect_remote_fit_reports.py`.

## What the saved diagnostics say

These are development fits on previously compiled inputs, not fits on today's
new real ledgers or newly repaired synthetic artifacts. `v2` is the saved run
name, not a new model architecture; the integration target remains V6.

| Saved run | Dimensions | Flagged diagnostics | Converged | Numerically usable |
|---|---:|---:|---|---|
| v2_C29__S12_dedup_p8192 | 113 | 0 | yes | yes |
| v2_C29__S12_p8192 | 155 | 0 | yes | yes |
| v2_combined_dedup_p8192 | 493 | 0 | yes | yes |
| v2_combined_p8192 | 611 | 0 | yes | yes |
| v2_S03_p4096 | 578 | 62 | no | no |
| v2_all5_p4096 | 1,048 | 76 | no | no |
| rw_fit_solartrace12 | 78 | 79 | no | no |
| rw_fit_solartrace60 | 366 | 380 | no | no |

Eight earlier `w2_v6_fit_*` runs are also preserved in the collection. The
C29 and C44 single-program originals pass both gates. The earlier C29 deduplicated
fit passes convergence but fails numerical usability. The combined, replicated
combined, combined-deduplicated, S03 and all-five originals fail convergence.
Flag counts include reported functionals, not only latent coordinates; therefore
they can exceed the latent dimension.

The severe SolarTRACE mixing remains a substantive diagnostic lead: saved maximum
R-hat is about 2.39 for the 12-unit fit and 3.28 for the 60-unit fit. By contrast,
the later S12 fits' maximum R-hat ranges from approximately 1.0012 to 1.0071.
Neither observation establishes recovery, identification or population accuracy.

## Next analysis, without changing the target to get a pass

1. Read saved configuration, source snapshots and input provenance before
   comparing runs; distinguish extra draws, integration resolution, model changes
   and deduplication. A better diagnostic cannot be attributed to a single change
   without that comparison.
2. Retrieve required draws/source snapshots and independently replay selected
   likelihoods/diagnostics. Keep failed results and their original inputs.
3. For SolarTRACE, inspect which hierarchy directions and program quantities
   differ across chains and whether the aggregate likelihood/model specification
   creates difficult posterior dependence. Do not present its unconverged agency
   estimates as measured effects.
4. Resolve remaining source/structure/temporal reviews before fitting the new real
   corpus; finish synthetic rendering/verification and isolate the evaluation
   partition before assessing predictive performance.

No benchmark labels, scoring outputs or reserved truth were read to collect these
reports. No Bayesian-versus-LLM superiority claim is supported by this collection.
