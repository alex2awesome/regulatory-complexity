# Solar as Claude's leg: feasibility assessment and plan

Alex's instruction: Codex takes CalFresh, Claude takes solar. Alex also caught an
inconsistency, and it was mine to answer, so that comes first.

## 0. Correcting myself on two things

**On concealed carry.** What I said should stop was the clause-by-clause parsing
of new forum pages, which returned zero usable rows across the last 1,582 posts
read. I did not separate that from using the 2,011 case identities already
parsed, and as written it read as though the statute were not worth pursuing.
That was careless phrasing, not a change of position.

**On solar.** My objection was to how the current fit is built, one median per
authority with no sample size, which makes the between-authority spread a
function of an assumed reporting precision. That objection was correct about the
build and wrong about the data. Having now read the underlying panel, solar is
the best-identified design in the project, and by some distance. The reasons are
below and they are all measurements, not impressions.

## 1. What is actually in the panel

**Corrected in section 2c:** the 32,238 figure below counts repeated rows. The
independent total is 9,584 cells and the owner count is 440, not 536. Read 2c
before using any number in this section.

`runs/rw_parse_20260918/solar_permit/source/solartrace_dataset_2025-09-09__ahj_utility_timelines__ca_long.csv`,
59,022 rows.

| | |
|---|---:|
| timing cells | 32,238 |
| authorities (AHJs) | 526 with timing, of 536 |
| utilities | 55 |
| years | 2017 to 2024 |
| timing cells per authority | median 61, p90 101, max 210 |
| authorities with 4 or more distinct years | 488 |
| authorities with 6 or more distinct years | 470 |
| authorities with all four timing phases | 419 |

Four phases, split cleanly by actor. The building department owns median permit
time and median inspection time; the utility owns median pre-install
interconnection time and median final-interconnection-to-permission-to-operate.
Every row names its utility.

Three properties make this different from everything else in the corpus.

**The denominator is not unknown.** Every one of the 32,238 timing cells has an
install count in the identical authority, year, size-class and technology cell.
Median 13, ninetieth percentile 127; 17,830 cells have at least 10 installs and
10,061 have at least 30. Codex established correctly that this is not the exact
sample behind a median, because a project enters the dataset on one date pair and
only about half carry every milestone. So it is an upper bound with a documented
completeness fraction, which is a great deal better than the "0 of 401 sample
sizes known" the current fit records.

**The design is genuinely crossed.** 801 authority-utility pairs, with 188
authorities served by more than one utility and all 55 utilities serving more than
one authority. That crossing is exactly what separates an authority effect from a
utility effect and from the step itself. It is the direct answer to the
collinearity that made the earlier 60-authority fits fail at R-hat 3, where every
operation belonged to exactly one agency.

**There are eight years per authority.** Median 8 distinct years. Repeated
measurement of the same authority separates within-authority variation, meaning
reporting noise and year shocks, from the between-authority effect that the
agency-culture question is about. One cell per authority cannot do this, which is
why the current build's spread is assumption-driven.

## 2. The natural experiment, which is the real find

**Demoted in section 2a and dropped from the executable plan.** The mandate
deadlines fall inside a 92 percent collapse in installations, so this design is
confounded. Kept as the reasoning record.

Government Code 65850.52 does not ask jurisdictions to automate. It orders them
to, on a staggered schedule set by population:

| group | requirement |
|---|---|
| city under 5,000 population, or any city in a county under 150,000 | exempt |
| city of 50,000 or fewer, not exempt | comply by 30 September 2024 |
| city or county over 50,000, not exempt | comply by 30 September 2023 |

Compliance means an online platform that "verifies code compliance and issues
permits in real time." The companion section 65850.5 sets the level promise:
expedited streamlined permitting, administrative approval, and "only one
inspection shall be required."

So the panel has an outcome measured annually for eight years per authority, and a
treatment whose timing is set by statute and population rather than by the
authority's own enthusiasm. That is staggered adoption with a never-treated
control group and a population threshold at 50,000. It is close to exogenous,
which is more than this project has had anywhere else.

It also makes an existing finding testable rather than anecdotal. The earlier
observation was that automation collapsed the permit step, median review falling
from seven business days to zero, while permit-to-passed-inspection fell only from
49 days to 37. With four phases per authority per year around each authority's own
mandate date, that becomes a real test of whether removing a step moves the
applicant's total wait.

