# Simplified process-evidence model

An alternate to `../latex_plate_diagram/`, which is left intact. Same format:
TikZ circles, directed arrows, nested plates, a standalone figure, and an article
defining **every drawn variable**, its support, and its implementation status.

Timing is explicit: elapsed calendar days, payer hands-on hours, and agency
hands-on hours are separate. Payer burden and agency burden are separate derived
vectors. The unknown number of steps is a finite population-size parameter under
a disclosure model, not a count of positive document votes.

Files:

- [Standalone figure PDF](plate_diagram_standalone.pdf).
- [Model, factorization and glossary PDF](generative_model.pdf).
- [V4/V5 implemented architectures PDF](architectures_v4_v5.pdf) and
  [LaTeX source](architectures_v4_v5.tex): plate-and-stick schematics, notation,
  likelihoods (including how multiple reports share one case), learning
  mechanisms, separate versus joint components, runtime measurements, and the
  unfinished integration into v6.
- `plate_diagram.tex`: embeddable TikZ figure (no `tikz-bayesnet` required).
- `plate_diagram_standalone.tex`: compile the figure alone.
- `plate_diagram_caption.tex`: standalone caption defining each symbol.
- `generative_model.tex`: factorization, full node glossary, timing semantics,
  and an explicit target-model versus implemented-pilot distinction.
- `audit_terms.py`: verifies that every node has exactly one glossary entry and
  that edge endpoints exist.

From this directory:

```sh
python3 audit_terms.py
pdflatex -interaction=nonstopmode -halt-on-error plate_diagram_standalone.tex
pdflatex -interaction=nonstopmode -halt-on-error generative_model.tex
pdflatex -interaction=nonstopmode -halt-on-error generative_model.tex
pdflatex -interaction=nonstopmode -halt-on-error architectures_v4_v5.tex
pdflatex -interaction=nonstopmode -halt-on-error architectures_v4_v5.tex
```

The diagram now explicitly includes shared agency and task-type effects outside
the program plate, so timing evidence can inform organizations across programs.
The hierarchy prototype is [2026-09-16-bayesian-process-v4.md](../../2026-09-16-bayesian-process-v4.md).
The subsequent [v5 timing experiments](../../2026-09-16-bayesian-process-v5-results.md) and
[v6 joint visit development](../../2026-09-16-bayesian-process-v6-results.md) distinguish
completed measurements from still-unvalidated integration work; the diagram is
the fuller target, not a claim that every node has been fitted successfully.
Current [experiments and limitations](../../2026-09-16-bayesian-process-v4-results.md) include
joint agency learning, matched-evidence controls, and explicit count-calibration failures.
The historical specification is [2026-09-16-bayesian-process-v3.md](../../2026-09-16-bayesian-process-v3.md).
The [executed pilot results](../../2026-09-16-bayesian-process-v3-results.md) report the
negative baseline comparison and the limits of this first implementation.
The dashed global circles denote shared parameters, **not** a claim that those
parameters have already been calibrated. The finite-step plate has random size;
the nested case-visit plate includes a repetition index so rework is not confused
with discovering another distinct step. Process rework cycles do not make the
Bayesian dependency graph cyclic.
