"""Every planted coefficient in one place, with its provenance.

Why one module. The corpus plan forbids tuning coefficients until a desired
correlation appears, and the only way to keep that promise checkably is to put
all of them where a reader can audit them against their sources in one sitting.
Nothing here reads truth or scores; these are pure functions of a county's
public covariates plus a keyed RNG.

Provenance vocabulary, from the plan's section 3. Every coefficient below
carries one, and `provenance_report()` prints the whole table:

    measured_anchor           counted from bytes on disk; the citation names the file
    derived_with_assumptions  counted, but a stated assumption converts it
    design_assumption         no measurement exists; the generator picks a value

The measurements come from `docs/2026-09-16-source-volume-register.md`, built by
`pipeline/recon/source_volume.py`. Two rules that document establishes and this
module obeys:

1.  **Existence and volume are separate mechanisms.** The CalGuns county forum
    assigned a thread to all 58 counties in one administrative batch in October
    2010, so existence carried no population signal while volume spanned three
    orders of magnitude. A single availability slope cannot produce that.
2.  **Slopes differ by family**, measured from 0.75 (reddit) through 0.99
    (administrative records) to 1.16 (the gun forum). So the slope is per
    channel, not global.

Where the evidence does not identify a direction, the coefficient is a scenario
variable with **zero as its default** and the alternatives named in `SCENARIOS`.
That is the plan's section 6 rule, and `V_DELAY` is the case that forced it: the
W2 spec planted 0.55 for "delay generates posts" and our best real measurement
puts it at +0.076 with a ΔR² of 0.004, sign-flipped for timing-bearing posts.
"""
from __future__ import annotations

import math

from .rng import chance, sub_rng

# --------------------------------------------------------------------- record

class Coef:
    """A planted number that knows where it came from.

    Deliberately not a plain float: an un-sourced coefficient is the specific
    failure this class exists to make impossible, so `provenance` and `source`
    are required positional arguments.
    """

    __slots__ = ("value", "provenance", "source", "note")

    def __init__(self, value, provenance, source, note=""):
        if provenance not in ("measured_anchor", "derived_with_assumptions", "design_assumption"):
            raise ValueError("unknown provenance %r" % provenance)
        self.value = value
        self.provenance = provenance
        self.source = source
        self.note = note

    def __float__(self):
        return float(self.value)

    def __repr__(self):
        return "Coef(%r, %s)" % (self.value, self.provenance)


def v(c) -> float:
    """The numeric value of a Coef or a bare number."""
    return float(c)


REGISTER = "docs/2026-09-16-source-volume-register.md"
SWEEP = "corpus/counties/source_volume_anchors.json"
APR = "corpus/counties/apr_permit_timing.csv"
P5 = "corpus/counties/p5_environmental_health_inventory.json"

# ------------------------------------------------------- population reference
# The real 58-county log-population distribution, so a z-score in a synthetic
# world means the same thing as the z-score the slopes were measured on. Taken
# from ca_counties_covariates.csv (pop_2023); recomputing it here keeps the
# generator free of a data dependency at build time.
LOG_POP_MEAN = Coef(12.061, "measured_anchor", "ca_counties_covariates.csv",
                    "mean of ln(pop_2023) over 58 CA counties")
LOG_POP_SD = Coef(1.838, "measured_anchor", "ca_counties_covariates.csv",
                  "sd of ln(pop_2023) over 58 CA counties; the 50-county APR "
                  "subset used for the delay test has sd 1.576")


def z_log_pop(county: dict) -> float:
    """Standardised log population, on the real 58-county scale."""
    pop = max(int(county.get("pop") or 1), 1)
    return (math.log(pop) - v(LOG_POP_MEAN)) / v(LOG_POP_SD)


def _z(value, mean, sd) -> float:
    return 0.0 if not sd else (float(value) - mean) / sd


