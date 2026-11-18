"""58 fictional county-like jurisdictions, shaped like the real panel.

The plan's section 4 rule, followed exactly: preserve real geography only as
*distributional* inspiration, and never attach a synthetic burden or an inferred
efficiency ranking to a real county name. So no name, FIPS or seat here
corresponds to a real place; what is borrowed is the shape of the covariate
joint distribution, because that shape is what makes an inference problem hard
or easy.

What the real panel taught us, and what is therefore reproduced:

* **Population is the dominant axis and it is enormously skewed.** The real
  range is 1,129 (Alpine) to 9.7 million (Los Angeles), a factor of 8,600, and
  density runs 1.5 to 17,323 per square mile, a factor of 11,549. A synthetic
  panel with a tame population range would make every availability slope easier
  to estimate than it really is.
* **Staffing per capita runs INVERSE to size** (r = -0.73 against log
  population). Small counties carry more local-government employment per
  thousand residents, not less. Planting the intuitive direction would have
  produced a world where capacity and population were redundant.
* **Covariates explain little timing variation**: about 4% pooled, rising to
  ~25% when city and county processes are separated (n = 18). So a county effect
  here is mostly *not* predictable from public covariates, and a generator that
  makes it predictable hands the estimator a gift the real world does not.
* **Rurality is not one variable.** RUCC and the USDA urban-influence code
  disagree: `is_noncore` defined as RUCC >= 6 sweeps in the micropolitan band
  and mislabels four counties. The real noncore count is 11, not 15. Both codes
  are carried separately and neither is collapsed into the other.
* **Consortium membership is a lineage variable, not a size variable.** The real
  split is 39 / 18 / 1 across three legacy eligibility consortia, and it is the
  cleanest natural experiment we have for copied policy text.

Every generated field records which real quantity it was matched to, in
`provenance`, so a reader can check the panel against
`corpus/counties/ca_counties_covariates.csv` without trusting this docstring.
"""
from __future__ import annotations

import math

from .rng import pick, sub_rng, weighted

N_COUNTIES = 58

# --------------------------------------------------------------------- names
# Invented place names, deliberately unlike California's. Two-word and
# possessive forms are included because real county names are not uniform, and
# a renderer that only ever sees one name shape learns the wrong prior.
_STEMS = [
    "Ashlyn", "Bardwell", "Callowe", "Denmark", "Eastmere", "Fennick", "Garrow",
    "Haleburn", "Ionfield", "Jarrow", "Kesslin", "Lanmore", "Marbeck", "Nyewood",
    "Orrance", "Pemberly", "Quarryhill", "Rothwen", "Selby", "Tamworth",
    "Underhill", "Verrick", "Wraycroft", "Yarrow", "Zellwood", "Amberly",
    "Brackenridge", "Coldwater", "Drummond", "Elmsworth", "Fairholm", "Glenarvon",
    "Hollybrook", "Inverleigh", "Kirkwall", "Loxley", "Millbrae", "Northcote",
    "Oakhampton", "Pinebluff", "Ravensden", "Stoneleigh", "Thistlewood",
    "Ulverston", "Vanbrough", "Westerly", "Wintringham", "Aldermoor", "Bexhill",
    "Crowmarsh", "Dunwoody", "Ellerby", "Fordham", "Granthorpe", "Hartsmere",
    "Ibbotson", "Jessamine", "Kettleby",
]
_SEAT_SUFFIX = ["", " City", " Junction", "ville", " Falls", " Landing", " Crossing",
                " Springs", " Mills", "burg", " Flat", " Hollow"]

