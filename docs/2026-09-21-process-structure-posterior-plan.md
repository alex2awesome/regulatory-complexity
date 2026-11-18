# A posterior over the process itself: steps, repeats, stringency, and where the burden sits

## For Codex: read this section first

This plan replaces the 20 September ordered remaining-work list. Alex has
approved it. It is the current work order.

**Scope of this handoff.** Phases 1 through 5 below, on **CalFresh and
concealed carry**, real data only. Solar stays with Claude, who owns its panel
and runs the same phases there. Claude also builds the synthetic test-bed for
solar and CalFresh. Codex does no synthetic work and no new retrieval.

**What changes from the current work order.**

1. The 47-case joint timing fit: let the running attempt finish, take its result
   or its failure, preserve everything, and stop. No eighth attempt.
2. Drop the county-hierarchy extension of the administrative fit. The conjugate
   Dirichlet baseline already beat V6 on that comparison; county contrasts on
   time are readable from the baseline that won.
3. Descriptive packets stop. The two just-finished candidate packets get their
   root review and then no successors.
4. The deliverable changes from clocks to a **step-level burden posterior**: for
   each step, presence probability, expected rounds, time, cost and payee,
   stringency, obstacle count, and the posterior share of total burden.

**Non-negotiables in the model.**

- The step universe is the union of every step observed in *any* source, the
  statute, any jurisdiction's own documents, any applicant account. Never the
  statute alone. Label every step by the layer it is observed in: statutory,
  administrative-only, applicant-only. The gaps between layers are the result.
- Silence is not absence. Every source type gets its own detection probability
  per step, estimated where documents are complete. A step not mentioned is not
  a step not present.
- Per-step repeat blocks in V6 is the one model change. Make it. Do not route
  around it with the single block.
- The occupancy model lives outside V6 and feeds it route weights. Do not build
  it inside the trace machinery.

**What to reuse, not rebuild.**

- CalFresh: the thirteen action headings are the step vocabulary. The seven
  fitted clocks attach to steps. The 56 contact, 40 phone-failure and 30
  rework references become count observations through the existing count
  channel. The eleven obstacle headings are the onerousness proxy.
- Concealed carry: 21 agency-side activities in the `ccw_counties` ledger,
  2,011 case identities across 30 authorities with eight or more cases, four
  fee payees. No fit exists. This is the family where per-jurisdiction
  structure is genuinely identifiable, and it comes before any further CalFresh
  clock.
- The evidence contract, `burden-count-evidence/2`, `effective_evidence.py`,
  and the semantic review discipline all stand.

**Bookkeeping rule.** One packet per phase per family. A hash repair does not
spawn a packet. Report findings, not denominators.

**Validation split.** Claude validates the occupancy model on solar's
requirements file as real ground truth and on the synthetic test-bed. Codex's
gate on CalFresh and concealed carry is held-out jurisdictions, Phase 3, and
the synthetic test-bed once Claude delivers it.

**Shared artefact.** The step-level burden table schema, agreed between Codex
and Claude before Phase 1 ends, so the three families' results sit side by side.

---

2026-09-21. Alex's request: a plan to get real posterior confidence on the
process model, meaning the number of steps, how often each repeats, how
demanding each is, so that burden can be mapped to the parts of the process
that carry it. This is the project's actual question, and none of the work so
far has aimed at it directly. Every fit to date has treated the process
structure as a fixed input and estimated time on top of it.

## 0. Two corrections to what I said last

I wrote that "a unified posterior" and "any family complete" were not required.
Alex asked why not. The answer is that I conflated two meanings of each word.

**Unified across evidence types**, one likelihood over every administrative
cell and every forum sentence at once: not required, and six failed sampler
attempts on CalFresh say it is not the way in. **Unified across the process**,
one model whose parameters *are* the steps, their repeat rates, their stringency
and their times: required, because that is the only object from which "which
part of the process carries the burden" can be read with uncertainty. A table
assembled from separate fits has no joint posterior over the process; it cannot
say how confident we are that a jurisdiction has eleven steps rather than nine.

**Complete corpus**, every source read and every use closed: not required.
**Complete model**, every step in a family's process with a posterior on its
presence, repeats, stringency, time and cost: required. That is the deliverable.

## 1. What the process model has to contain

For one statute implemented by many jurisdictions:

| quantity | per | what it is |
|---|---|---|
| step universe | statute | every step any implementation might contain |
| presence | jurisdiction and step | required, conditional, or absent |
| participation | step | whether the applicant acts, or only waits |
| repeats | jurisdiction and step | probability of another round, and how many |
| stringency | jurisdiction and step | what the step demands: documents, professional stamps, in-person attendance, fees, notarisation |
| time | jurisdiction and step | elapsed, with waiting and service separate where observable |
| cost | jurisdiction and step | amount and payee |
| order | jurisdiction | serial, parallel, and which repeat returns to where |