# ------------------------------------------------------------ channel existence
# H0 is the logit intercept, H_POP the coefficient on z_log_pop.
#
# A channel we measured at 58/58 is UNIVERSAL, not merely very likely. Writing
# that as H0 = +9.9 leaves a one-in-twenty-thousand failure, which over enough
# seeds produces a county with no grand jury -- a thing that cannot happen,
# since the report is statutorily mandated. So `channel_exists` treats
# H0 >= UNIVERSAL_H0 with a zero population slope as a declared certainty. The
# coefficient still reads as a logit so the hurdle stays one mechanism.
UNIVERSAL_H0 = 9.0
CHANNEL_EXISTS = {
    "county_sub": (
        Coef(2.10, "measured_anchor", REGISTER,
             "9 of 58 counties have no candidate subreddit; H0=2.10 with H_POP=1.35 "
             "gives 9.7 expected. The spec's first draft (1.55 -> 13.6) overstated the "
             "disappearing commons by 50%, which would have flattered our own hypothesis."),
        Coef(1.35, "measured_anchor", REGISTER,
             "candidate-subreddit count correlates with ln(pop) at r=0.741")),
    "statewide_sub": (
        Coef(9.9, "measured_anchor", REGISTER,
             "r/California and the programme subs always exist; they rescue 8 of the 9 "
             "counties with no sub of their own, so ANY-evidence existence is 57/58 "
             "even though county-sub existence is 49/58"),
        Coef(0.0, "measured_anchor", REGISTER, "a statewide sub's existence is independent of county size")),
    "admin_forum": (
        Coef(9.9, "measured_anchor", REGISTER,
             "the CalGuns control case: 58/58 county threads created in one batch on "
             "2010-10-14/15. Existence was assigned administratively and carries no "
             "population signal whatsoever."),
        Coef(0.0, "measured_anchor", REGISTER, "see above; this is the point of the control")),
    "regional_forum": (
        Coef(0.4, "design_assumption", REGISTER, "City-Data county subforums thin out; not counted"),
        Coef(0.6, "design_assumption", REGISTER, "")),
    "review_site": (
        Coef(2.2, "derived_with_assumptions", "docs/scoping/2026-09-16-forums-beyond-reddit.md",
             "place entities exist for rural offices (verified for Modoc County Social "
             "Services), so existence is probably near-universal; review VOLUME unmeasured"),
        Coef(0.9, "design_assumption", REGISTER, "")),
    "grand_jury": (
        Coef(9.9, "measured_anchor", "docs/scoping/2026-09-16-forums-beyond-reddit.md",
             "a civil grand jury is mandated in all 58 counties and 8 of the 9 counties "
             "with no subreddit publish fetchable reports. The best-evidenced inversion "
             "against reddit in the project."),
        Coef(0.0, "measured_anchor", "docs/scoping/2026-09-16-forums-beyond-reddit.md",
             "mandate is universal, so existence has no population slope. VOLUME is NOT "
             "counted at title level and must not be given a fitted slope.")),
    "staff_review_site": (
        Coef(-0.2, "design_assumption", REGISTER,
             "Glassdoor/Indeed reviews by county staff exist only where there are enough staff"),
        Coef(1.1, "design_assumption", REGISTER, "")),
    "official_stats": (
        Coef(9.9, "measured_anchor", APR,
             "every county appears in the statewide APR panel; 58/58. A per-county "
             "publication hurdle would be modelling the wrong stage."),
        Coef(0.0, "measured_anchor", APR, "")),
}

