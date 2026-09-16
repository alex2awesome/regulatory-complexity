# The generative model, in LaTeX

## `generative_model.tex` — the write-up

A standalone article: what the model is for, the joint distribution, **every node in the hierarchy
defined** (symbol, name, observed/latent/global, parents and children, support, distributional family,
what data informs it, and whether it is implemented), the priors and posteriors, and the measured
verdict on what the Bayesian layer is worth. The plate diagram is embedded as a full landscape page.

```
pdflatex generative_model.tex && pdflatex generative_model.tex   # twice, for the longtable
```

Eight pages. The node glossary covers all 39 nodes drawn in the figure; a check in the build confirms
the two counts match, so nothing in the diagram goes undefined.

## `plate_diagram.tex` — the figure alone, in TikZ

The plate diagram for `docs/2026-09-15-generative-model.md`. Hand-rolled node styles, so it needs **no**
`tikz-bayesnet`; only `tikz` with `arrows.meta, positioning, fit, backgrounds, calc, shapes.geometric`.

**In a paper:**

```latex
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,fit,backgrounds,calc,shapes.geometric}
...
\begin{figure*}[t]
  \centering
  \resizebox{\textwidth}{!}{\input{figures/latex_plate_diagram/plate_diagram.tex}}
  \input{figures/latex_plate_diagram/plate_diagram_caption.tex}   % optional: a caption glossing every symbol
\end{figure*}
```

It is about 24 cm wide by 20 cm tall at natural size, so it wants `figure*` in a two-column layout, or
`\resizebox`. Compile it on its own with:

```
pdflatex plate_diagram_standalone.tex     # -> plate_diagram_standalone.pdf
```

**Layout decisions worth keeping if you edit it.** Global parameters sit in the left and right margins
beside the plates they feed, rather than in a row across the top, which is what kept their edges short
and roughly horizontal. Plate tags hang *below* each plate instead of sitting inside the bottom-right
corner, because inside they collided with the node captions. The two multi-symbol nodes use the `wide`
ellipse style; a 10 mm circle cannot hold $\mu_{it},\sigma_i$ legibly.

## Companion files (one level up, in `docs/figures/`)

| file | what |
|---|---|
| `../plate_diagram.svg` | the same diagram for the web, with CSS-variable colours and standalone fallbacks |
| `../plate_diagram.html` | a viewer for the SVG with its own light and dark palette — open it directly |
| `plate_diagram.pdf` | compiled output of the TikZ version |
| `plate_diagram_caption.tex` | a caption glossing every symbol, so the figure stands alone |