V6 already carries presence as route hypotheses with prior weights,
participation as payer flags, one repeat block per programme, time, cost on
operations, and order as blocks. It has no stringency, and it holds one repeat
block where real processes have several. What it has never had is a *posterior*
over presence: the routes are supplied by hand with fixed weights.

## 2. The model: steps as occupancy with imperfect detection

The right statistical object for "is step s part of jurisdiction j's process"
is an occupancy model with detection, the structure ecologists use for species
that are present but not always seen. Evidence about a step is a *detection*,
and the sources differ in how reliably they detect a step that is present.

    z[j,s] ~ Bernoulli(psi[s] + u[j])          presence, pooled across jurisdictions
    y[j,s,k] ~ Bernoulli(z[j,s] * p[s,k])      detection by source type k

`psi[s]` is how common a step is across jurisdictions under this statute.
`u[j]` is a jurisdiction's tendency to add or omit steps. `p[s,k]` is the
probability that source type k mentions step s when it is present: an agency
checklist detects a required step almost always, a forum account detects a
payment step rarely. Silence is then weak evidence, weighted by how detectable
the step is, rather than being read as absence, which is the error every
inventory built so far has been exposed to.

Three things fall out of this at once. The posterior number of steps in
jurisdiction j is the posterior sum of `z[j,·]`. A jurisdiction with thin
documents inherits a prior from the jurisdictions with rich ones, which is the
hierarchical pooling the project wanted for agency culture, applied to
structure. And detection probabilities are estimated from the jurisdictions
whose agency documents are complete, then transported to those whose are not.

**Repeats** attach per step: a hurdle-geometric law per step and jurisdiction,
pooled, fed by the count channel V6 already has, meaning additional rounds and
visit counts from applicant accounts and from published rework rates.

**Stringency** is a feature vector per step and jurisdiction, extracted from
agency documents as structured fields rather than prose: number of documents
required, professional review or stamp, in-person attendance, fee and payee,
appointment required, notarisation. It is reported directly as burden, and it
enters as a covariate on time and repeats to test whether demanding steps take
longer or come back more.

**Burden mapping** is then arithmetic on posteriors: for each step, the
posterior probability it is present, times the expected rounds, times the
time, plus its cost, plus its stringency score. The share of total burden at
each step, with an interval, is the answer to "which part of the process."

## 3. Where V6 changes and where it does not

- **Occupancy model:** new, outside V6, and its output is a posterior over
  inventories, which V6 already consumes as route hypotheses. V6 stays the
  integration target; the occupancy model replaces the hand-authored handoff as
  the source of its route weights.
- **Per-step repeat blocks:** the one real change to V6. The trace model raises
  on a second repeat block today. Real processes have several.
- **Stringency:** no model change. A regression on fitted per-step quantities.
- **Time and cost:** already there.

## 4. Evidence, and what it can identify, per family

**Solar.** The step universe is 45 ledger activities, 19 core and 18
conditional, split across the authority, the utility, the installer and the
applicant. Detection is nearly complete on the authority side: the SolarTRACE
requirements file states, per authority, the number of inspections required,
whether structural and electrical review are required, whether a rough-in
inspection is required, whether review is outsourced. That is direct
observation of presence for the steps that matter, on 240 to 439 authorities.
Time per phase is fitted. Cost per authority is present. Repeats are implicit,
since the permit metric counts resubmission from the original date, so a
per-step repeat rate needs the forum accounts. Solar is the anchor: presence
posteriors will be sharp, and the model can be checked against near-complete
detection before it is trusted anywhere else.

**Concealed carry.** The step universe is 21 agency-side activities, from
application through Live Scan, background investigation, interview, training,
psychological evaluation, committee review, decision, issuance, plus renewal and
modification. 2,011 case identities across 30 authorities with eight or more
cases. Presence per authority is identifiable from applicant accounts because
there are 20 to 130 cases per authority. Repeats are directly reported:
resubmissions, renewals, repeated calls. Cost has four separate payees. This is
where a per-jurisdiction structural posterior is genuinely identifiable from
applicant evidence, and where the burden is largest.

**CalFresh.** The step universe is the thirteen action headings. Fifty-eight
counties, but detection per county from forum accounts is sparse, five cases
for the best county. So presence posteriors will be mostly statewide, not per
county; county contrasts come from the administrative census on time alone.
Repeats are the richest here: 56 contact-or-escalate references, 40 phone
failures, 30 rework references, none yet a count. Time is fitted for seven
clocks. Honest framing: a statewide step-level burden posterior, with county
variation on time only.

## 5. Validation on real ground truth, not synthetic

Revised after Alex asked whether this meant going back to synthetic data. It
does not, and the first draft was wrong to propose it: detecting steps across
thousands of rendered documents is the expensive loop again, and the real data
holds a better test.