# ---------------------------------------------------------------- volume slopes
# V0 is the log-mean intercept, V_POP the per-channel coefficient on z_log_pop.
# V_POP is per channel because the measured slopes differ by more than 50%.
CHANNEL_VOLUME = {
    "county_sub": (
        Coef(2.159, "measured_anchor", SWEEP,
             "calibrated so the REALIZED median is 13 distinct posts per county-programme "
             "cell, the measured value. The coefficient is larger than log(13) because the "
             "existence hurdle, the Poisson draw and the log1p floor all attenuate."),
        Coef(1.250, "measured_anchor", REGISTER,
             "calibrated JOINTLY with statewide_sub, because the sweep deduplicated a post "
             "to one county whichever venue carried it. The union of the two channels "
             "realises: per-cell median 14 against the measured 13, mean 38.1 against "
             "39.6, zero share 7.4% against 7%, county-total log10-log10 slope 0.701 "
             "against 0.747, and 57.7 of 58 counties with any user evidence against 57. "
             "Calibrating county_sub ALONE put the zero share at 22%, because it charged "
             "the 9 counties with no forum of their own with having no evidence at all -- "
             "the same overstatement of the disappearing commons the W2 spec rejected when "
             "it tuned its own hurdle. The spec's V_POP=0.85 implies a slope of only 0.539 "
             "and so made rural counties look better supplied than they are.")),
    "statewide_sub": (
        Coef(1.800, "measured_anchor", SWEEP,
             "calibrated jointly with county_sub so the UNION leaves 7.4% of "
             "county-programme cells empty against the measured 7%, and 57.7 of 58 "
             "counties with some user evidence against the measured 57. This channel is "
             "what rescues the counties with no forum of their own: they are not "
             "evidence-free, they are evidence-thin, and that difference is the whole "
             "rural-commons argument."),
        Coef(1.10, "derived_with_assumptions", REGISTER,
             "assumed slightly steeper than a county sub: naming your county in a "
             "statewide venue is something urban posters do more. Not separately measured, "
             "because the sweep cannot tell a statewide hit from a county-sub hit once "
             "both are deduplicated to one post.")),
    "admin_forum": (
        Coef(4.948, "measured_anchor", SWEEP,
             "calibrated to a realized median of 155 thread replies per county against the "
             "measured 156; real max 19,262 with 3 counties at zero replies"),
        Coef(2.246, "measured_anchor", REGISTER,
             "calibrated to a realized log10-log10 slope of 1.160 against the measured "
             "1.157. Super-linear: volume concentrates harder than population, the opposite "
             "of the sub-linear reddit slope in the same evidence tier.")),
    "official_stats": (
        Coef(8.537, "measured_anchor", APR,
             "calibrated to a realized median of 5,522 APR project records per county "
             "against the measured 5,461. The observed tier is ~150x the user tier."),
        Coef(1.835, "measured_anchor", APR,
             "calibrated to a realized log10-log10 slope of 0.989, matching the measurement "
             "exactly. Almost perfectly linear in population, i.e. per-capita constant -- "
             "administrative records behave unlike either user channel.")),
    "grand_jury": (
        Coef(1.0, "design_assumption", "docs/scoping/2026-09-16-forums-beyond-reddit.md",
             "1 report-year doc in the smallest counties to 10-25/yr in a large one; "
             "statewide order 5,000-15,000 docs over 20 years, title-level count NOT made"),
        Coef(0.35, "design_assumption", "docs/scoping/2026-09-16-forums-beyond-reddit.md",
             "deliberately shallow, NOT fitted. Rural reports are more on-topic per "
             "document, so a steep slope here would erase the inversion we actually observed.")),
    "regional_forum": (Coef(0.2, "design_assumption", REGISTER, ""),
                       Coef(0.9, "design_assumption", REGISTER, "")),
    "review_site": (Coef(1.1, "design_assumption", REGISTER, ""),
                    Coef(1.2, "design_assumption", REGISTER, "")),
    "staff_review_site": (Coef(0.3, "design_assumption", REGISTER, ""),
                          Coef(1.4, "design_assumption", REGISTER, "")),
}

# Shared volume terms, applied to every channel.
V_CASELOAD = Coef(0.30, "design_assumption", REGISTER,
                  "more cases, more posts; plausible but not separated from population "
                  "in our data, where caseload and population are nearly collinear")
V_DELAY = Coef(0.0, "measured_anchor", REGISTER,
               "THE SCENARIO VARIABLE. The W2 spec planted 0.55 ('delay generates posts', "
               "the selection mechanism kappa). Measured at county level across 50 counties: "
               "+0.076 with a delta-R2 of 0.004 after controlling for population, and the "
               "sign FLIPS NEGATIVE (-0.034) for timing-bearing posts. The raw correlation "
               "of +0.44 is population confounding (delay~pop r=+0.50). Default 0.0 per the "
               "plan's rule on unidentified directions; see SCENARIOS for the alternatives. "
               "The mechanism may still live at CASE level -- delayed applicants posting -- "
               "which this county-level test cannot see.")
SIGMA_CELL = Coef(0.3, "measured_anchor", SWEEP,
                  "cell-level overdispersion. The real per-cell counts are strongly "
                  "right-skewed -- mean 39.6 against median 13, a ratio of 3.0 -- which a "
                  "pure Poisson cannot produce, since Poisson has variance equal to its "
                  "mean. So the volume is Poisson-lognormal: the county effect SIGMA_V "
                  "plus this within-county, between-programme term. Fitted jointly with "
                  "V0 and V_POP against the median, the mean and the 7% zero share. NOTE "
                  "the real maximum of 303 is CENSORED by the search API's 100-result "
                  "limit, so the upper tail is not a target.")
SIGMA_V = Coef(0.6, "design_assumption", REGISTER,
               "a shared county volume effect; sized so the residual spread does not "
               "swamp the measured population gradient")
