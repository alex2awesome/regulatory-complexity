# The 58-county covariate table: what it contains and what it implies

2026-09-16. Workstream A7 of [the scale-up plan](../2026-09-16-county-scale-up-plan.md),
done. Table at `corpus/counties/ca_counties_covariates.csv`, column-by-column
provenance in `corpus/counties/README.md`, builder at
`pipeline/recon/build_county_covariates.py`.

**26 of 40 columns complete for all 58 counties**, from five keyless public
downloads (USDA ERS population, poverty, income/unemployment and education;
the Census 2023 Gazetteer; the USDA Rural-Urban Continuum Codes; BLS QCEW, one
call per county). Nothing invented; 14 columns are empty with the source each
needs recorded. Two sources that the brief assumed would work do not:

- **The Census API now requires a key** and returns a "Missing Key" HTML page.
  That removes broadband subscription and the ACS language variables until
  someone registers a key.
- **The State Controller's compensation and financial-transactions site returns
  HTTP 403 to scripted fetches.** That is the same wall the CCW research hit on
  six of fifteen county sheriff sites, and it removes county-government FTE and
  general-fund figures, which were the brief's first-choice capacity measures.
  The substitute is BLS QCEW local-government employment, which is uniform and
  keyless but counts cities and school districts alongside county government.

## Three findings that change the model design

### 1. Population is bimodal by a factor of 8,470

Alpine 1,141 to Los Angeles 9,663,345. Median county population is about
190,000, but the mean is 690,000: five counties hold more than half the state.

**Density correction, 2026-09-16.** An earlier draft of this line said density
spans 1.5 to 2,380 per square mile. That maximum was Los Angeles, taken from a
six-county sample rather than a sort of all 58. The true range is **1.5 (Alpine)
to 17,323 (San Francisco), a factor of 11,549** — four orders of magnitude, not
three. Density also correlates with log population at only r = 0.88, so it
carries information population does not, and the [W2 spec](../2026-09-16-w2-generator-spec.md)
finds it the single best real predictor of permit timing while noting it is
absent from the plan's covariate vector.

**A harder identification fact.** Log population and log local-government staff
correlate at **r = 0.991**. Their separate coefficients are therefore not
identifiable from real California data at any sample size: a model reporting
both is reporting an arbitrary split of one effect. Either use one, or plant
deliberate within-county allocation noise in W2 so the two separate there, and
say plainly that the real-data version cannot separate them.

This is the arithmetic case for the covariate regression in the plan's §4.1.
A per-county random effect with no covariates would leave the 30 smallest
counties estimated almost entirely from their priors, which is precisely the
failure the audit measured in the two-program model (66% of coordinates under
10% learned). With covariates, a county with two forum posts is still predicted,
from its size, rurality and staffing, with an interval that honestly reflects
how little it contributed.

### 2. Staffing per capita runs *inverse* to county size, and that inverts the naive capacity story

| county | population | local-government employees per 1,000 residents | average wage |
|---|---:|---:|---:|
| Alpine | 1,141 | **192.8** | $62,304 |
| Inyo | 18,527 | 131.1 | $68,778 |
| Mono | 13,066 | 113.7 | $71,657 |
| … | | | |
| Orange | 3,135,755 | 36.5 | $82,400 |
| Contra Costa | 1,155,025 | 36.3 | $86,554 |
| Solano | 449,218 | **33.3** | $80,221 |

Correlation of log population with staff per 1,000: **r = −0.73**. Correlation
of the rurality code with staff per 1,000: **r = +0.69**. Both strong, both in
the direction opposite to "rural counties are understaffed".

Fixed costs explain it. A county needs a sheriff, an assessor, a recorder and an
environmental-health specialist whatever its population, so small counties carry
proportionally more staff. What they do not have is **absolute headcount or
depth**: the CCW research found Lake County teaching its own 16-hour firearms
course because there is no local vendor, and Humboldt stating that clearance
time is "dependent on CCW applicant load" because one coordinator handles it.

**Consequence for the model.** Staff per capita is the wrong capacity regressor
for process speed, and using it would produce a coefficient with the wrong sign
and a confident wrong story about rural efficiency. The right regressors are
**log absolute staff** (depth and specialisation), **staff per case** where a
caseload denominator exists, and the average wage as a second, milder gradient
(r = 0.65 with log population). Record all three in W2 as planted coefficients
so recovery can be scored.

### 3. Forum availability scales with population: r = 0.74

Number of plausible county subreddits against log population: **r = 0.741**.
Nine counties have no candidate subreddit at all — Alpine, Amador, Calaveras,
Colusa, Glenn, Mariposa, Modoc, Sierra, Trinity — holding 183,972 people, 0.47%
of California.

This is the disappearing-commons hypothesis measured at the level of *channel
existence*, before counting a single post. The post-level measurement is
workstream A8, running now. The structural point already stands: user evidence
is not merely thinner in small counties, the venue often does not exist, so the
availability model needs a **hurdle**: first whether a channel exists at all,
then the volume given that it does. A single continuous "fewer posts in small
counties" term would misfit nine counties to zero rather than modelling them as
structurally absent.

## Other patterns

- **Income and education track size weakly**: log population with median
  household income r = 0.52, with the bachelor's-degree share r = 0.36. So size
  is not a proxy for affluence, and the two should enter the model separately.
- **Poverty is nearly uncorrelated with size** (r = −0.29). Modoc's poverty rate
  of 20.1% sits with a median income of $51,996; Alpine's 15.6% sits with
  $83,265. Rural counties are not uniformly poor.
- **The two rurality definitions disagree, usefully.** 32 counties are RCRC
  members; the USDA noncore set is different, and Napa is an RCRC member at
  RUCC 2. Keeping both lets the model test which definition predicts process
  behaviour instead of assuming one. That is a small empirical result in its own
  right for a paper about how rules classify things.

## What to do with it next

1. **Feed the distributions into the W2 generator** (plan §3.1) so the synthetic
   county size distribution matches California's real bimodality rather than the
   current six hand-written jurisdictions. The generator should draw a covariate
   vector per county and *derive* speed, hourly rate and disclosure from it,
   with planted coefficients.
2. **Plant the inverse staffing relationship**, not a naive one. If W2 encodes
   "more staff per capita means faster", it will teach the model the opposite of
   what California shows, and any covariate-recovery result will be an artefact.
3. **Make the availability model a hurdle**: channel existence, then volume.
4. **Fill the four highest-value empty columns by hand**: county-government FTE
   and general fund from the State Controller (403 to scripts, fine in a
   browser), percent unincorporated and city counts from Department of Finance
   E-1. Unincorporated share matters especially for the ADU and environmental
   health programs, where the county only has jurisdiction outside cities.
