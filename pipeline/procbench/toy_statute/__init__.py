"""Toy statute world: statute -> decision model -> process models -> observations.

See docs/2026-09-26-toy-statute-plan.md and docs/CORE_GOAL.md.

Module roles:
  spec         public knowledge: statute text, decision model, p-step catalog,
               refinement menu, chain construction (shared by generator, model,
               LLM prompt).
  truth_world  ground-truth parameters for world W0 (generator + scorer ONLY).
  generate     simulate cases, evidence, held-out cases; writes evidence/ and truth/.
  grid         exact day-grid discretization and convolution helpers.
  model        likelihood and priors over the continuous parameters, with exact
               enumeration of structures and case paths.
  estimands    burden / complexity / counterfactual estimands from (theta, structure).
  fit          MAP -> Laplace -> preconditioned random-walk Metropolis; answers.
  llm_baseline tool-less LLM answering the same estimands from the same evidence.
  score        compare answers to truth.
"""