RHO_UV = Coef(0.3, "design_assumption", REGISTER,
              "correlation between the disclosure effect u_c and the volume effect v_c: a "
              "county that publishes nothing also tends to have a thin civic internet. "
              "Kept low so that ~14 counties have both official_stats and forum posts, "
              "which is the sample size for kappa.")

# --------------------------------------------------------------- the funnel
# Conditional retrieval probabilities per source family, measured per county in
# the P5 packet. READ AS JOINT RATES, NOT PUBLICATION RATES: the packet spent
# ~1 fetch per county-programme, so each stage is publication x indexing x our
# own bounded search depth. That makes them the right calibration for what a
# bounded solver finds, and a lower bound on what is published.
FUNNEL = {
    "septic": Coef((0.98, 0.84, 0.08, 0.67), "measured_anchor", P5,
                   "57/48/3/2 of 58 for located / authority evidenced / fetched / "
                   "operative version verified. The 3% floor is partly structural: a LAMP "
                   "is an OPTIONAL Tier 2 instrument, so a missing document can mean the "
                   "county lawfully uses Tier 1, not that retrieval failed."),
    "wells": Coef((1.00, 0.38, 0.73, 0.0), "measured_anchor", P5,
                  "58/22/16/0 of 58. The terminal zero is a finding about identifiability, "
                  "not a gap: 52 counties are not_verified and 4 are explicitly "
                  "'not established, not a negative finding'."),
    "retail_food": Coef((1.00, 0.47, 0.74, 0.35), "measured_anchor", P5,
                        "58/27/20/7 of 58; the shallowest of the three and the only one "
                        "where a quarter of counties yield a scoreable local policy choice"),
    "housing": Coef((1.00, 0.83, 0.43, 0.30), "derived_with_assumptions",
                    "docs/scoping/2026-09-16-adu-58-counties.md",
                    "ADU documents were located for most counties but only 46 of 57 were "
                    "verified; the deeper stages are interpolated from the env-health "
                    "families and are NOT independently counted"),
}
FUNNEL_STAGES = ("located", "authority_evidenced", "document_read", "operative_policy_established")

# --------------------------------------------------- information-bearing share
# Volume and information run in opposite directions, so a document count is not
# an information count. These are the measured fractions that carry a usable
# quantity.
INFORMATIVE_SHARE = {
    "official_stats": Coef(0.106, "measured_anchor", APR,
                           "97,983 of 922,104 APR project records carry a measurable "
                           "entitlement-to-permit span"),
    "user_post": Coef(0.32, "measured_anchor", SWEEP,
                      "1,597 of 4,998 distinct posts contain a duration word. NOTE the "
                      "per-cell distribution matters more than the mean: the MEDIAN "
                      "county-programme cell has ONE timing-bearing post and 38% have none."),
}

# --------------------------------------------------------------- defect rates
# The plan asks for controlled versions of observed defects. These are the ones
# we actually hit, at the rate we hit them.
DEFECTS = {
    "clock_collapse": Coef(2 / 50, "measured_anchor", APR,
                           "Madera and Plumas report a weighted median entitlement-to-permit "
                           "span of exactly 0 days: the same-date filing habit"),
    "reported_zero_artifact": Coef(82 / 193, "measured_anchor", APR,
                                   "82 of 193 jurisdictions report exactly zero withdrawals; "
                                   "withdrawal is a REPORTING variable, not a case attribute"),
    "date_present_by_habit": Coef(0.50, "measured_anchor",
                                  "corpus/counties/apr_discretion_by_jurisdiction.csv",
                                  "P(entitlement date present | ministerial route) has p10 0.00, "
                                  "median 0.50, p90 1.00 across jurisdictions: a filing habit, "
                                  "not a project attribute"),
    "http_error": Coef(1 / 13, "measured_anchor", "corpus/counties/p5_source_manifest.json",
                       "1 of 13 recorded retrieval failures was an HTTP 500 on a live "
                       "official dataset landing page. Not absence of data."),
    "image_only_pdf": Coef(0.33, "derived_with_assumptions",
                           "docs/scoping/2026-09-16-forums-beyond-reddit.md",
                           "about a third of rural grand jury PDFs are image-only and need OCR"),
    "access_blocked": Coef(7 / 58, "measured_anchor",
                           "docs/scoping/2026-09-16-forums-beyond-reddit.md",
                           "grand jury retrieval: 4 counties 403, 1 JS-only DocBox, 1 Drive "
                           "folder, 1 email-only"),
    "result_truncated": Coef(10 / 58, "measured_anchor", SWEEP,
                             "10 of 58 counties had at least one search return exactly the "
                             "API limit, so their counts are lower bounds"),
    "duplicate_record_id": Coef(1 / 22, "measured_anchor",
                                "docs/scoping/2026-09-16-wide-net-retrieval.md",
                                "Sonoma's permit export has duplicate record IDs"),
    "date_order_anomaly": Coef(1 / 22, "measured_anchor",
                               "docs/scoping/2026-09-16-wide-net-retrieval.md",
                               "San Diego's export has issuance dates before opening dates"),
}