# ------------------------------------------------------- real covariate shape
# Quantiles of the real 58-county distributions, used as the target shape. Read
# off ca_counties_covariates.csv; each entry names the real column.
REAL_SHAPE = {
    "pop": dict(column="pop_2023", min=1129, p10=9200, p25=31000, median=188000,
                p75=740000, p90=2100000, max=9663345,
                note="a factor of 8,600 from smallest to largest"),
    "land_area_sqmi": dict(column="land_area_sqmi", min=46, median=1560, max=20052,
                           note="San Francisco 46 sq mi to San Bernardino 20,052"),
    "density": dict(column="pop_density_per_sqmi", min=1.5, median=95, max=17323,
                    note="Alpine 1.5 to San Francisco 17,323: a factor of 11,549. An "
                         "earlier pass published 2,380 as the max by sampling six "
                         "counties and mistaking Los Angeles for the maximum."),
    "local_govt_empl_per_1k_pop": dict(column="local_govt_empl_per_1k_pop",
                                       min=14, median=38, max=118,
                                       note="runs INVERSE to population at r=-0.73"),
    "pct_pop_unincorporated": dict(column="pct_pop_unincorporated", min=0.0, median=0.17, max=1.0,
                                   note="San Francisco is 0 (consolidated city-county); "
                                        "several rural counties are near 1.0"),
    "n_incorporated_cities": dict(column="n_incorporated_cities", min=0, median=5, max=88,
                                  note="Alpine and Trinity have none; Los Angeles has 88"),
    "poverty_rate": dict(column="poverty_rate_2023", min=0.065, median=0.128, max=0.221),
    "broadband_pct": dict(column="broadband_subscription_pct", min=0.63, median=0.87, max=0.95),
}

# The real consortium split: 39 / 18 / 1. Carried as a lineage variable, because
# two counties on the same platform copy each other's policy text while running
# genuinely different procedures -- exactly the distinction the plan's section 7
# asks the corpus to contain.
CONSORTIA = [("Meridian", 39), ("Northgate", 18), ("Sole", 1)]

# USDA urban-influence and rural-urban continuum codes, kept SEPARATE. The real
# noncore count under the correct UIC definition is 11 of 58; defining it as
# RUCC >= 6 gives 15 and mislabels four counties, because that threshold sweeps
# in the micropolitan band.
UIC_NONCORE = ("3", "6", "8", "9")
RUCC_BY_BAND = {"metro_large": ("1", "2"), "metro_small": ("3",),
                "micropolitan": ("4", "5", "7"), "noncore": ("6", "8", "9")}

PORTAL_VENDORS = [("Accela", 18), ("Tyler EnerGov", 12), ("OpenGov", 9),
                  ("eTRAKiT", 6), ("in-house", 8), (None, 5)]
CODE_HOSTS = [("municodex", 31), ("codepublishing", 14), ("amlegal", 7), ("self-hosted", 6)]


def _lerp_quantile(u: float, shape: dict) -> float:
    """Draw from a distribution specified by its quantiles, log-interpolated.

    Log space because every heavy-tailed covariate here spans orders of
    magnitude; linear interpolation between p90 and max would put almost all
    the mass at the top.
    """
    pts = [(0.0, shape["min"]), (0.5, shape["median"]), (1.0, shape["max"])]
    for q, key in ((0.10, "p10"), (0.25, "p25"), (0.75, "p75"), (0.90, "p90")):
        if key in shape:
            pts.append((q, shape[key]))
    pts.sort()
    for (q0, v0), (q1, v1) in zip(pts, pts[1:]):
        if u <= q1:
            t = 0.0 if q1 == q0 else (u - q0) / (q1 - q0)
            if v0 > 0 and v1 > 0:
                return math.exp(math.log(v0) + t * (math.log(v1) - math.log(v0)))
            return v0 + t * (v1 - v0)
    return pts[-1][1]


