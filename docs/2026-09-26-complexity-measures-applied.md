# Complexity measures applied to the toy statute (2026-09-26, overnight)

Inputs:
- **Survey:** `docs/2026-09-26-complexity-measures-survey.md`, 17 candidate
  measures with verified citations.
- **Causal frame:** `docs/process-model-causal-frame.md`.
- **Code:** `pipeline/procbench/toy_statute/extended.py`, computed post hoc from
  saved posterior particles and from truth.

These measures are **descriptive**: Bayes against truth only. The LLM baselines
were not asked them in round 1 or round 2.

## On the Blum lead

The survey could not confirm which work Kevin Stangl meant. The
human-computation line (humanly usable passwords, and the PNAS 2020
"complexity of human computation via a concrete model", which measures a
person's cost as PREP, one-time learning, plus PROC, per-case work) is
**Manuel** Blum's, with Vempala, Blocki and Datta. Manuel is Avrim's father.
Avrim's own closest recent work applies theory to social and legal settings:
- strategic litigation, where lower courts learn rules from higher-court
  rulings;
- pessimism traps and grit;
- short certificates for predictions;
- few-round kidney-exchange queries.

Kevin's own work with Blum is on multi-stage screening pipelines. It's worth
asking Kevin directly. Whichever it was, two ideas transfer directly: the
PREP/PROC split, which gave our self-assessability measure, and certificate
complexity.

## What was implemented and what it says (W0, fit003 posterior vs truth)

All 27 town-level truths lie inside the Bayes 90% intervals.

| measure (survey id) | Alder (S1) | Birch (S3) | Cedar (S4) | drafting lever |
|---|---|---|---|---|
| Deadline coverage (M9): share of waiting inside the §4 clock | truth 0.69 · Bayes 0.72 [0.44, 0.85] | 0.76 · 0.75 [0.41, 0.90] | 0.75 · 0.76 [0.60, 0.86] | where the clock starts; "deemed complete unless notified in N days" |
| P(miss 30 d) if the clock started at submission (M9 lever) | 0.17 (now 0.03) | 0.80 (now 0.48) | 0.88 (now 0.55) | same |
| Serialisation excess, days (M8) | 0.0 | **11.8** · 8.1 [2.2, 14.0] | **9.7** · 8.3 [2.5, 12.1] | concurrency clause: "notice, review and inspection shall proceed concurrently" |
| Consolidated deficiency notice, Δ days (M1) | −0.2 | −0.4 | −2.2 · −1.3 [−3.8, −0.2] | "the authority shall state all deficiencies at once" |
| Error sensitivity, days per unit P(incomplete) (M10) | 17 | 22 | 27 | precise §2 contents; cure without restart |
| Days per correction loop (M10) | 14.0 | 15.7 | 13.5 | same |
| Exposure: neighbours informed / premises entered / P(in-person discretionary encounter) (M11) | 0 / 0 / 0 | 0 / 1 / 1 | 1 / 0 / 0.25 | desk review by default; notice rules |
| Guidance deficit, bits of procedure uncertainty from the town's own web page (M6) | 0.86 | **1.88** | 0.91 | publication mandate (Birch's page omits the inspection) |
| Counterfactual "§3 concrete", invariance band (causal assumption 1) | −4.8 to +1.6 | −17.2 to −8.9 (point −11.0) | −25.1 to −19.4 (point −20.8) | same edit, with honest uncertainty about behavioural response |

Statute level:
- **Openness (M4):** the text leaves log2 6 = 2.58 bits of procedure open (the
  menu).
- **Realised variety:** 1.58 bits across the three towns. Every town chose
  differently.

**Self-assessability (M3, text property):** 2 of 3 d-steps are determinable by
the applicant in advance. D2 is not, because "not a nuisance" is a standard,
not a rule.

## What this adds to the drafting picture

1. **Procedural vagueness and substantive vagueness are different levers.**
   - The round-1 counterfactual ("the authority shall *review the site plan*")
     makes the **procedure** concrete. It saves 11 and 21 days in Birch and
     Cedar.
   - It leaves the **standard** vague. Self-assessability stays at 2/3,
     because the applicant still cannot predict the nuisance judgement.
   - A **safe harbour** ("a coop at least N ft from the property line is
     deemed not a nuisance") targets the substance. It raises
     self-assessability to 3/3, and would likely cut correction loops and
     denials, which the current generator does not model.
   - The two edits are complementary, and our estimands should keep them
     separate.
2. **A concurrency clause captures most of the time savings without removing
   safeguards.**
   - Serialisation excess in Birch (11.8 days) is about the same as the whole
     "make §3 concrete" saving (11.0 days).
   - That saving came from deleting the inspection. Requiring the inspection
     to run concurrently with the desk review keeps it.
   - In Cedar, concurrency recovers about 9.7 of the 20.8 days while keeping
     neighbour notice and the hearing.
   - For a drafter, this is the more attractive edit when the inspection or
     notice has value. The model can price both.
3. **The §4 deadline covers only about 70–76% of the waiting.** The clock
   starts at "complete application", so correction loops are invisible to it.
   Measured from submission, the miss rate goes from 0.48 to 0.80 in Birch.
   That is a cheap drafting fix ("deemed complete unless notified within N
   days"), and the gap grows with the incompleteness rate. In W1, Alder's
   incompleteness rate is 0.5.
4. **Opacity is a jurisdiction property, not a statute property.**
   - Birch's page leaves 1.9 bits of uncertainty, against about 0.9 for the
     others, because the page omits its inspection.
   - A publication mandate addresses this regardless of what §3 says.
   - This measure separates town opacity from statutory vagueness, which the
     survey rightly emphasised.
5. **The consolidated-notice lever is small in W0,** because incompleteness is
   rare there. It is a lever whose value depends on the applicant population.
   Round 2's W1 (Alder at P(incomplete) = 0.5) will show a larger effect.

## Not implemented yet, and why

- **M2 ordering regret, M5 extensional disagreement, and M1's denial
  asymmetry** need a denial model. The generator has no denials. That is a
  worthwhile next generator variant, since denials and appeals are real
  burden.
- **M12 Kaplow break-even** needs drafting-cost and tailoring-value inputs.
  Conceptual.
- **M13 monetised burden** needs volume and wage inputs. Easy once those are
  chosen.
- **M7 interaction rounds** is mostly redundant with applicant interactions.
- **M14–M17 are flagged useless** for burden.

## Next

- Ask the LLM baseline these extended estimands in the next comparison, so
  Bayes and the LLM are compared on them too.
- A denial-model generator variant, enabling M2 and M5.
- Report every counterfactual with its invariance band, per the causal note.