# ----------------------------------------------------------------- scenarios
# The plan's three declared regimes, as coefficient overrides. `reference` is
# the measured world. Each alternative names what it is testing, so a result can
# say which assumption it depended on.
SCENARIOS = {
    "reference": dict(
        note="the measured world: per-family slopes from the register, V_DELAY at its "
             "measured ~0, funnel rates as counted",
        overrides={}),
    "evidence_constrained": dict(
        note="the W2 spec's original selection story, retained as an alternative rather "
             "than deleted: delay generates posts at the spec's planted 0.55",
        overrides={"V_DELAY": 0.55}),
    "delay_suppresses": dict(
        note="the sign our timing-bearing regression actually showed (-0.034, scaled up to "
             "be detectable). If a result survives both this and evidence_constrained, it "
             "does not depend on the direction of kappa.",
        overrides={"V_DELAY": -0.40}),
    "rural_commons_moves": dict(
        note="the grand-jury inversion made strong enough to REVERSE the rural information "
             "ranking. Tests whether a conclusion about rural counties is an artifact of "
             "which channel we happened to sweep.",
        overrides={"GRAND_JURY_V_POP": -0.30}),
    "flat_availability": dict(
        note="the null the register argues against: one availability slope for every "
             "channel. A method that only works here is fitted to a wrong world.",
        overrides={"UNIFORM_V_POP": 1.31}),
}


def scenario_coefs(scenario: str = "reference") -> dict:
    """Resolved coefficient overrides for a named scenario."""
    if scenario not in SCENARIOS:
        raise ValueError("unknown scenario %r; have %s" % (scenario, sorted(SCENARIOS)))
    return dict(SCENARIOS[scenario]["overrides"])


# ------------------------------------------------------------------ mechanisms

def _logistic(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-min(x, 60.0)))
    e = math.exp(max(x, -60.0))
    return e / (1.0 + e)


def channel_exists(county: dict, channel: str, seed: int) -> bool:
    """Stage one of the hurdle: does this county have this channel at all?

    Keyed on (county, channel) rather than drawn from a passed-in rng, so that
    adding a channel never reshuffles another channel's draw.
    """
    h0, hpop = CHANNEL_EXISTS[channel]
    if v(h0) >= UNIVERSAL_H0 and v(hpop) == 0.0:
        return True                       # measured at 58/58; see UNIVERSAL_H0
    p = _logistic(v(h0) + v(hpop) * z_log_pop(county))
    return chance(sub_rng(seed, "channel_exists", county["id"], channel), p)


def post_volume(county: dict, channel: str, seed: int, *, scenario: str = "reference",
                caseload_z: float = 0.0, delay_z: float = 0.0,
                volume_effect: float = 0.0, programme: str = "") -> int:
    """Stage two: how much, given that it exists. Zero if it does not.

    The unit is the (county, channel, PROGRAMME) cell, because that is the unit
    the register measured: a median of 13 distinct posts per county-programme
    cell, 38% of cells empty. Drawing one number per county and reusing it for
    every programme would apply the county's whole budget to each process and
    flatten the population gradient -- which measured 0.32 against the true 0.75
    before this argument existed.

    `volume_effect` is the county's shared v_c, supplied by the caller so the
    same draw is reused across channels and programmes within a county (that
    within-county correlation is the point of SIGMA_V/RHO_UV).
    """
    if not channel_exists(county, channel, seed):
        return 0
    over = scenario_coefs(scenario)
    v0, vpop = CHANNEL_VOLUME[channel]
    slope = v(vpop)
    if "UNIFORM_V_POP" in over:
        slope = over["UNIFORM_V_POP"]
    elif channel == "grand_jury" and "GRAND_JURY_V_POP" in over:
        slope = over["GRAND_JURY_V_POP"]
    delay_coef = over.get("V_DELAY", v(V_DELAY))
    rng = sub_rng(seed, "post_volume", county["id"], channel, programme)
    lam = math.exp(v(v0) + slope * z_log_pop(county)
                   + v(V_CASELOAD) * caseload_z + delay_coef * delay_z
                   + v(SIGMA_V) * volume_effect
                   + v(SIGMA_CELL) * rng.gauss(0.0, 1.0))
    return _poisson(rng, lam)