**One input is missing and it bounds the design.** County population is on disk
for all 58 counties, with 2020 to 2023 estimates and rurality codes. City
population is not, and 448 of the 536 authorities are cities. So the plan has
tiers:

- **Tier 1, no new data.** Exemption is fully determined from county population,
  because every city inside a county under 150,000 is exempt. That gives a clean
  never-treated group, plus each authority's own pre-period and post-period
  around the two statutory dates.
- **Tier 2, one small public table.** City populations would assign the 2023
  against 2024 deadline and open a regression discontinuity at 50,000. This needs
  one file and therefore Alex's explicit authorisation, since the network
  retrieval question is already unsettled in this project. I will not fetch it
  without that.
- **Tier 3, not planned.** Voluntary SolarAPP adoption dates per authority would
  need extracting from the performance reviews or new retrieval. Skip it; the
  statutory mandate is the better instrument anyway.

## 2a. Revision after Alex's two questions, 2026-09-20

Alex asked whether solar has forum data, and pointed out that solar policy
changed repeatedly over this period. Both change this plan. The mandate
difference-in-differences of stage D is demoted, and a stronger design replaces
it.

### Forum data exists, and it identifies the utility rather than the authority

| | |
|---|---:|
| forum measurements in the solar ledger | 257 of 476, 54% |
| forum cases, which is every case in the ledger | 132 |
| Reddit or forum documents | 139 of 198 |
| forum measurements naming an authority in the panel | 31, across 10 authorities |
| forum measurements naming a utility | 125 |

So authority-level matching is as thin as Codex found: about ten authorities,
one to four cases each. But **utility-level matching is not thin.** PG&E appears
in 94 forum measurements, Southern California Edison in 20, SMUD in 5, SDG&E in
6. And two of the panel's four phases belong to the utility, not the building
department: pre-install interconnection, and final interconnection to permission
to operate.

That is the matched comparison the project has been unable to find. The same
quantity, a utility's interconnection wait, is measured administratively across
hundreds of authority-years and reported by applicants in 125 forum rows. The
source-bias calibration that has zero candidates at the authority level has real
coverage at the utility level, and it sits exactly where the applicant complaints
concentrate.

### The policy history breaks the mandate experiment

Alex is right, and the data show it plainly. Installs across all size classes and
technologies, from the panel itself:

| year | installs | change | median authority permit time, business days |
|---|---:|---:|---:|
| 2017 | 27,176 | | 4.5 |
| 2018 | 55,474 | +104% | 5.0 |
| 2019 | 61,251 | +10% | 5.0 |
| 2020 | 56,837 | −7% | 10.0 |
| 2021 | 96,597 | +70% | 11.0 |
| 2022 | 168,027 | +74% | 10.0 |
| 2023 | 84,949 | −49% | 7.8 |
| 2024 | 14,158 | −83% | 2.5 |

Volume fell 92% from its 2022 peak, and permit time fell with it. The net-energy
metering transition to the net billing tariff took effect on 15 April 2023,
producing a rush to be grandfathered under the old tariff and then a collapse in
demand. The automation mandate deadlines are 30 September 2023 and 30 September
2024, inside that collapse. Attributing the fall from 10 days to 2.5 days to
automation would be a textbook confound: permit time fell in a year when there
was almost no work to do.

Other statewide changes in the same window: COVID staffing in 2020 and 2021, the
federal credit extension in August 2022, building-code storage requirements in
2023, and prevailing-wage rules in 2024. Each is common in timing, so year
effects absorb the shared component, but heterogeneity by jurisdiction size
remains, and that is correlated with treatment status.

A data caution as well. 2024 has 61% zero-install cells and 3,091 timing cells
against 5,927 in 2022, so 2024 is thin and may be partial. Nothing should lean
on it.

### The design that survives, and is better

Invert the problem. Volume swings by an order of magnitude for reasons entirely
outside any authority's control: a tariff decision at the Public Utilities
Commission, a federal credit, a pandemic. That makes load an **exogenous
exposure** rather than a nuisance.

