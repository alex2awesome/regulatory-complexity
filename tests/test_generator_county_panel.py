"""The county panel and the availability coefficients reproduce their anchors.

Every assertion here is a calibration claim made in
`docs/2026-09-16-source-volume-register.md` or in `counties.py`'s own docstring.
The point is not that the generator runs; it is that the world it builds has the
shape our real retrievals measured, so that a method which works on it is not
working on a tamer problem than the real one.

Tolerances are on the **mean over seeds**, because a single seed is allowed to
miss. Where a sign matters more than a magnitude the test asserts the sign
strictly -- a staffing gradient that flipped positive would silently make
capacity redundant with population, which is the error the real panel caught.

No network, no paid calls, no benchmark truth.
"""
from __future__ import annotations

import math
import statistics as st

import pytest

from benchmark.synth.generator import capacity as cap
from benchmark.synth.generator.counties import (N_COUNTIES, build_counties,
                                                panel_diagnostics)

SEEDS = range(1, 41)


@pytest.fixture(scope="module")
def panels():
    return [build_counties(s) for s in SEEDS]


@pytest.fixture(scope="module")
def diags(panels):
    return [panel_diagnostics(p) for p in panels]


# ------------------------------------------------------------------ the panel

def test_panel_size_and_identity(panels):
    for p in panels:
        assert len(p) == N_COUNTIES == 58
        assert len({c["id"] for c in p}) == 58
        assert len({c["name"] for c in p}) == 58


def test_no_real_county_name_is_reused(panels):
    """The plan forbids attaching synthetic burdens to real county names."""
    real = {"Alameda", "Alpine", "Amador", "Butte", "Calaveras", "Colusa",
            "Contra Costa", "Del Norte", "El Dorado", "Fresno", "Glenn",
            "Humboldt", "Imperial", "Inyo", "Kern", "Kings", "Lake", "Lassen",
            "Los Angeles", "Madera", "Marin", "Mariposa", "Mendocino", "Merced",
            "Modoc", "Mono", "Monterey", "Napa", "Nevada", "Orange", "Placer",
            "Plumas", "Riverside", "Sacramento", "San Benito", "San Bernardino",
            "San Diego", "San Francisco", "San Joaquin", "San Luis Obispo",
            "San Mateo", "Santa Barbara", "Santa Clara", "Santa Cruz", "Shasta",
            "Sierra", "Siskiyou", "Solano", "Sonoma", "Stanislaus", "Sutter",
            "Tehama", "Trinity", "Tulare", "Tuolumne", "Ventura", "Yolo", "Yuba"}
    for p in panels:
        assert not ({c["short"] for c in p} & real)


def test_population_range_is_as_skewed_as_the_real_one(diags):
    """A tame population range would make every availability slope too easy."""
    ratios = [d["pop"]["ratio"] for d in diags]
    assert st.mean(ratios) > 2000, "real ratio is 8,561; a flat panel is a softer problem"
    medians = [d["pop"]["median"] for d in diags]
    assert 140_000 < st.mean(medians) < 260_000, "real median is 188,000"


def test_density_stays_inside_the_real_envelope(diags):
    """Real density runs 1.5 to 17,323; area is independent of population, so
    an unclamped draw manufactures counties emptier than any real one."""
    assert min(d["density"]["min"] for d in diags) >= 1.4
    assert max(d["density"]["max"] for d in diags) <= 18_000


def test_staffing_per_capita_runs_inverse_to_size(diags):
    """The single most counter-intuitive fact in the real panel.

    Asserted on every seed, not on the mean: a positive gradient in any world
    would make local-government staffing recoverable from population alone.
    """
    rs = [d["staffing_r_on_log_pop"]["value"] for d in diags]
    assert max(rs) < -0.4, "the gradient must be negative in every world"
    assert -0.85 < st.mean(rs) < -0.60, "real r is -0.73"


def test_noncore_count_matches_the_uic_definition(diags):
    """11, not 15. Defining noncore as RUCC >= 6 sweeps in the micropolitan
    band and mislabels four counties."""
    counts = [d["noncore_count"]["value"] for d in diags]
    assert 9.0 <= st.mean(counts) <= 13.5, "real count is 11 of 58"