def county_effects(county: dict, seed: int) -> tuple[float, float]:
    """(u_c, v_c): the county's disclosure and volume effects, correlated at RHO_UV."""
    rng = sub_rng(seed, "county_effects", county["id"])
    u = rng.gauss(0.0, 1.0)
    rho = v(RHO_UV)
    return u, rho * u + math.sqrt(max(0.0, 1.0 - rho * rho)) * rng.gauss(0.0, 1.0)


def funnel_outcome(county: dict, family: str, seed: int) -> str:
    """How far retrieval gets for this county and family: the deepest stage reached.

    Returns one of `not_located` or a member of FUNNEL_STAGES. The stages are
    conditional, so a county that fails at `authority_evidenced` never reaches
    `document_read` -- which is the shape that makes "we know a rule exists but
    do not hold its text" the common state it really is.
    """
    rates = v_tuple(FUNNEL[family])
    rng = sub_rng(seed, "funnel", county["id"], family)
    reached = "not_located"
    for stage, p in zip(FUNNEL_STAGES, rates):
        if not chance(rng, p):
            return reached
        reached = stage
    return reached


def v_tuple(c) -> tuple:
    return tuple(c.value) if isinstance(c, Coef) else tuple(c)


def _poisson(rng, lam: float) -> int:
    """Knuth for small lam, normal approximation above 30. Stdlib only."""
    if lam <= 0:
        return 0
    if lam <= 30:
        target = math.exp(-lam)
        k, p = 0, 1.0
        while True:
            p *= rng.random()
            if p <= target:
                return k
            k += 1
            if k > 1000:
                return k
    return max(0, int(round(rng.gauss(lam, math.sqrt(lam)))))



# ----------------------------------------------------------- adopted fee rates
# The hand-written six jurisdictions carry literal hourly rates; a generated
# county needs one derived. The real gradient is shallow: average local-
# government annual wage runs ln(wage) = 10.371 + 0.0658*ln(pop) with r = 0.675,
# i.e. a 10x larger county pays only about 16% more per hour. So an adopted
# billing rate should NOT scale steeply with size, and a generator that made
# fees track population strongly would invent a relationship the payroll data
# denies.
WAGE_INTERCEPT = Coef(10.371, "measured_anchor", "ca_counties_covariates.csv",
                      "ln(avg_local_govt_wage_2023) regressed on ln(pop_2023), n=58")
WAGE_POP_SLOPE = Coef(0.0658, "measured_anchor", "ca_counties_covariates.csv",
                      "r = 0.675. Shallow on purpose: wages barely track county size, "
                      "unlike staffing per capita which runs strongly INVERSE to it.")
FEE_OVERHEAD = Coef(5.5, "derived_with_assumptions",
                    "docs/scoping/2026-09-16-permit-labor-target.md",
                    "an adopted cost-recovery rate is the bare hourly wage times an "
                    "indirect-cost multiplier covering supervision, facilities and "
                    "benefits. 5.5 places the median county at ~$183/hour, matching the "
                    "median of the hand-written table. The multiplier is an assumption; "
                    "fee divided by rate is NOT measured labour.")
WORK_HOURS_PER_YEAR = 2080


def hourly_rate(county: dict) -> int:
    """The county's adopted cost-recovery hourly rate, in whole dollars."""
    pop = max(int(county.get("pop") or 1), 1)
    wage = math.exp(v(WAGE_INTERCEPT) + v(WAGE_POP_SLOPE) * math.log(pop))
    return int(round(wage / WORK_HOURS_PER_YEAR * v(FEE_OVERHEAD)))