The primary estimand becomes two parameters per authority: its baseline speed,
and the elasticity of its processing time to load. Eight years of exogenous
volume variation per authority identifies both. That is a direct measurement of
agency capacity under stress, which is the agency speed and culture question
that started this audit, and it is robust to the net-metering transition because
the transition is what provides the variation.

The mandate effect becomes a secondary question, tested where both groups are
already past the tariff change, meaning a within-2023 or within-2024 contrast
across treatment groups. That needs city population, so it is Tier 2 and it is
reported as the weaker of the two.

Stage D below is replaced accordingly: load response first, mandate second and
explicitly confounded. Stages A, B, C and E stand, with one addition to B, a
volume term with an authority-specific slope, and one addition to E, the
utility-level source-bias comparison against the forum rows.

## 2b. Second revision: retrospective window, and latent authority assignment

Alex made two corrections on 2026-09-20. Both improve the design and one of them
removes an assumption I had imposed without justifying it.

### The retrospective window fixes the identification problem

Alex is content to study solar permitting retrospectively. Restricting to **2017
to 2022** does more than duck the salience objection: it excludes both policy
discontinuities that made the design unsound.

| | |
|---|---:|
| statewide installs, 2017 | 27,176 |
| statewide installs, 2022 | 168,027 |
| growth across the window | 6.2 times |
| authorities with at least four years of at least five installs | 325 |
| within-authority swing in annual volume, max over min | median 6.9 times, quartiles 4.5 and 11.8 |

The tariff change of April 2023 and the automation deadlines of September 2023 and
2024 are all outside this window. What remains inside is COVID staffing in 2020
and 2021 and the federal credit from August 2022, both statewide in timing and so
absorbed by year effects.

So the load-elasticity design becomes clean: 325 authorities, each experiencing a
roughly sevenfold internal swing in demand driven by a statewide boom none of
them controlled, with permitting time observed annually in four phases. We lose
the mandate experiment entirely, which was already demoted, and we gain a
well-identified estimate of how an authority's service time responds to load.

Salience is also better on this framing than on the full series. During the boom,
permitting friction was a live constraint and volumes were rising. A retrospective
study of that period is a study of the period when the thing mattered.

### The "named department" rule was my assumption and it was wrong

I had required a forum post to name its building department before it could be
compared with the administrative panel. That is hard matching, and Alex is right
that it discards information for no reason. The correct treatment is a latent
assignment: a distribution over which authority a case belongs to, formed from
whatever locating evidence the post carries, and marginalized in the likelihood.

Naming a utility is the most common locating clue, and its strength varies enormously:

| utility | authorities served | effective number under volume weighting | forum measurements naming it |
|---|---:|---:|---:|
| PG&E | 343 | 73.9 | 94 |
| Southern California Edison | 233 | 59.4 | 20 |
| SDG&E | 40 | 7.5 | 6 |
| SMUD | 11 | 5.8 | 5 |
| LADWP | 16 | about 3 | 0 |

So a post naming SMUD or SDG&E narrows 526 authorities to an effective six or
eight, and contributes 12 to 17 percent of its weight to any one of them. A post
naming PG&E narrows to an effective 74 and contributes about 1.4 percent. That is
not a reason to discard it; it is a reason to let the arithmetic decide. Most of
the forum evidence sits behind the weak constraint, so the honest expectation is:

- **all 132 cases enter**, rather than 31 surviving a hard rule;
- they inform the **statewide** applicant-experience distribution strongly;
- they inform **utility-level** effects well, since the utility is usually named
  and owns two of the four phases;
- they inform **per-authority** effects only weakly, which is fine, because
  per-authority times already come from the administrative panel. The forum data's
  job is to supply what the panel cannot see: the applicant's own preparation, the
  gaps between phases, resubmissions, trips and out-of-pocket cost.

**The discipline that keeps this honest.** Build the assignment prior from
locating evidence only, meaning the utility, any place mentioned, and
install-volume weighting. Never from the reported duration. If the duration is
allowed to inform the assignment, a case drifts to whichever authority its number
already resembles, and then inflates that authority's estimate; that is
self-fulfilling and it must be reported as a sensitivity rather than used as the
default.