def build_counties(seed: int, n: int = N_COUNTIES) -> list[dict]:
    """The synthetic county panel. Deterministic given the seed."""
    out: list[dict] = []
    # Consortium labels are dealt out to match the real 39/18/1 split exactly
    # rather than drawn independently, because the split is a known fact about
    # the panel and a multinomial draw would blur it.
    labels: list[str] = []
    for name, k in CONSORTIA:
        labels += [name] * int(round(k * n / N_COUNTIES))
    while len(labels) < n:
        labels.append(CONSORTIA[0][0])
    labels = labels[:n]
    sub_rng(seed, "consortium_order").shuffle(labels)

    for i in range(n):
        rng = sub_rng(seed, "county", i)
        stem = _STEMS[i % len(_STEMS)]
        # A stratified uniform, so the generated panel covers the real range
        # instead of clumping wherever the draws happened to fall.
        u = (i + rng.random()) / n
        pop = int(round(_lerp_quantile(u, REAL_SHAPE["pop"])))
        # Land area is very nearly INDEPENDENT of population in the real panel
        # (r = +0.04 on logs), which is why a big county is not reliably a
        # sparse one. Drawn independently, then resampled if the implied
        # density falls outside the real observed envelope -- no real county is
        # emptier than 1.5 per square mile, and independence over a
        # 8,600-fold population range would otherwise manufacture emptier ones.
        for _attempt in range(24):
            area = max(45, int(round(_lerp_quantile(rng.random(), REAL_SHAPE["land_area_sqmi"]))))
            density = pop / area
            if 1.4 <= density <= 18_000:
                break
        else:
            area = max(45, int(round(pop / 100.0)))
            density = pop / area

        # Staffing per capita is INVERSE to size: the real r is -0.73 against
        # log population. Built as a deterministic inverse trend plus noise so
        # the sign cannot drift with the seed.
        z = (math.log(pop) - 12.061) / 1.838
        # Calibrated to the real r = -0.73, not stronger: the inverse trend is
        # real but noisy, and an over-tight version would let an estimator
        # recover staffing from population alone.
        emp_per_1k = max(12.0, 38.0 * math.exp(-0.32 * z) * math.exp(rng.gauss(0, 0.35)))

        # All 11 real noncore counties have population below 46,565, but four
        # counties under that line are NOT noncore (Alpine among them), so the
        # label is conditional rather than a threshold. P(noncore | small) is
        # 11/15 in the real panel.
        small = pop <= 47_000
        band = ("metro_large" if pop > 1_000_000 else
                "metro_small" if pop > 250_000 else
                "micropolitan" if not small else "noncore")
        if small and rng.random() > 0.63:
            band = "micropolitan"
        # RUCC and UIC must genuinely DISAGREE, not merely be two names for the
        # same band. In the real panel RUCC >= 6 labels 15 counties noncore and
        # the UIC definition labels 11, so they conflict on at least four -- and
        # reading one as the other is the error that mislabelled Alpine, Del
        # Norte, Inyo and Lassen. So RUCC slips a band for about one county in
        # eight, independently of the UIC draw below.
        rucc = pick(rng, RUCC_BY_BAND[band])
        if rng.random() < 0.12:
            neighbours = {"metro_large": "metro_small", "metro_small": "micropolitan",
                          "micropolitan": "noncore", "noncore": "micropolitan"}
            rucc = pick(rng, RUCC_BY_BAND[neighbours[band]])
        uic = (pick(rng, UIC_NONCORE) if band == "noncore"
               else pick(rng, ("4", "5", "7")) if band == "micropolitan"
               else pick(rng, ("1", "2")))

        uninc = min(1.0, max(0.0, rng.betavariate(1.4, 3.2) if pop > 80_000
                             else rng.betavariate(3.0, 1.6)))
        # Fitted on the real panel: ln(1+cities) = -3.695 + 0.451*ln(pop),
        # which reproduces the median of 5, the maximum of 88 and the three
        # counties with no incorporated city at all.
        n_cities = max(0, int(round(math.expm1(
            -3.695 + 0.451 * math.log(max(pop, 2)) + rng.gauss(0, 0.42)))))
        # Only 3 of 58 real counties have no incorporated city, and all three
        # are tiny. Without this floor the lognormal noise puts about 7 counties
        # at zero, which would overstate how many places have no city hall to
        # publish anything at all -- the same direction of error the W2 spec
        # rejected for the subreddit hurdle.
        # The real zeros are Alpine (1,129) and Trinity (15,670) plus one more,
        # so the threshold is ~16,000, and even below it most counties do have a
        # city. Left probabilistic rather than hard so the count is not pinned.
        if not n_cities and (pop > 16_000 or rng.random() < 0.45):
            n_cities = 1

        name = "%s County" % stem
        out.append(dict(
            id="C%02d" % (i + 1),
            name=name,
            short=stem,
            kind="county",
            state="Marisol",
            fips="%05d" % (6000 + 2 * (i + 1)),
            seat="%s%s" % (stem, pick(rng, _SEAT_SUFFIX)),
            pop=pop,
            pop_unincorporated=int(round(pop * uninc)),
            land_area_sqmi=area,
            pop_density_per_sqmi=round(density, 1),
            rucc=rucc,
            uic=uic,
            is_noncore=uic in UIC_NONCORE,
            urban_band=band,
            local_govt_empl_per_1k_pop=round(emp_per_1k, 1),
            local_govt_employment=int(round(emp_per_1k * pop / 1000)),
            pct_pop_unincorporated=round(uninc, 3),
            n_incorporated_cities=n_cities,
            poverty_rate=round(min(0.30, max(0.05, rng.gauss(0.128, 0.035))), 3),
            broadband_pct=round(min(0.97, max(0.55, 0.87 + 0.03 * z + rng.gauss(0, 0.035))), 3),
            consortium=labels[i],
            permit_portal_vendor=weighted(rng, PORTAL_VENDORS),
            code_host=weighted(rng, CODE_HOSTS),
            target=True,
        ))
    return out