# ------------------------------------------------------------- process speed
# The plan flags "a county's population determines its intrinsic speed" as a
# HYPOTHESIS, not an estimate, and requires null and alternative-sign settings.
# So here is what the real data says, and what it does not.
#
# Measured on the APR entitlement-to-permit clock, 50 counties with at least 30
# dated spans: ln(1+median days) = const + 0.4988*ln(pop), r = +0.498, so
# population explains 25% of the between-county variance and the largest county
# is about 6.3x slower than the smallest. Bigger is SLOWER.
#
# Two reasons that slope is not a causal county effect, both of which the
# generator honours by keeping the residual large:
#   * The clock is county-AGGREGATED over its cities, and a large county holds
#     more large cities, so part of the gradient is compositional rather than
#     intrinsic.
#   * The clock starts at the completeness date, not at first submission, so it
#     is a lower bound whose bias may itself vary with county size.
# The residual sd in log space is 1.368 against a total sd of 1.578: most of a
# county's speed is NOT recoverable from its public covariates, and a generator
# that shrank this residual would hand the estimator a gift the real world
# withholds.
SPEED_POP_SLOPE = Coef(0.4988, "measured_anchor", APR,
                       "ln(1+median entitlement-to-permit days) on ln(pop), n=50, r=+0.498. "
                       "Bigger counties are slower. NOT established as causal: the clock is "
                       "aggregated over a county's cities and starts at completeness.")
SPEED_SIGMA = Coef(1.368, "measured_anchor", APR,
                   "residual sd of ln(1+delay) after population, against a total sd of "
                   "1.578. Population explains only 25% of between-county timing variance.")
SPEED_CENTRE = Coef(1.15, "derived_with_assumptions", APR,
                    "the multiplier is centred on the mean of the hand-written table "
                    "(1.0/1.25/1.4/1.15) so that v1 and v2 worlds have comparable pace")

# The plan requires a null and an alternative sign for this relationship.
SPEED_SCENARIOS = {
    "reference": v(SPEED_POP_SLOPE),
    "speed_null": 0.0,          # county size tells you nothing about pace
    "speed_inverse": -0.4988,   # small counties slower: the intuitive story, inverted
}


# The measured log-scale spread (total sd 1.578) would give a 100-fold range of
# process durations, which no renderer can turn into plausible documents. So the
# spread is COMPRESSED by a common factor while the RATIO of explained to
# unexplained variance is preserved exactly -- that ratio, not the absolute
# spread, is what determines how much an estimator can recover from covariates.
# Solving a/sqrt(a^2+s^2) = 0.498 with a total log sd of 0.37 (a ~6x duration
# range, matching the real 6.3x) gives the two damping factors below.
SPEED_SLOPE_DAMP = Coef(0.37, "derived_with_assumptions", APR,
                        "compresses the measured slope so durations stay renderable; "
                        "chosen jointly with SPEED_SIGMA_DAMP to hold r at +0.498")
SPEED_SIGMA_DAMP = Coef(0.275, "derived_with_assumptions", APR,
                        "same compression applied to the residual, so the 25% explained "
                        "share is preserved rather than inflated. Solved over 30 seeds to "
                        "a realised r of +0.50 and a 6.2x duration range, against the "
                        "measured +0.498 and 6.3x.")


def speed_factor(county: dict, seed: int, *, scenario: str = "reference") -> float:
    """A county's pace multiplier: >1 is slower. Mostly unexplained on purpose."""
    slope = SPEED_SCENARIOS.get(scenario, v(SPEED_POP_SLOPE))
    rng = sub_rng(seed, "speed", county["id"])
    resid = rng.gauss(0.0, v(SPEED_SIGMA) * v(SPEED_SIGMA_DAMP))
    raw = v(SPEED_CENTRE) * math.exp(
        slope * v(SPEED_SLOPE_DAMP) * z_log_pop(county) + resid)
    return max(0.45, min(4.0, raw))


# ---------------------------------------------------------------- caseload
# A county's case volume is very nearly proportional to its population: the APR
# panel's project counts regress on population with a log-log slope of 0.989
# (r = 0.950), so per-capita demand is effectively constant. That is a different
# fact from staffing, which runs strongly INVERSE to size, and the two together
# are what make large counties slower per case.
CASELOAD_POP_SLOPE = Coef(0.989, "measured_anchor", APR,
                          "ln(APR projects) on ln(pop), n=58, r=0.950. Per-capita demand "
                          "is constant, so caseload scales with population.")
CASELOAD_FLOOR = Coef(12, "measured_anchor", APR,
                      "the smallest real county reports 61 projects across 8 years and all "
                      "unit categories; a per-process floor of 12 keeps a tiny county's "
                      "process non-empty without inventing demand")
