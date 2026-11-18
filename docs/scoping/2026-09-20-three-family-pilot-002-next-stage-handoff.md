# THREE_FAMILY_PILOT_002 next-stage handoff

Status: constructed and held for source review. Do not prepare, render, verify, or
release this successor until the cutoff/path/clock contract and the public-only
adapter changes receive independent/root review.

## Constructed successor

- Immutable candidate world: `benchmark/synth/worlds/THREE_FAMILY_PILOT_002`
- Generator: `benchmark/synth/generator/three_family_pilot.py`
- Public-only adapter: `benchmark/synth/render/three_family_pilot.py`
- Counts: 24 fictional jurisdictions, 24,000 episodes, 246 structured render
  specifications, zero rendered artifacts, and zero independently verified
  artifacts.
- `public/render_specs/` and `public/render_context/` are renderer inputs. They
  are not a synthetic prose corpus and must not be supplied to an extractor or
  fitter.

The v1 world, audit, prepared packets, six rendered draft documents, and six
draft-record JSON files were preserved before source changes in
`runs/three_family_20260920/pre_successor_v1_snapshot`. The sealed audit text is
not amended here; its rendering-history erratum is a separate provenance item.

Preservation-receipt qualification: an earlier work log recorded aggregate v1
tree digest `6234dc581c49ef4d1b0627ea1bdc4804c27bde34e6fa04002fa10e081c54539d`,
but the exact routine/version that produced it is not recoverable from the
compacted record. The current `test_three_family_pilot_generator._tree_hash`
routine sorts files, updates SHA-256 with each relative POSIX path, then with the
binary SHA-256 digest of that file's bytes; it produces
`2859bc855dcf16510cb5822d1e9752d30ff42b4850d589c9b78db9577b6110b9` for
both the live v1 tree and the sealed copy. These aggregate digests must not be
treated as directly comparable without the missing old routine. The
authoritative immutability check compared all 107 relative paths and individual
file SHA-256 values between live v1 and the sealed copy and found zero added,
removed, or changed files.

## Required source review

Review the generator for these successor invariants:

1. `latent_eventual_path` is private mechanics; `observed_path` contains only
   events whose end is at or before the fixed cutoff. `in_progress_event` is a
   sanitized right-censor record with no future end or duration.
2. Withdrawal checkpoint is drawn once, is never `decision`, and terminates the
   latent route before a decision.
3. Decision outcome/status and pickup or issuance status/censoring are separate.
   A known approval remains approved while fulfillment is pending.
4. Renewal cases have no interview, matching the declared renewal inventory.
5. CalFresh private clocks separately name application-to-approval,
   service-origin-to-approval, application-to-issuance, and
   decision-to-issuance. Published approval timing is stratified by route and
   clock origin; aggregate workload is not presented as timing sample size.
6. Forum directives identify a completed observed endpoint or an
   application-to-cutoff right-censored lower bound. They do not use latent
   future endpoints.

Review the adapter for the no-private-read boundary and world binding. It now
accepts only `THREE_FAMILY_PILOT_001` and `THREE_FAMILY_PILOT_002`, requires
public spec/context world identity to match the directory and frozen run, and
retains the existing packet, prompt, public-input, artifact, verdict, and
release binding gates. It still does not implement semantic verification.

## Eventual public-only adapter usage (after review)

Create a new explicit 002 public artifact-ID allowlist and evaluator selection
receipt. Selection may use `public/artifact_manifest.json` and jurisdiction/split
metadata needed to enact the predeclared selection rule, but must not inspect
case outcomes, summaries, reserved labels, or scores. Do not reuse the v1 receipt
as if it identified the successor.

Preparation, once approved, is:

```text
python -m benchmark.synth.render.three_family_pilot prepare \
  --world benchmark/synth/worlds/THREE_FAMILY_PILOT_002 \
  --allowlist <reviewed-002-public-ids.txt> \
  --out runs/<fresh-three-family-002-render-run>
```

The only renderer inputs for each artifact are its frozen packet and prompt in
that fresh run: the matching public spec, matching public context (or null for a
shared artifact), mapped style guide, boundary text, and prompt constraints.
Private truth, provenance, evaluation ceilings, split assignments, summaries,
and cases are excluded. Any eventual transport must be explicitly supplied to
`invoke_with_transport`; the CLI has no render command. Drafts belong only under
the fresh run's `drafts/` directory. Verified releases belong only under a fresh
release directory's `source_only/`; never write rendered documents into the
immutable world.

Every draft remains `unverified` until a separate semantic verifier supplies a
current, independent, hash-bound verdict. Count completion is not verification,
and the adapter refuses release for missing, failing, malformed, or stale
verdicts.

## Bounded construction gaps

This successor does not model CalFresh recertification, CCW policy-era
transitions, a paired mechanics-versus-misspecification world, or
jurisdiction-specific step-inventory variation. CalFresh schema eras and report
gaps are present, but they are not a policy-era model. All stochastic parameters
remain fictional design assumptions without empirical calibration.