An LLM reading the post is a legitimate way to propose the candidate set and its
weights, and the repository already has the right pattern for it in
`semantic_calibration`, where model-proposed alternatives become calibrated priors
rather than labels. The existing caution applies: several model votes are
correlated predictors, not independent observations.

This changes stage B, which must marginalize the case likelihood over candidate
authorities, and stage E, whose utility-level source comparison now rests on
weighted assignment rather than exact matches.

## 2c. Third correction, and it is mine: the panel is a third the size I claimed

Before writing the executable plan I tested whether the panel's rows are
independent observations. They are not, and my earlier figure of 32,238 timing
cells overstates the information by about 3.4 times.

For each phase, I checked whether the value repeats across every authority served
by the same utility in the same year, size class and technology:

| phase | raw rows | independent cells | level | identical within a utility stratum |
|---|---:|---:|---|---:|
| authority permit time | 5,527 | 4,756 | authority | 2% |
| inspection time | 5,034 | 4,296 | authority | 2% |
| pre-install interconnection | 10,277 | 252 | utility | **100%** |
| final interconnection to permission to operate | 11,400 | 280 | utility | **100%** |

The two interconnection phases are utility-level figures repeated once for every
authority that utility serves. Every one of the 168 and 192 multi-authority strata
has an identical value across all its authorities. Treating those rows as
authority-level observations would be double counting on a large scale, which is
the same error class that moved a synthetic clock by 26 to 50 percent earlier in
this project.

The independent total is **9,584 cells**, which matches the 9,586 retained cells in
Codex's corrected admission packet to within two. **Codex's consolidation was
right and mine was wrong.** Its panel also corrects the owner count from my raw
536 distinct name strings to **440 authority owners**, 439 with geographic
identifiers, and its units are business days throughout.

Three consequences for this plan.

- **Start from Codex's packet, do not rebuild.**
  `runs/three_family_20260920/solar_full_panel_admission_v1/full_owner_phase_stratum_coverage.csv`
  is the complete owner by phase by stratum matrix, 30,016 slots with 9,586
  present, and it already carries the zero semantics, the owner consolidation and
  the per-cell source row counts. Re-deriving from the raw CSV would reintroduce
  the double counting.
- **The authority analysis is still strong**: 9,052 authority-level cells across
  two phases, permit review and inspection, which is what the load-elasticity
  design needs.
- **The utility analysis is much weaker than I said.** It is 532 utility-level
  cells, not hundreds of authority-years. The matched comparison against 125
  forum measurements is real but small, and it should be described as a
  utility-level calibration on a few hundred cells rather than as a large panel.

**One disagreement with Codex's packet, stated explicitly rather than acted on.**
It records installation counts as `not_established_by_joined_installs_count` and
keeps them out of the timing denominator. That is correct: the install count is
not the number of projects behind a timing median, because a project enters the
dataset on one date pair and only about half carry every milestone. I am not
proposing to use installs as `n`. I am proposing two different uses that its
reasoning does not rule out: installs as an **upper bound** on the unknown
denominator, and installs as the **exposure variable** in the load-elasticity
design, where local demand is the regressor rather than a precision. Both need to
be declared as what they are, and neither may be reported as a known sample size.

## 3. Is this advisable? Yes, with one honest trade

What solar can answer, and answer well: whether the jurisdiction and a mandated
process change alter how long an applicant waits. That is your second priority,
at 526-jurisdiction scale, with a policy shock.

What solar cannot answer at scale: the number of steps, applicant effort, trips,
and money. The panel holds four phase durations, not a step inventory. The
applicant side of the solar corpus is 257 forum measurements over 132 cases,
which is about four cases per authority, too thin to attribute. Solar has 21 fee
rows and 2 effort rows in total.

So taking solar means the headline becomes waiting time and the policy effect on
it, and the steps-and-money questions come from elsewhere or leave the headline.
That is the trade against concealed carry, which has steps, trips and four fee
payees but only 30 authorities and pervasive selection. I think solar is the right
call for a first real result, because it is the one place where the answer will
not rest on an assumption about who chose to post.

There is also a sharper reason to prefer it. The project's founding claim is that
process structure matters more than decision-tree complexity. Automation removes
a decision node by statute. Asking whether the applicant's wait follows is a
direct test of that claim, and it is closer to Dan's framing than a burden
inventory would be.

## 4. The executable plan

