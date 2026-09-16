"""Synthetic process-ecosystem generator (benchmark/synth/DESIGN.md).

Backwards generation, no LLM calls, stdlib only, deterministic given --seed:

    world -> statutes -> local rules -> designed processes -> simulated log
          -> artifact specs (visibility model) -> ceiling + tasks -> provenance

Entry point: ``python3 -m benchmark.synth.generator.build --world W1 --seed 1``
"""