def test_rurality_codes_are_not_collapsed(panels):
    """RUCC and UIC disagree in the real data; a panel where one determines the
    other would hide that a rurality claim depends on which code was used."""
    disagree = 0
    total = 0
    for p in panels:
        for c in p:
            total += 1
            rucc_noncore = c["rucc"] in ("6", "8", "9")
            if rucc_noncore != c["is_noncore"]:
                disagree += 1
    assert disagree > 0.02 * total, "the two codes must not agree everywhere"


def test_consortium_split_is_exact(diags):
    """39 / 18 / 1 is a known fact about the panel, so it is dealt, not drawn."""
    for d in diags:
        assert sorted(d["consortium_split"]["value"].values(), reverse=True) == [39, 18, 1]


def test_city_counts_match_the_fitted_relation(diags):
    """Only 3 of 58 real counties have no incorporated city."""
    zeros = [d["cities"]["zero"] for d in diags]
    assert 1.5 <= st.mean(zeros) <= 5.5, "real count is 3"


def test_panel_is_deterministic():
    assert build_counties(7) == build_counties(7)
    assert build_counties(7) != build_counties(8)


# ------------------------------------------------------ availability mechanisms

def _slope(xs, ys):
    mx, my = st.mean(xs), st.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx


N_PROGRAMMES = 8          # the count a county-sized world actually implements


def _realized(channels, panels, **kw):
    """(county-total slope, per-cell median, per-cell values) for one or more channels.

    The unit matters and cost a calibration pass to get right. The register
    measured a post ONCE per county, whichever venue carried it, so the quantity
    to reproduce is the UNION of the user channels over a county-programme cell.
    Drawing one volume per county and reusing it for every programme applied the
    county's whole budget to each process and realised a slope of 0.32 against
    the measured 0.75; calibrating `county_sub` alone put 22% of cells at zero
    against the measured 7%, by charging the counties with no forum of their own
    with having no evidence at all.
    """
    if isinstance(channels, str):
        channels = (channels,)
    xs, ys, vals = [], [], []
    for seed, p in zip(SEEDS, panels):
        for c in p:
            _u, vc = cap.county_effects(c, seed)
            total = 0
            for d in range(N_PROGRAMMES):
                n = sum(cap.post_volume(c, ch, seed, volume_effect=vc,
                                        programme="d%d" % d, **kw) for ch in channels)
                vals.append(n)
                total += n
            xs.append(math.log10(c["pop"]))
            ys.append(math.log10(total + 1))
    return _slope(xs, ys), st.median(vals), vals


USER_CHANNELS = ("county_sub", "statewide_sub")


def test_user_channel_union_reproduces_all_four_measured_moments(panels):
    """The register measured four things about reddit volume. All four, not just
    the slope, because a model can match a slope while getting the shape wrong."""
    slope, median, vals = _realized(USER_CHANNELS, panels)
    zero = sum(1 for v in vals if v == 0) / len(vals)
    assert abs(slope - 0.747) < 0.09, "county-total slope %.3f against 0.747" % slope
    assert 10 <= median <= 18, "per-cell median %s against the measured 13" % median
    assert 30 <= st.mean(vals) <= 50, "per-cell mean %.1f against 39.6" % st.mean(vals)
    assert 0.04 <= zero <= 0.12, "empty-cell share %.3f against the measured 0.07" % zero


def test_per_cell_counts_are_overdispersed_like_the_real_ones(panels):
    """Mean 39.6 against median 13 is a ratio of 3.0, which a pure Poisson
    cannot produce because its variance equals its mean."""
    _slope_, median, vals = _realized(USER_CHANNELS, panels)
    assert st.mean(vals) / max(1, median) > 2.0, "the count distribution must be skewed"
    assert st.variance(vals) > 5 * st.mean(vals), "variance must exceed the Poisson floor"