CASELOAD_CEILING = Coef(6000, "design_assumption", APR,
                        "a render and runtime backstop, not a measured limit. The real "
                        "maximum is 195,483 projects; simulating that per process would "
                        "dominate build time for no benchmark gain.")


def caseload(county: dict, median_caseload: int) -> int:
    """Applicants for one process in this county, scaled from a median county.

    The slope is already expressed per unit of ln(population), so it multiplies
    the raw log deviation from the panel mean rather than a z-score.
    """
    pop = max(int(county.get("pop") or 1), 1)
    n = round(median_caseload * math.exp(
        v(CASELOAD_POP_SLOPE) * (math.log(pop) - v(LOG_POP_MEAN))))
    return max(int(v(CASELOAD_FLOOR)), min(int(v(CASELOAD_CEILING)), int(n)))


# ------------------------------------------------------------------ reporting

def all_coefs() -> list[tuple[str, Coef]]:
    out: list[tuple[str, Coef]] = []
    for name, c in (("LOG_POP_MEAN", LOG_POP_MEAN), ("LOG_POP_SD", LOG_POP_SD),
                    ("V_CASELOAD", V_CASELOAD), ("V_DELAY", V_DELAY),
                    ("SIGMA_V", SIGMA_V), ("SIGMA_CELL", SIGMA_CELL), ("RHO_UV", RHO_UV),
                    ("WAGE_INTERCEPT", WAGE_INTERCEPT), ("WAGE_POP_SLOPE", WAGE_POP_SLOPE),
                    ("FEE_OVERHEAD", FEE_OVERHEAD), ("SPEED_POP_SLOPE", SPEED_POP_SLOPE),
                    ("SPEED_SIGMA", SPEED_SIGMA), ("SPEED_CENTRE", SPEED_CENTRE),
                    ("SPEED_SLOPE_DAMP", SPEED_SLOPE_DAMP),
                    ("SPEED_SIGMA_DAMP", SPEED_SIGMA_DAMP),
                    ("CASELOAD_POP_SLOPE", CASELOAD_POP_SLOPE),
                    ("CASELOAD_FLOOR", CASELOAD_FLOOR),
                    ("CASELOAD_CEILING", CASELOAD_CEILING)):
        out.append((name, c))
    for ch, (h0, hp) in CHANNEL_EXISTS.items():
        out.append(("CHANNEL_EXISTS[%s].H0" % ch, h0))
        out.append(("CHANNEL_EXISTS[%s].H_POP" % ch, hp))
    for ch, (v0, vp) in CHANNEL_VOLUME.items():
        out.append(("CHANNEL_VOLUME[%s].V0" % ch, v0))
        out.append(("CHANNEL_VOLUME[%s].V_POP" % ch, vp))
    for fam, c in FUNNEL.items():
        out.append(("FUNNEL[%s]" % fam, c))
    for k, c in INFORMATIVE_SHARE.items():
        out.append(("INFORMATIVE_SHARE[%s]" % k, c))
    for k, c in DEFECTS.items():
        out.append(("DEFECTS[%s]" % k, c))
    return out


def provenance_report() -> dict:
    """Counts by provenance, and the full table. Written into the world bundle."""
    coefs = all_coefs()
    by = {}
    for _n, c in coefs:
        by[c.provenance] = by.get(c.provenance, 0) + 1
    return {
        "n_coefficients": len(coefs),
        "by_provenance": by,
        "register": REGISTER,
        "coefficients": [
            dict(name=n, value=c.value, provenance=c.provenance, source=c.source, note=c.note)
            for n, c in coefs],
        "scenarios": {k: dict(note=s["note"], overrides=s["overrides"]) for k, s in SCENARIOS.items()},
    }


if __name__ == "__main__":
    import json
    rep = provenance_report()
    print("%d planted coefficients" % rep["n_coefficients"])
    for p, n in sorted(rep["by_provenance"].items(), key=lambda kv: -kv[1]):
        print("  %-26s %3d  %4.0f%%" % (p, n, 100 * n / rep["n_coefficients"]))
    print("\nunsourced design assumptions (the audit surface):")
    for c in rep["coefficients"]:
        if c["provenance"] == "design_assumption":
            print("  %-42s %-8s %s" % (c["name"], c["value"], c["note"][:60] or "(no note)"))
    print("\nscenarios: %s" % ", ".join(rep["scenarios"]))
    print(json.dumps(rep["by_provenance"]))
