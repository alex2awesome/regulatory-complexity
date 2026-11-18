# Source trustworthiness for timing evidence: what exists, what is broken, what to build

For Codex, from Alex's question: can the model take account of how much a
source should be believed, so that a forum recollection and an oversight report
are not treated alike?

This is the detailed specification for items 3 and 4 of section 6 of the
[three-family plan](2026-09-20-three-statute-parse-verify-analysis-plan.md),
which already names the risk of double-counting per-source offsets against new
source-type shifts. It does not change scope and it authorises nothing. Every
number below is reproduced by
`runs/codex_audit_20260920/audit_source_trust.py`, receipt
`source_trust_audit.json`, which reads saved fits and frozen ledgers only, no
truth and no refit.

**Short answer.** The machinery for bias exists and has never moved off its
prior in any fit. The machinery for precision exists and is pointed backwards:
an aggregate with a stated sample size is currently given a wider error band
than one applicant's recollection. The machinery for outliers is uniform across
all sources. And the reason the bias term cannot move is only partly data
scarcity; it is also the parameterisation, which is fixable.

## 1. Three different quantities, currently conflated

| quantity | what it answers | where it lives now | status |
|---|---|---|---|
| **bias** | which direction a source leans | `par['source'][channel, family]`, added as a log offset in the report kernel | learned, but pinned at its prior; width too narrow by a factor of about seven |
| **precision** | how tightly to believe the number | `Config.report_sd` 0.25 for an individual, `max(.,0.5)` floor for a population summary of unknown n, 0.25 inside the finite-cohort quantile likelihood | fixed, two-valued, and inverted |
| **outliers** | is this number simply wrong | `Config.contamination` 0.05, one wide-kernel mixture component | uniform across every source |

Selection is a fourth, separate mechanism and should stay separate: it
conditions a case on its own clock rather than shifting a source, and your new
`source_type_sampling` policy is the right seam for declaring it by type.

Two current exclusions are correct and should be preserved. Money carries no
source offset, because a reported fee total is a rounding report of a number the
schedule fixes, so an offset there would be identified only by how wrong
applicants are about a published price. Counts carry no offset either, though
that one is a decision rather than a derivation and is worth revisiting: a
forum count of trips and an agency count of required inspections are not
equally reliable, and `count_error_scale` is a single global 0.5.

## 2. What is measured

Three saved fits, every source offset, against a prior standard deviation of
0.25 log units (28 percent):

| fit | source families | mean variance contraction | offsets below 10 percent contraction |
|---|---:|---:|---:|
| solar, extended | 17 | 0.003 | 100% |
| C44 control | 5 | 0.049 | 80% |
| C29 control | 5 | 0.040 | 100% |

Every posterior median sits within 6 percent of zero, and every 90 percent
interval is between 2.85 and 3.51 prior standard deviations wide. The prior's
own interval is 3.29 wide. The posterior is the prior, to two figures.

**Why, in the solar fit, is unambiguous.** Sixteen of its seventeen source
families contributed no informative row at all: every SolarTRACE, dashboard,
review and study row fell to a process-independent residual, and residual rows
carry no source offset by construction. The seventeenth family, forum, supplied
all 92 informative observations. A single source cannot have a bias estimated
against nothing.

**The width is wrong even where data exist.** In C44, where the truth is known,
the agency page says three to five weeks and the two forum whole-case clocks say
about three months and 218 days. That gap is roughly 1.7 log units, nearly
seven prior standard deviations. The model cannot represent the disagreement it
is meant to arbitrate, so it resolves it by moving the global location instead.

**The identifying comparison is not yet available in the real data.** Pairing
solar figures by their clock-boundary pair, agency source types against forums:

| start to end | agency, days | forum, days | ratio |
|---|---:|---:|---:|
| submission to unspecified | 182.6 | 42.0 | 0.23 |
| activity start to activity end | 21.0 | 12.5 | 0.60 |
| submission to decision | 19.8 | 13.0 | 0.66 |
| unspecified to activity end | 14.0 | 14.0 | 1.00 |
| preparation start to decision | 145.0 | 167.4 | 1.15 |
| complete application to decision | 10.5 | 26.5 | 2.52 |
| unspecified to unspecified | 53.7 | 182.6 | 3.40 |

Median ratio 1.00, range 0.23 to 3.40. That is not evidence of no bias. It is
evidence that the boundary labels do not pin the same quantity, so semantic
mismatch swamps any source signal. **Source trust cannot be estimated before
the quantities are pinned**, which is the same blockage as the clock failure and
puts this work after, not before, the whole-process binding in the plan.

## 3. The parameterisation problem, and the fix