@pytest.mark.parametrize("channel,target_slope,target_median", [
    ("admin_forum", 1.157, 156),        # measured: CalGuns thread replies per county
    ("official_stats", 0.989, 5461),    # measured: APR project records per county
])
def test_single_channel_slopes_reproduce_their_anchors(channel, target_slope,
                                                       target_median, panels):
    """These two were measured per COUNTY, not per cell, so they are checked at
    that unit: one draw per county rather than a union over programmes."""
    xs, ys, vals = [], [], []
    for seed, p in zip(SEEDS, panels):
        for c in p:
            _u, vc = cap.county_effects(c, seed)
            n = cap.post_volume(c, channel, seed, volume_effect=vc)
            xs.append(math.log10(c["pop"]))
            ys.append(math.log10(n + 1))
            vals.append(n)
    slope, median = _slope(xs, ys), st.median(vals)
    assert abs(slope - target_slope) < 0.08, (
        "%s realized slope %.3f against the measured %.3f" % (channel, slope, target_slope))
    assert 0.5 * target_median <= median <= 2.0 * target_median, (
        "%s realized median %s against the measured %s" % (channel, median, target_median))


def test_the_three_slopes_are_actually_different(panels):
    """The register's central claim: one availability slope cannot fit all
    families. Reddit is sub-linear, administrative records linear, the
    administratively-created forum super-linear."""
    sub, _, _ = _realized(USER_CHANNELS, panels)
    stats, _, _ = _realized("official_stats", panels)
    forum, _, _ = _realized("admin_forum", panels)
    assert sub < 0.85 < stats < 1.05 < forum, (
        "expected sub-linear < linear < super-linear, got %.3f / %.3f / %.3f"
        % (sub, stats, forum))


def test_existence_and_volume_are_separate_mechanisms(panels):
    """The CalGuns control: every county got a thread in one 2010 batch, so
    existence carries no population signal while volume spans three orders of
    magnitude. A model with one parameter cannot do both."""
    for seed, p in zip(SEEDS, panels):
        assert all(cap.channel_exists(c, "admin_forum", seed) for c in p)
    _slope_, _median, vals = _realized("admin_forum", panels)
    assert min(vals) == 0, "some counties must have an existing channel and zero volume"
    assert max(vals) > 400, "volume must span orders of magnitude (real max 19,262)"


def test_county_sub_hurdle_matches_the_nine_real_counties(panels):
    """9 of 58 counties have no candidate subreddit. The spec rejected its own
    first draft for predicting 13.6, on the grounds that overstating the
    disappearing commons flatters our own hypothesis."""
    missing = [sum(1 for c in p if not cap.channel_exists(c, "county_sub", seed))
               for seed, p in zip(SEEDS, panels)]
    assert 6.0 <= st.mean(missing) <= 13.0, "expected ~9.7 of 58, got %.1f" % st.mean(missing)


def test_statewide_channel_rescues_the_hurdle_counties(panels):
    """Any-evidence existence is 57/58 even though county-sub existence is
    49/58, because the statewide subs always exist."""
    for seed, p in zip(SEEDS, panels):
        assert all(cap.channel_exists(c, "statewide_sub", seed) for c in p)
        assert all(cap.channel_exists(c, "grand_jury", seed) for c in p)


def test_delay_coefficient_defaults_to_its_measured_zero():
    """The W2 spec planted 0.55 for 'delay generates posts'. Measured at county
    level: +0.076 with a delta-R2 of 0.004, sign-flipped for timing-bearing
    posts. So the default is zero and the alternatives are named scenarios."""
    assert cap.v(cap.V_DELAY) == 0.0
    assert cap.V_DELAY.provenance == "measured_anchor"
    assert cap.scenario_coefs("evidence_constrained")["V_DELAY"] == 0.55
    assert cap.scenario_coefs("delay_suppresses")["V_DELAY"] < 0


def test_delay_actually_moves_volume_when_a_scenario_turns_it_on(panels):
    """A scenario knob that changed nothing would be decorative."""
    p = panels[0]
    ref = [cap.post_volume(c, "county_sub", 1, delay_z=1.5, volume_effect=0.0,
                           programme="d0") for c in p]
    alt = [cap.post_volume(c, "county_sub", 1, delay_z=1.5, volume_effect=0.0,
                           programme="d0", scenario="evidence_constrained") for c in p]
    assert sum(alt) > sum(ref)


def test_scenarios_are_declared_and_resolvable():
    for name in cap.SCENARIOS:
        assert cap.SCENARIOS[name]["note"], "every scenario states what it tests"
        cap.scenario_coefs(name)
    with pytest.raises(ValueError):
        cap.scenario_coefs("no_such_scenario")


# --------------------------------------------------------------- the funnel