Supersedes the stage list drafted before the corrections above. Window **2017 to
2022**, business days, Codex's corrected 440-owner panel as the starting input.

### Stage 0. Freeze the estimands, half a day

Write them down before touching a model, per the project's own standard. Four
quantities, each with its population, clock endpoints and units stated:

1. **Authority phase time.** The median business-day duration of permit review,
   and of inspection, for one authority in one year, size class and technology.
2. **Authority load elasticity.** The proportional change in that median per
   doubling of local annual installations.
3. **Applicant total wait.** Permit submission to permission to operate, composed
   across the four phases, which is not the sum of the four medians.
4. **Reporting offset.** The ratio between what applicants report for a utility
   interconnection phase and what the panel records for the same utility, year and
   stratum.

Also frozen here: the held-out split, the baselines, and the decision rule for
what counts as a result. No estimand is added later.

### Stage A. Panel construction and design audit, half a day

Build one tidy table from Codex's coverage matrix: owner, owner kind, geographic
id, utility, year, size class, technology, phase, median business days, source row
count, zero semantics, install count in the same cell, county, county population,
rurality. Carry the missing cells as missing.

Then audit the design before fitting. Rank and confounding of the authority, year
and phase contrasts. How much of the within-authority volume variation survives
the window. How many authorities have four or more usable years. And the checks
Codex's own review flagged: the treatment of the 585 reported zeros and their
three distinct semantics, and whether the same-day cells should be modelled as an
interval of zero to half a day or zero to one day.

*Gate.* If the authority effect is not separable from year and phase on the
realised design, say so and stop. If more than a quarter of cells rest on a single
source row, report that before any estimate.

### Stage B. The administrative model, one day

A crossed hierarchical lognormal on log median phase time, with an authority
effect, a year effect, a phase effect, size-class and technology effects, an
authority-specific slope on log installations, and observation precision informed
by the install count as a bound and the source row count. Roughly 500 to 900
coefficients over about 9,000 observations, minutes to run.

This is deliberately **not V6**. There are no cases, no repeat blocks and no route
uncertainty here, so the trace machinery would add nothing and forcing it would
repeat the error I criticised in the CalFresh fit.

*Gate.* Beat the raw cell medians and a two-way fixed-effects regression on the
held-out split, or report the loss.

### Stage C. Forum cases under latent authority assignment, one day

All 132 forum cases enter. For each, build a candidate set and weights from
**locating evidence only**: the utility named, any place named, and
install-volume weighting within the candidate set. An LLM may propose the
candidates and weights, treated as a calibrated prior in the pattern
`semantic_calibration` already uses, never as labels. The likelihood marginalises
over the candidate set.

Expected behaviour, stated in advance so it is not read as failure: a case naming
SMUD or SDG&E narrows to an effective six to eight authorities and contributes 12
to 17 percent of its weight to any one; a case naming PG&E narrows to an effective
74 and contributes about 1.4 percent. So forum cases will inform the statewide and
utility levels well and individual authorities weakly. Their real job is the part
the panel cannot see: the applicant's own preparation, the gaps between phases,
resubmissions, trips and out-of-pocket cost.

*Gate.* The assignment prior must not use the reported duration. Run the
duration-informed variant as a labelled sensitivity and report the difference; if
the two diverge materially, the fixed-prior version is the result.

### Stage D. The composed applicant clock, half a day

Compose the four phases into permit submission to permission to operate. This is
where V6 earns its place and nothing else in the repository does the job, because
the median of a sum is not the sum of medians, an arithmetic error that already
caught me once on this dataset. Note the asymmetry the corrections force:
permit review and inspection are authority-level, and the two interconnection
phases are only available at utility level, so a composed clock is
authority-specific in its first half and utility-level in its second. Say so.

*Gate.* Check the composed total against any panel or forum figure that spans the
same endpoints, at the same endpoints.

### Stage E. Load response, half a day

The authority-specific elasticity from Stage B, reported as a distribution across
authorities and related to population and rurality using the county covariates
already on disk. Which authorities hold their service time as local demand swings
roughly sevenfold, and which do not.

*Gate.* Volume is exogenous to any one authority, being driven by statewide tariff
and credit policy, so conditioning on it is a congestion control and not
conditioning on a mediator. State that argument explicitly, and show the estimate
with and without year effects.