Adding a constant to the global location and subtracting it from every source
offset leaves the likelihood unchanged for any observation that has a source.
Location and source offsets are confounded by construction. The model already
knows this: `source_location_update` proposes along exactly that ridge, with
direction `[1/location_sd, -1/source_sd, ...]`.

The prior breaks the tie, and it breaks it hard. The location prior is 2.0 and
the source prior is 0.25, so common movement is eight times cheaper in the
location. **The offsets sit at zero because the geometry sends everything
common to the location, not only because the data are thin.** Widening
`source_sd` without changing the parameterisation makes the ridge worse and
will degrade mixing, which is the same failure mode as the collinear agency
effects in the SolarTRACE fits.

**Recommended fix: a reference source type.** Designate one type as the
reference, fix its offset at zero, and make every other type's offset a
relative shift against it. Then "forum figures run x percent longer than
administrative figures for the same pinned quantity" is a well-posed estimand,
the location no longer competes for the common part, and the prior can be wide
without creating a ridge. A soft sum-to-zero constraint across types is the
alternative; the reference version is easier to interpret and easier to report.

Which type is the reference is a declared assumption, not a finding, and it
must be recorded as one. Administrative data with a reviewed denominator is the
natural choice because its population is stated, not because it is true.

## 4. Changes, ranked, with acceptance gates

**4.1 Stop the precision inversion.** Replace the two-valued report scale with
a per-source-type scale, and route any aggregate with a reviewed denominator
through the finite-cohort likelihood rather than the unknown-n floor. Keep the
floor only for aggregates whose denominator review is genuinely unresolved.

*Gate:* on a fixture where the same quantity is reported by one forum post and
by an aggregate of stated n, the aggregate moves the posterior more than the
post. Today it moves it less. No change to any fit that supplies neither.

**4.2 Hierarchical, reference-anchored source offsets.** A type-level offset
with a learned spread, a document-level offset nested inside it, one type fixed
as reference, and a prior wide enough to express a factor of two (a type-level
scale of about 0.5 log units, with the spread itself learned rather than
assumed).

*Gate:* refit C29 and C44 and show that the type offsets move off the prior
where both channels report a pinned quantity, that the location no longer
absorbs the common part, and that R-hat and effective sample size on the source
block are no worse than the current fits. Report the fitted spread with an
interval, and state plainly when it is prior-dominated.

**4.3 Per-type contamination.** One outlier rate per source type instead of a
global 0.05, weakly informed and reported.

*Gate:* the fitted rates are reported with intervals; a type with few rows
visibly retains its prior rather than acquiring a spurious rate.

**4.4 Decide the count channel explicitly.** Either extend the source offset
and error scale to counts, or record in the model's limitations that count
evidence is treated as equally reliable from every source and why.

*Gate:* whichever is chosen is stated in the posterior report, not left
implicit.

## 5. Where to identify it, and how far it travels

A source-type effect is identified only where two types measure the same pinned
quantity. Four real processes have both channels: solar, naturalisation, food
benefits and unemployment. Within the approved scope, solar is the one to use,
and it needs the whole-process and administrative-cohort binding first.
Concealed carry has almost no administrative timing data, which is exactly why
it needs a transported prior rather than its own estimate.

Because the source list is global across programmes in a joint fit, a type
offset learned where both channels exist will pool into processes where only
forums exist. That is the mechanism for transport and it is also the risk:
pooling amplified bias in the five-programme fit when no correction was
present. Two requirements follow. Type grouping must be on, since per-document
families pool nothing, which is why the solar fit had seventeen families and
learned nothing. And transport must be stated as an assumption about
comparability between processes, with a sensitivity run that drops it.

## 6. Cautions

- **Do not hardcode a ranking.** An oversight report exists because someone
  suspected a problem, so it is selected on the institution; a forum post is
  selected on the individual; an agency page leans optimistic, which the
  synthetic case shows directly, with the page below the truth and the posters
  well above it. The existing taxonomy comment on the `oversight` class already
  makes this point. Learn the direction; do not assert it.
- **Do not double-count.** If a type-level shift is added while per-document
  offsets remain free and unanchored, the two absorb each other. The nesting in
  4.2 is what prevents this, and the plan already flags the hazard.
- **Bias is not precision.** A source that is reliably 40 percent high is
  useful once the 40 percent is known. A source that is unbiased and vague is
  not. Reporting one number per source will hide this; report both.
- **Residual rows teach nothing about their source.** Any claim that a source's
  offset was estimated must be accompanied by that source's informative row
  count, or it is a prior with a decimal point.

## 7. Not recommended

Widening `source_sd` on its own. Ranking sources by hand. Estimating source
bias before whole-process and boundary binding lands, since the paired table in
section 2 shows semantic mismatch dominating at a ratio spread of fifteen to
one. And per-document offsets with a wide prior, which would give every
document its own excuse and identify nothing.
