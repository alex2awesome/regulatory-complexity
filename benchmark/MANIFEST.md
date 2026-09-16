# Benchmark manifest — statute ↔ decision-model pairs, downloadable today

Assembled 2026-09-03. External repos live in `benchmark/sources/` (gitignored — reclone via the commands below). The benchmark's unit is a **(legal text, authored decision model, cases-with-answers?)** triple; each source contributes a different slice.

## In hand

| Source | What it is | Units | Contributes |
|---|---|---|---|
| **SARA** (`corpus/tax/sara/`) | 9 IRC sections + expert gold Prolog + 376 answered cases | 9 sections, 376 cases | Parser validation with full ground truth; looseness negative control |
| **PolicyEngine-US** (`sources/policyengine-us`) | US federal+state tax/benefit rules engine | **5,991 variable files, 4,630 YAML test files** | Behavioral ground truth at scale on unsanitized law; metric corpus (complexity distribution over coded law) |
| **GOV.UK smart-answers** (`sources/smart-answers`) | UK government's live statutory decision trees (Ruby, MIT) | **30 flows** (minimum wage, benefits, maternity pay…) | Government-*authored* trees: parse the cited legislation, compare our tree to theirs |
| **Catala examples** (`sources/catala-examples`) | Lawyer-validated literate encodings | US IRC §121/§132, FR housing & family benefits, FR income tax, successions, Polish taxes, NSW gaming (+tests) | Expert statute↔code gold pairs with exception (default-logic) structure |
| **NY/SD health codes** (`corpus/health_codes/`) | Both score sheets + Ho's recovered hand crosswalk + exact 2007 SD form | 68+48 items, 43 gold pairs | Cross-jurisdiction crosswalk gold; score-node (point-system) exemplar |
| **AB 2533 pilot** (`corpus/ab2533/`, `corpus/adu/`) | Amnesty + ministerial ADU statutes, city checklist URLs | 3 statutes | The discretion-heavy pole; city checklists = in-the-wild family members |

| **DMN-TCK** (`sources/dmn-tck`) | DMN standard's compatibility kit | **162 DMN models + 154 test-case files** (inputs→expected outputs) | Executable decision models WITH case suites — behavioral-eval calibration on non-legal models; score-node semantics reference |
| **ISDA CDM** (`sources/common-domain-model`) | FINOS open-source model of standard derivatives contract terms | 148 Rosetta model files | Private-law (contract standard)↔code pairs — the business-side exemplar |
| **AHRQ CDS Connect** (`sources/AHRQ-CDS-Connect-PAIN-MANAGEMENT-SUMMARY` + org `github.com/AHRQ-CDS`, API cds.ahrq.gov) | Computable clinical decision support paired with published guidelines | 1 artifact cloned; more via org/API | Guideline→CQL pairs — the medical analog of statute→code; imposed-thinness measurement target (guideline standards → hard criteria) |

Gated/not downloadable: BPM Academic Initiative model collection (registration-walled; models also not law-paired) — noted, skipped.

Reclone: `cd benchmark/sources && git clone --depth 1 https://github.com/{alphagov/smart-answers,PolicyEngine/policyengine-us,CatalaLang/catala-examples,finos/common-domain-model,dmn-tck/tck,AHRQ-CDS/AHRQ-CDS-Connect-PAIN-MANAGEMENT-SUMMARY}`

## Composition logic

The sources span the two axes the benchmark must test: **codability spectrum** (SARA/PolicyEngine ≈ fully codable ←→ AB 2533/HSC 17920.3 ≈ judgment-heavy; health codes in between with scored judgment) and **validation type** (case answers: SARA, PolicyEngine, Catala tests; authored models: smart-answers, IRS worksheets, SD form; human crosswalk: Ho). Report any codable-fraction number **relative to a stated input environment** (the § 7703 lesson: codability = f(text × fact-finding environment)).

## Prior benchmark use (novelty check, 2026-09-03)

Partially claimed territory — position accordingly:
- **[Lorenzo, Pietromatera & Holzenberger, NLLP 2025](https://aclanthology.org/2025.nllp-1.4/)**: statute→**Catala** translation benchmark (fine-tuning + few-shot, code-generation metrics). The Catala-pairs slice IS an existing benchmark — by SARA's own author. Cite; don't claim "first statute-to-code benchmark."
- **[Reasoners or Translators? (arXiv:2605.16052)](https://arxiv.org/pdf/2605.16052)**: contamination-aware tax-law eval; neuro-symbolic (translate-then-solve) beats monolithic LLMs; probes generalization via case/rule variations.
- Dutch production models (arXiv:2604.17153) and NormBench (arXiv:2606.08932) are purpose-built single-domain benchmarks.

**Still unclaimed** (our composition): (a) **behavioral evaluation against production test suites** — nobody scores parses by running PolicyEngine's 4,630 YAML cases (or Catala's test dirs) through them; existing work scores code-vs-gold-code similarity, which the Dutch paper itself showed diverges from outcome equivalence; (b) **government-authored trees** (smart-answers, IRS worksheets) as gold; (c) **cross-domain composition spanning the codability spectrum** (all existing benchmarks are single-domain, near-fully-codable); (d) **family/divergence measurement** — every existing benchmark scores distance to ONE gold; none measures the spread of defensible parses.

## Full benchmark landscape

See `docs/2026-09-10-benchmarks-inventory.md` (2026-09-10; ~60 verified rows across text→process, process mining, text→DMN, law→logic/code, rules-as-code tests). Most relevant additions to fetch next: **BREX** (2025; 409 regulatory/administrative docs → expert rule-flow graphs; GitHub) — the closest thing to law→process gold; **PAGED** (ACL 2024; 3,394 procedural docs → graphs); **ProMoAI** (text + POWL model + simulated log triples — the semi-synthetic pattern); **CCC19** (expert normative BPMN + real logs); Graus Dutch permit models (arXiv 2604.17153; 95 models + test scenarios, release status unclear).

## To chase (not yet downloadable / needs work)

- Statute texts behind PolicyEngine/smart-answers: 26 USC XML (uscode.house.gov bulk), UK legislation.gov.uk API — needed to complete the pairs.
- Dutch production decision models (95, arXiv:2604.17153) — check for released data/STTR files.
- NormBench (arXiv:2606.08932) — check for release.
- FDA Food Code + standard inspection form (shared ancestor for NY/SD).
- IRS Interactive Tax Assistant flows (scrape), German Programmablaufplan Lohnsteuer (BMF PDF).
- Ho's replication mapping file (ask Dan) — upgrades the 43-pair gold to the full 115→52 mapping.