def test_funnel_is_steep_and_family_specific():
    """Measured: the deepest stage is 3% for septic, 0% for wells, 12% for food.
    A shared rate could not produce a tenfold spread."""
    deep = {}
    for fam in cap.FUNNEL:
        counties = build_counties(3)
        reached = [cap.funnel_outcome(c, fam, 3) for c in counties]
        deep[fam] = sum(1 for r in reached if r == "operative_policy_established") / len(reached)
    assert deep["wells"] == 0.0, "wells is 0 of 58 and that is a finding, not a gap"
    assert deep["retail_food"] > deep["septic"], "food is the shallowest funnel"


def test_funnel_stages_are_conditional():
    """A county that fails an early stage must never reach a later one: 'we know
    a rule exists but do not hold its text' is the common real state."""
    order = ["not_located"] + list(cap.FUNNEL_STAGES)
    for fam in cap.FUNNEL:
        for seed in range(1, 12):
            for c in build_counties(seed):
                assert cap.funnel_outcome(c, fam, seed) in order


# ----------------------------------------------------------- provenance audit

def test_every_coefficient_carries_a_provenance_and_a_source():
    for name, c in cap.all_coefs():
        assert c.provenance in ("measured_anchor", "derived_with_assumptions",
                                "design_assumption"), name
        assert c.source, "%s has no source" % name


def test_most_coefficients_are_measured_not_assumed():
    rep = cap.provenance_report()
    measured = rep["by_provenance"].get("measured_anchor", 0)
    assert measured / rep["n_coefficients"] > 0.5, (
        "a generator whose coefficients are mostly assumptions cannot claim to be "
        "inspired by real observations")


def test_unsourced_coefficients_cannot_be_created():
    with pytest.raises(ValueError):
        cap.Coef(1.0, "because_it_looked_right", "nowhere")


# ----------------------------------------------------------- forum identity

def test_a_county_without_its_own_forum_still_gets_a_fetchable_venue():
    """The W2 spec flagged this and the first build reproduced it: a county with
    no subreddit was rendering URLs like `reddit.com/None/comments/...`. A dead
    link would teach an extractor that rural counties have broken pages, when
    what the measurement actually found is that they have DIFFERENT venues --
    57 of 58 counties yield posts while only 49 have a sub of their own.
    """
    from benchmark.synth.generator.world import build_world
    w = build_world("T", 101, {"world_model_version": 2, "n_counties": 24})
    panel = w["county_panel"]
    without = [c for c in panel if not c["forum_is_own"]]
    assert without, "some counties must have no forum of their own"
    for c in panel:
        assert c["forum_venue"], "%s has no venue" % c["short"]
        assert "None" not in str(c["forum_venue"])
        if c["forum_is_own"]:
            assert c["subreddit"] == c["forum_venue"]
        else:
            assert c["subreddit"] is None, "a county without its own sub carries None"
            assert c["forum_venue"].startswith("r/"), "it falls back to a statewide venue"


# ---------------------------------------------------- scenarios that bite

def _channel_slope(channel, scenario, seeds=12, nprog=3):
    out = []
    for seed in range(1, seeds + 1):
        counties = build_counties(seed)
        xs, ys = [], []
        for c in counties:
            _u, vc = cap.county_effects(c, seed)
            n = sum(cap.post_volume(c, channel, seed, scenario=scenario,
                                    volume_effect=vc, programme="d%d" % d)
                    for d in range(nprog))
            xs.append(math.log10(c["pop"]))
            ys.append(math.log10(n + 1))
        out.append(_slope(xs, ys))
    return st.mean(out)


def test_rural_commons_scenario_reverses_the_oversight_slope():
    """The scenario exists to test whether a conclusion about rural counties is
    an artifact of which channel we happened to sweep. For that it must make the
    oversight channel favour SMALL counties while the user channel still favours
    large ones -- otherwise a method could pass it without ever confronting the
    inversion the real grand-jury evidence shows.
    """
    ref = _channel_slope("grand_jury", "reference")
    alt = _channel_slope("grand_jury", "rural_commons_moves")
    assert ref > 0 > alt, (
        "grand-jury slope must reverse sign: %.3f -> %.3f" % (ref, alt))
    user_ref = _channel_slope("county_sub", "reference", nprog=8)
    user_alt = _channel_slope("county_sub", "rural_commons_moves", nprog=8)
    assert user_alt > 0.3, "the user channel must still favour large counties"
    assert abs(user_ref - user_alt) < 0.02, (
        "this scenario must move ONLY the oversight channel")