### Stage F. Reporting offset at the utility level, half a day

The 125 forum measurements naming a utility against that utility's 532
administrative interconnection cells, same phase, same years. This is the
project's first available matched comparison and the only way to replace a
declared source offset with a measured one.

*Gate.* Report it as a utility-level calibration on a few hundred cells. Do not
transport it to other families without a stated comparability assumption and a
sensitivity that drops it.

### Stage G. Held-out evaluation and the literature gate, one day

Two splits, both frozen in Stage 0. Hold out whole authorities, to test whether
the hierarchy predicts a jurisdiction it has never seen. Hold out 2022, the last
year in the window, to test forward prediction. Score coverage and interval score,
not only point error, against three baselines: the raw cell median, a two-way
fixed-effects regression, and an LLM given the same panel description.

**The literature gate.** Before anything is written up, run the literature search
this session could not, because the claim that the load-elasticity estimate and
the reporting-offset calibration are novel currently rests on my recall. What is
already verified in our own corpus is that the descriptive layer belongs to the
National Renewable Energy Laboratory: the SolarTRACE retrospective on permitting,
inspection and interconnection timelines, the SolarAPP+ pilot analysis of January
2022, and performance reviews for 2022, 2023 and 2024. Our contribution has to be
the identification and the applicant-side integration, not the description.

*Gate, and the stopping rule.* When the held-out score exists, the leg is
reportable whether the model wins or loses. A loss to the raw medians is a
publishable finding about process modelling.

## 4a. Modules, runtime and deliverables

New code under `pipeline/procbench/solar_panel/` plus a run directory
`runs/solar_panel_<date>/`. No edits to Codex's packet, to `rw_parse_20260918`,
to `rw_parse_20260919`, or to the CalFresh path. V6 is touched only in Stage D and
only if composition needs it.

Runtime is small: Stage B is minutes on one core, and nothing here needs the
compute host. The whole leg is about five days of work, and the expensive part is
Stages 0, A and C, meaning definitions and assignment, not sampling.

Deliverables: per-authority phase-time profiles with uncertainty for 2017 to 2022;
the load-elasticity distribution across authorities; the composed applicant clock
with its asymmetry stated; a measured utility-level reporting offset; a held-out
score table against three baselines; and one limitations section naming the
unknown denominators, the utility-level collapse of two phases, and the selection
in the forum cases.

## 4b. Risks, and when to stop

- **The window may be too thin once cells are counted properly.** 9,584
  independent cells span eight years; restricting to six will cut it. If fewer
  than roughly 200 authorities have four usable years in the window, the
  elasticity design fails and Stage E should be dropped rather than weakened.
- **Two phases are utility-level.** Any claim about an authority's total service
  is really a claim about half of it.
- **Unknown denominators remain unknown.** Installs bound them and do not
  establish them.
- **Forum selection is unmodelled at the statewide level.** People who post waited
  longer. The offset in Stage F measures part of this and does not remove it.
- **Kill criterion.** If Stage A's design audit fails, or if Stage B cannot beat
  the raw medians out of sample, the leg reports that and stops. It does not
  acquire more data to rescue the model.

## 5. Interface with Codex's CalFresh leg

- Separate corpora and separate run directories. Neither leg reads the other's
  evidence.
- Codex owns the aggregate and census path, including its histogram module and the
  reviewed-denominator compiler change CalFresh needs now. I own my own new panel
  module and, if Stage C needs it, the hierarchy in `bayes_trace_hierarchy.py`.
  Running fits carry frozen source snapshots, so neither side disturbs the other.
- One shared artefact by agreement: the promise-against-practice table shape, so
  the two legs' results sit side by side. Solar's promise is administrative
  approval and one inspection; CalFresh's is the three-day rule.
- The currently running five solar conditions should finish and be preserved.
  They are the one-cell-per-authority build and they are superseded by Stage B,
  not repeated by it. Do not restart them.

## 6. What I will not do

Fetch anything from the network without explicit authorisation. Parse new forum
pages. Force V6 onto a model that does not need it. Report a policy effect from
Tier 2 without the population table actually on disk. Or present an in-sample fit
to the panel's own medians as a validation win.