The solar requirements file records, per authority, whether structural review,
electrical review, a rough-in inspection and third-party review are required,
and how many inspections. That is real ground truth for step presence on 240
to 439 authorities. The test: hide the requirements file for a held-out fifth
of authorities, fit the occupancy model on their other documents and the forum
accounts only, and score the recovered presence against what the requirements
file says. Real documents, real silence patterns, and the one question that
matters, whether the model mistakes silence for absence, answered on the data
it will be used on. The synthetic world is a fallback only if this proves too
thin, and with several hundred authorities it will not.

The limit is that the requirements file covers a handful of step features, not
the full 45-activity universe, so detection is validated for those steps and
transported to the rest as an assumption, stated as one.

## 5a. The step universe, and the steps a county adds on its own

Alex's second question: does this find steps that are not in the statute but
that a county adds implicitly? **Only if the universe is built from the
implementations rather than from the statute**, and that is the design
decision this plan rests on.

The universe is the union of every step observed in any source: the statute,
every jurisdiction's own documents, and every applicant account. A step that
appears only in one county's checklist enters the universe, receives a low
pooled rate because it is rare, and a high presence posterior for that county
because it was detected there. Every step is then labelled by where it is ever
observed:

| layer | where the step appears | its presence means |
|---|---|---|
| statutory | in the statute or rule | mandated burden |
| administrative | in a jurisdiction's documents but not the statute | county-added burden |
| applicant-only | in applicant accounts but in no document anywhere | undocumented burden |

The gaps between the layers, per jurisdiction and with posterior uncertainty,
are the metric seam this project set out to measure. The third layer is the one
that matters most for burden and the model surfaces it without instruction: a
step no agency document mentions gets a near-zero detection probability for
that source type, so agency silence stops counting against it and only
applicant accounts move its posterior. That is how forty phone-access failures
and thirty document-rework references become steps with presence probabilities
rather than anecdotes.

What the model cannot do is find a step that no source has ever named. The
count is therefore a lower bound on steps that exist. It is not a lower bound on
steps that burden anyone, since a step nobody has mentioned in any source has
imposed no burden anyone reported.

## 6. The plan, with gates

**Phase 1, the step universe and the detection matrix. One week.**
For each family, one table: jurisdiction by step by source type, each cell
detected, not detected, or source absent. Solar first, because its authority
side is nearly complete detection and the requirements file is already joined.
Concealed carry second, from the 2,011 cases and the county documents. CalFresh
from the thirteen headings and the claim references, which already carry
source links. Stringency features extracted alongside as structured fields.
*Gate:* every cell traces to a quotation or a structured source field, and the
matrix reports its own sparsity per jurisdiction before anything is fitted.

**Phase 2, the occupancy model, tested against the solar requirements file.
One week.** Conjugate Gibbs; it is small. Build the universe as the union of
everything observed and label each step by layer. Hold out a fifth of solar
authorities, hide their requirements file, fit on their remaining documents and
forum accounts, and score recovered presence against the file.
*Gate:* recovered presence covers the file's answer on held-out authorities,
and the recovered step count does not fall with document sparsity faster than
the file's does. If the model reads silence as absence it fails here, on real
data, before it is used anywhere.

**Phase 3, real presence posteriors. Three days.**
Solar as the check, since detection is near complete and the posteriors should
be sharp. Then concealed carry per authority. Then CalFresh statewide.
*Gate:* held-out jurisdictions, predicting their inventory from the hierarchy
and scoring it against their own documents.

**Phase 4, repeats and stringency. One week.**
Extend V6 to per-step repeat blocks. Fit repeat rates per step from the count
channel, concealed carry and CalFresh first because they report repeats.
Regress time and repeats on stringency across jurisdictions.
*Gate:* repeat rates are reported with intervals and with the selection caveat
that applicants who post are not applicants in general.

**Phase 5, the burden map. Three days.**
Per family, per step: presence probability, expected rounds, time, cost,
stringency, obstacle count, and the posterior share of total burden. Held out
by jurisdiction. This is the deliverable, and it is also the first output of
the project that can be handed to a policymaker.

**Total: about four weeks**, with a real-data recovery result on solar at the
end of week two that decides whether to continue.

**Revised again on the synthetic question.** Alex is willing to have a synthetic
test-bed built as long as Claude does it without Codex. It is feasible: the
generator already plants the three layers this model needs, every activity
carrying an applicant-facing, inferable or staff-only flag, plus 1,058 rework
loops and 135 county-added retrofits. The solar analogue S07 exists with 60
county processes and 2,396 specs, of which 31 are rendered; CalFresh needs a new
domain, about a day of generator code. Rendering ten to fifteen counties per
family, about 500 documents each, by fresh-context subagents at three or four
at a time, is three to four days of Claude's time. The extraction side stays
truth-blind because subagents do it. This runs beside, not ahead of, the real
solar validation, and it is not on Codex's critical path.

## 7. What this displaces

The 47-case joint timing fit, after its current attempt. The county-hierarchy
extension of the administrative fit. Further descriptive packets. The literature
check still gates a write-up. And this plan does not require any family's
corpus to be complete; it requires each family's *step universe* to be
complete, which is a different and much smaller thing, and for solar and
concealed carry it already is.