def test_flat_availability_scenario_collapses_the_family_differences():
    """The null the register argues against: one slope for every channel. A
    method that only works here is fitted to a world we measured to be false."""
    gj = _channel_slope("grand_jury", "flat_availability")
    stats = _channel_slope("official_stats", "flat_availability")
    ref_gj = _channel_slope("grand_jury", "reference")
    ref_stats = _channel_slope("official_stats", "reference")
    assert abs(gj - stats) < abs(ref_gj - ref_stats), (
        "under the flat scenario the families must differ LESS than under reference")


def test_speed_cache_does_not_leak_across_builds_in_one_process():
    """Codex review finding 4. The cache was keyed by county id alone, so a
    second build in the same process read the first build's speed factors and
    two scenarios produced identical process dictionaries. Separate CLI
    processes hid it; a multi-seed or scenario sweep would not have.
    """
    from benchmark.synth.generator import processes as pr
    from benchmark.synth.generator.world import build_world

    ref = build_world("SC_REF", 101, {"world_model_version": 2, "n_counties": 4,
                                      "speed_scenario": "reference"})
    inv = build_world("SC_INV", 101, {"world_model_version": 2, "n_counties": 4,
                                      "speed_scenario": "speed_inverse"})
    for w in (ref, inv):
        for c in w["county_panel"]:
            pr._SPEED_CACHE[pr._speed_key(w, c["id"])] = cap.speed_factor(
                c, w["seed"], scenario=w["knobs"]["speed_scenario"])
    for c_ref, c_inv in zip(ref["county_panel"], inv["county_panel"]):
        a = pr._SPEED_CACHE[pr._speed_key(ref, c_ref["id"])]
        b = pr._SPEED_CACHE[pr._speed_key(inv, c_inv["id"])]
        assert a != b, "the two scenarios must not share a cached speed factor"


def test_speed_key_separates_world_seed_and_scenario():
    from benchmark.synth.generator import processes as pr
    base = {"world": "W", "seed": 1, "knobs": {"speed_scenario": "reference"}}
    keys = {
        pr._speed_key(base, "C01"),
        pr._speed_key(dict(base, world="X"), "C01"),
        pr._speed_key(dict(base, seed=2), "C01"),
        pr._speed_key(dict(base, knobs={"speed_scenario": "speed_null"}), "C01"),
        pr._speed_key(base, "C02"),
    }
    assert len(keys) == 5, "every dimension must widen the key"


def test_delay_scenarios_change_the_CORPUS_not_just_the_function():
    """Codex review finding 2. `post_volume` accepted `delay_z` but nothing in
    the build path passed it, so every delay scenario produced an identical
    volume vector and the knob was decorative.

    The earlier test passed because it supplied `delay_z` by hand -- it checked
    the function, not the wiring. This one drives an actual build, which is the
    only thing that can catch an unconnected parameter. Worth remembering for
    the other scenario knobs.
    """
    from benchmark.synth.generator.local_rules import build_local_rules
    from benchmark.synth.generator.processes import build_processes
    from benchmark.synth.generator.simulate import simulate_all
    from benchmark.synth.generator.statutes import build_statutes
    from benchmark.synth.generator.visibility import select_personas
    from benchmark.synth.generator.world import build_world

    def corpus_posters(scenario):
        knobs = {"world_model_version": 2, "outcome_model_version": 2,
                 "p_self_select": 0.97, "n_counties": 5, "n_applicants": 120,
                 "availability_scenario": scenario}
        w = build_world("DELAY", 101, knobs)
        st = build_statutes(w)
        rules = build_local_rules(w, st)
        procs = build_processes(w, st, rules)
        logs, summaries = simulate_all(w, procs, rules)
        return sum(len(select_personas(w, procs[m], logs[m], summaries[m]))
                   for m in procs)

    ref = corpus_posters("reference")
    more = corpus_posters("evidence_constrained")   # V_DELAY = +0.55
    less = corpus_posters("delay_suppresses")       # V_DELAY = -0.40
    assert ref and more and less, "every scenario must produce some posters"
    assert more > ref > less, (
        "delay must move corpus volume: got %d / %d / %d" % (more, ref, less))
