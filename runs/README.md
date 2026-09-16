# Experimental records and archive policy

The raw runs remain local and gitignored. This README is trackable; it is not a
backup. No run directory or posterior has been deleted or moved by the audit repairs.

Documentation currently depends on:

- `bayes_v3_final/`: first pilot, corrected baseline scores, real-corpus control.
- `bayes_v4/`: extraction branches, frozen fits, matched controls, calibration.
- `bayes_v5/`: timing/selection controls, benchmark audits, source ledgers.
- `bayes_v6/`: joint-model fixtures, phase/interpretation fits, source compilation.
- `bayes_v6/audit_updates/`: retrospective lineage, revalidated source responses,
  policy compilation, unlabeled calibration-review packets, information reports.

Before publishing or moving a run, preserve an immutable bundle containing its
manifest, config, seeds, input files/hashes, **all transitive input runs**, source
snapshots, posterior/comparison JSON, raw extractor responses and logs, and draws.
Prediction-only refinements and extensions may depend on draws in an earlier run.
Record SHA-256, byte size and relative member paths in the bundle inventory.

Small manifests, configurations, and result summaries should enter a reviewed,
tracked experiment registry. Large draws and raw document caches need an approved
durable storage destination with a verified upload/checksum and a restore test.
The destination and tracked registry have **not** been set up yet. Do not delete
the local originals until those steps are complete and approved. A source commit
alone does not archive the experimental evidence.

Keep failed, unconverged and superseded runs. Revalidation uses a new directory
and records old and new validator versions; never overwrite a historical response
or claim a changed validator was the original one.