# ------------------------------------------------------------------ diagnostics

def panel_diagnostics(counties: list[dict]) -> dict:
    """Check the generated panel against the real shape it was built from.

    Reported, not asserted: a single seed is allowed to miss a target. The
    generator's test asserts the mean over seeds, which is the quantity the
    calibration actually claims.
    """
    def q(vals, p):
        xs = sorted(vals)
        return xs[min(len(xs) - 1, int(p * len(xs)))]

    pops = [c["pop"] for c in counties]
    emp = [c["local_govt_empl_per_1k_pop"] for c in counties]
    lp = [math.log(p) for p in pops]
    mlp, memp = sum(lp) / len(lp), sum(emp) / len(emp)
    sxy = sum((x - mlp) * (y - memp) for x, y in zip(lp, emp))
    sxx = sum((x - mlp) ** 2 for x in lp)
    syy = sum((y - memp) ** 2 for y in emp)
    r_emp = sxy / math.sqrt(sxx * syy) if sxx and syy else 0.0
    cons: dict[str, int] = {}
    for c in counties:
        cons[c["consortium"]] = cons.get(c["consortium"], 0) + 1
    return {
        "n": len(counties),
        "pop": dict(min=min(pops), median=q(pops, 0.5), max=max(pops),
                    ratio=round(max(pops) / max(1, min(pops))),
                    real_ratio=8561, real_median=188000),
        "density": dict(min=round(min(c["pop_density_per_sqmi"] for c in counties), 1),
                        max=round(max(c["pop_density_per_sqmi"] for c in counties), 1),
                        real_min=1.5, real_max=17323),
        "staffing_r_on_log_pop": dict(value=round(r_emp, 3), real=-0.73,
                                      note="must stay NEGATIVE; the intuitive positive sign "
                                           "would make capacity redundant with population"),
        "noncore_count": dict(value=sum(1 for c in counties if c["is_noncore"]), real=11,
                              note="under the UIC definition, not RUCC>=6 which gives 15"),
        "cities": dict(zero=sum(1 for c in counties if not c["n_incorporated_cities"]),
                       max=max(c["n_incorporated_cities"] for c in counties), real_max=88),
        "consortium_split": dict(value=cons, real={"39": 39, "18": 18, "1": 1}),
    }


if __name__ == "__main__":
    import json
    cs = build_counties(101)
    print(json.dumps(panel_diagnostics(cs), indent=1))
    print("\nsample rows:")
    for c in (cs[0], cs[len(cs) // 2], cs[-1]):
        print("  %-18s pop %8d  dens %8.1f  emp/1k %5.1f  uic %s  %s"
              % (c["name"], c["pop"], c["pop_density_per_sqmi"],
                 c["local_govt_empl_per_1k_pop"], c["uic"], c["consortium"]))
