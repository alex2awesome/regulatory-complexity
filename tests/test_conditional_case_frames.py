"""Source-free mechanics for the guarded finite reported-case frame."""
import copy

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.conditional_case_frames import canonical_sha256
from pipeline.procbench.run_visit_hierarchy import main, preflight_report
from procbench_fixtures import data_fixture
from test_cohort_histograms import histogram_fixture
from test_cohort_quantiles import cohort_fixture


def frame_config(**changes):
    values=dict(population_size=16, modeled_channels=("elapsed",),
        agency_sd=0., task_sd=0., operation_sd=0., common_case_sd=0.,
        source_sd=0., selection_sd=0.)
    values.update(changes)
    return Config(**values)


def frame_data():
    cases=["case-a", "case-b"]
    target="Reported approval-to-provider-completion elapsed phase"
    rows=[dict(registry_label_id=f"rank:{i}", status="excluded", case_id=None,
               reason="No reviewed clock with both phase endpoints") for i in range(1,49)]
    rows[6]=dict(registry_label_id="rank:7", status="included", case_id=cases[0],
                 reason="One reviewed completed reported phase")
    rows[30]=dict(registry_label_id="rank:31", status="included", case_id=cases[1],
                  reason="One reviewed completed reported phase")
    ledger=dict(schema_version="conditional-case-frame-ledger/1", rows=rows)
    frame=dict(schema_version="declared-conditional-case-frame/1", id="fixed-48",
        target=target,
        source_family="one-forum-thread", eligibility="Frozen registry labels with both reviewed phase endpoints",
        generalization_limit="No inference beyond eligible completed reports in this fixed registry",
        registry_label_denominator=48, included_case_ids=cases, ledger=ledger,
        ledger_sha256=canonical_sha256(ledger))
    operation=dict(id="reported_phase", actor_id=None, actor_role="unknown",
        task_type="reported_phase", markers=[], payer_work=False, agency_work=False)
    observations=[dict(id=f"clock-{i}", case_id=case, source_family="one-forum-thread",
        sampling="census_within_declared_conditional_frame", statistic="individual",
        lower=10.+i, upper=12.+i,
        operators=[dict(basis="single_visit_cycle", activity_ids=["reported_phase"])],
        operator_weights=[1.], provenance=dict(clock_id=f"clock-{i}",
            evidence_cell_ids=[f"synthetic-source-cell-{i}-start", f"synthetic-source-cell-{i}-end"],
            date_resolution_rule="Source-free test interval supplied directly"))
        for i,case in enumerate(cases)]
    program=dict(id="reported-program", conditional_frame_id="fixed-48",
        inventory_granularity="aggregate_phases",
        clock_estimand=target,
        routes=[dict(id="one", prior_weight=1., operations=[operation],
                     blocks=[dict(id="reported_phase", operations=["reported_phase"])])],
        observations=observations, rate_observations=[])
    return dict(elapsed_time_unit="calendar_days", conditional_case_frames=[frame], programs=[program])


def test_hash_bound_fixed_registry_and_reports_propagate_without_population_overclaim():
    model=VisitHierarchy(frame_data(),frame_config())
    frame=model.conditional_case_frames["reported-program"]
    assert frame["registry_label_denominator"]==48
    assert frame["included_case_count"]==2 and frame["excluded_registry_label_count"]==46
    assert "does not prove" in frame["binding_qualification"]
    preflight=preflight_report(model)
    assert preflight["conditional_frame_cases"]==2
    assert preflight["conditional_case_frames"]==model.conditional_case_frames
    source=preflight["source_support"]
    source_row=source["source_families"]["one-forum-thread"]
    assert source_row["duration_candidate_unselected_case_ids"]==[]
    assert len(source_row["duration_candidate_conditional_frame_case_ids"])==2
    assert source_row["duration_offset_fixed_zero"]
    assert source_row["offset_prior_sd_log"]==0.
    assert not source_row["duration_offset_effect_enabled"]
    assert "report-frame convention" in source["conditional_frame_policy"]


def test_conditional_sampling_uses_unchanged_ordinary_qmc_likelihood_not_an_alias():
    conditional=frame_data()
    legacy=copy.deepcopy(conditional)
    legacy.pop("conditional_case_frames")
    legacy["programs"][0].pop("conditional_frame_id")
    for row in legacy["programs"][0]["observations"]:
        row["sampling"]="unselected"
    first=VisitHierarchy(conditional,frame_config())
    second=VisitHierarchy(legacy,frame_config())
    assert first.layout.size==second.layout.size
    z=np.random.default_rng(14).normal(size=first.layout.size)
    assert first.log_likelihood(z,[0])==second.log_likelihood(z,[0])
    assert "conditional_case_frames" not in second.source_support_report()
    assert "conditional_frame_cases" not in preflight_report(second)


def test_posterior_program_keeps_frame_target_and_fixed_zero_qualification():
    model=VisitHierarchy(frame_data(),frame_config())
    states=np.random.default_rng(9).normal(size=(2,8,model.layout.size))
    routes=np.zeros((2,8,1),dtype=int)
    likelihood=np.array([[model.log_likelihood(z,[0]) for z in chain] for chain in states])
    report=model.report(states,routes,likelihood)
    program=report["programs"]["reported-program"]
    assert program["conditional_case_frame"]["ledger_sha256"]==canonical_sha256(
        frame_data()["conditional_case_frames"][0]["ledger"])
    assert program["ascertainment"]["conditional_frame_case_count"]==2
    assert program["ascertainment"]["unselected_case_count"]==0
    assert "not unselected" in program["ascertainment"]["qualification"]
    support=report["source_support"]["source_families"]["one-forum-thread"]
    assert support["offsets"]["elapsed"]["posterior_log_offset"]["median"]==0.
    assert support["offsets"]["elapsed"]["marginal_variance_contraction"] is None


def test_complete_registry_may_have_zero_exclusions_without_inventing_one():
    data=frame_data(); frame=data["conditional_case_frames"][0]
    frame["ledger"]["rows"]=[row for row in frame["ledger"]["rows"] if row["status"]=="included"]
    frame["registry_label_denominator"]=2
    frame["ledger_sha256"]=canonical_sha256(frame["ledger"])
    summary=VisitHierarchy(data,frame_config()).conditional_case_frames["reported-program"]
    assert summary["excluded_registry_label_count"]==0


def test_runner_cli_can_preflight_the_guarded_zero_effect_configuration(tmp_path,capsys):
    import json
    path=tmp_path/"data.json"; path.write_text(json.dumps(frame_data()))
    out=tmp_path/"preflight"
    main(["--data",str(path),"--out",str(out),"--preflight",
          "--observed-channels-only","--population-size","16",
          "--agency-sd","0","--task-sd","0","--operation-sd","0",
          "--source-sd","0","--common-case-sd","0"])
    report=json.loads((out/"preflight.json").read_text())
    manifest=json.loads((out/"manifest.json").read_text())
    assert report["conditional_frame_cases"]==2 and not report["sampling_performed"]
    assert manifest["provenance"]["config"]["source_sd"]==0.
    assert manifest["provenance"]["config"]["common_case_sd"]==0.
    capsys.readouterr()


@pytest.mark.parametrize("change,match", [
    ("hash", "digest does not match"),
    ("missing_registry_row", "every denominator"),
    ("case_mismatch", "exactly equal included_case_ids"),
    ("duplicate_case_row", "exactly equal included_case_ids"),
    ("unselected_alias", "explicit sampling kind"),
    ("two_rows_one_case", "exactly one observation per included case"),
    ("cohort", "forbids rates and cohort"),
    ("path", "bounded fields"),
    ("repeat", "bounded fields"),
    ("markers", "no decision markers"),
    ("target", "exactly equal"),
    ("labor", "implied labor"),
    ("source_hierarchy", "forbids source hierarchy"),
])
def test_frame_contract_fails_closed(change,match):
    data=frame_data(); program=data["programs"][0]; frame=data["conditional_case_frames"][0]
    if change=="hash": frame["ledger"]["rows"][0]["reason"]="tampered"
    elif change=="missing_registry_row": frame["ledger"]["rows"].pop(); frame["ledger_sha256"]=canonical_sha256(frame["ledger"])
    elif change=="case_mismatch": frame["included_case_ids"][0]="other"
    elif change=="duplicate_case_row":
        frame["ledger"]["rows"][30]["case_id"]="case-a"; frame["ledger_sha256"]=canonical_sha256(frame["ledger"])
    elif change=="unselected_alias": program["observations"][0]["sampling"]="unselected"
    elif change=="two_rows_one_case": program["observations"].append(copy.deepcopy(program["observations"][0]))
    elif change=="cohort": program["quantile_cohorts"]=[{}]
    elif change=="path": program["routes"][0]["paths"]=[]
    elif change=="repeat": program["routes"][0]["blocks"][0]["repeat_key"]="again"
    elif change=="markers": program["routes"][0]["operations"][0]["markers"]=["decision"]
    elif change=="target": program["clock_estimand"]="Contradictory clock"
    elif change=="labor": program["routes"][0]["operations"][0]["agency_work"]=True
    else: data["source_offset_hierarchy"]={}
    with pytest.raises(ValueError,match=match):
        VisitHierarchy(data,frame_config())


@pytest.mark.parametrize("level,field,value", [
    ("program", "extra", 1),
    ("route", "extra", 1),
    ("operation", "fee", 10.),
    ("operation", "extra", 1),
    ("block", "extra", 1),
    ("observation", "sample_size", 48),
    ("observation", "cohort_id", "cohort"),
    ("observation", "report_intervals", [[10., 11.], [12., 13.]]),
    ("observation", "extra", 1),
    ("operator", "visits", "first"),
    ("operator", "extra", 1),
    ("provenance", "extra", 1),
])
def test_conditional_nested_contract_rejects_every_undeclared_field(level,field,value):
    data=frame_data(); program=data["programs"][0]
    target={
        "program": program,
        "route": program["routes"][0],
        "operation": program["routes"][0]["operations"][0],
        "block": program["routes"][0]["blocks"][0],
        "observation": program["observations"][0],
        "operator": program["observations"][0]["operators"][0],
        "provenance": program["observations"][0]["provenance"],
    }[level]
    target[field]=value
    with pytest.raises(ValueError,match="bounded fields"):
        VisitHierarchy(data,frame_config())


@pytest.mark.parametrize("lower,upper", [
    (-1., 1.), (True, 2.), (1., True), (0., None), (1., None),
    (1., float("inf")), (1., float("nan")), (2., 2.), (3., 2.),
])
def test_conditional_completed_history_requires_finite_nonempty_interval(lower,upper):
    data=frame_data(); observation=data["programs"][0]["observations"][0]
    observation["lower"],observation["upper"]=lower,upper
    with pytest.raises(ValueError,match="finite nonempty elapsed interval"):
        VisitHierarchy(data,frame_config())


def test_same_day_completed_history_may_use_zero_lower_bound():
    data=frame_data(); observation=data["programs"][0]["observations"][0]
    observation["lower"],observation["upper"]=0.,1.
    VisitHierarchy(data,frame_config())


def censored_frame_data():
    data = frame_data()
    frame = data['conditional_case_frames'][0]
    frame['schema_version'] = 'declared-conditional-case-frame/2'
    frame['coarsening_assumption'] = dict(
        kind='assumed_ignorable_within_report_frame',
        rationale='Source-free fixture: fixed inspection times independent of case duration.',
        sensitivity_plan='Compare completed-only and mixed reported frames; no population claim.',
        informative_posting_unmodeled=True)
    first, second = data['programs'][0]['observations']
    first['observation_kind'] = 'completed_interval'
    second.update(observation_kind='pending_right_censored', lower=20., upper=None)
    return data


def terminal_neutral_frame_data():
    data = censored_frame_data()
    data['conditional_case_frames'][0]['schema_version'] = 'declared-conditional-case-frame/3'
    data['programs'][0]['observations'][1]['observation_kind'] = 'terminal_neutral_lower_bound'
    return data


def test_v3_terminal_neutral_lower_bound_uses_survival_factor_without_status_claim():
    neutral, pending = terminal_neutral_frame_data(), censored_frame_data()
    neutral_model, pending_model = VisitHierarchy(neutral, frame_config()), VisitHierarchy(pending, frame_config())
    z = np.zeros(neutral_model.layout.size)
    assert neutral_model.log_likelihood(z, [0]) == pending_model.log_likelihood(z, [0])
    frame = neutral_model.conditional_case_frames['reported-program']
    assert frame['observation_kind_counts']['terminal_neutral_lower_bound'] == 1
    assert 'does not assert' in frame['distribution_qualification']


def test_v2_pending_report_is_a_survival_factor_and_not_completed_time():
    from scipy.stats import t
    from pipeline.procbench.bayes_trace_hierarchy import duration_log_probability
    data = censored_frame_data()
    model = VisitHierarchy(data, frame_config(contamination=0.))
    z = np.zeros(model.layout.size)
    # V6's existing log-report kernel is Student-t with four degrees of
    # freedom, not Gaussian. Censoring must retain that exact target.
    expected = t.logsf((np.log(20.) - np.log(7.))/.25, df=4.)
    parts = model.log_likelihood(z, [0], parts=True)
    assert parts['reported-program:clock-1'] == pytest.approx(expected)
    assert float(duration_log_probability(20., None, 7., contamination=0.)) == pytest.approx(expected)
    assert model.log_likelihood(z, [0]) == pytest.approx(model.log_likelihood_reference(z, [0]))
    summary = model.conditional_case_frames['reported-program']
    assert summary['observation_kind_counts'] == dict(completed_interval=1, completed_lower_bound=0, pending_right_censored=1)
    assert not summary['all_observations_lower_bounds']


def test_v2_finite_only_contract_leaves_the_v1_target_exactly_unchanged():
    before = frame_data()
    after = censored_frame_data()
    for new, old in zip(after['programs'][0]['observations'], before['programs'][0]['observations']):
        new.update(lower=old['lower'], upper=old['upper'], observation_kind='completed_interval')
    old_model, new_model = VisitHierarchy(before, frame_config()), VisitHierarchy(after, frame_config())
    assert old_model.layout.size == new_model.layout.size
    for z in np.random.default_rng(91).normal(size=(5, old_model.layout.size)):
        assert old_model.log_likelihood(z, [0]) == new_model.log_likelihood(z, [0])


@pytest.mark.parametrize('kind,lower,upper', [
    ('terminal_neutral_lower_bound', 3., None),
    ('pending_right_censored', 0., None), ('pending_right_censored', 3., 5.),
    ('pending_right_censored', 3., float('inf')), ('pending_right_censored', True, None),
    ('pending_right_censored', float('nan'), None), ('completed_interval', 3., None),
    ('completed_lower_bound', -1., None), ('completed_lower_bound', 3., 5.),
    ('unspecified', 3., None), ([], 3., None),
])
def test_v2_requires_kind_and_bounds_to_agree(kind, lower, upper):
    data = censored_frame_data()
    data['programs'][0]['observations'][1].update(observation_kind=kind, lower=lower, upper=upper)
    with pytest.raises(ValueError):
        VisitHierarchy(data, frame_config())


@pytest.mark.parametrize('change', ['missing_assumption', 'missing_kind', 'undisclosed_selection', 'empty_rationale'])
def test_v2_does_not_silently_treat_forum_censoring_as_ignorable(change):
    data = censored_frame_data()
    frame = data['conditional_case_frames'][0]
    if change == 'missing_assumption': del frame['coarsening_assumption']
    elif change == 'missing_kind': del data['programs'][0]['observations'][1]['observation_kind']
    elif change == 'undisclosed_selection': frame['coarsening_assumption']['informative_posting_unmodeled'] = False
    else: frame['coarsening_assumption']['rationale'] = ''
    with pytest.raises(ValueError):
        VisitHierarchy(data, frame_config())


def test_v2_all_lower_bounds_are_not_a_typical_duration_headline():
    data = censored_frame_data()
    data['programs'][0]['observations'][0].update(observation_kind='completed_lower_bound', upper=None)
    model = VisitHierarchy(data, frame_config())
    states = np.random.default_rng(92).normal(size=(2, 8, model.layout.size))
    routes = np.zeros((2, 8, 1), dtype=int)
    likelihood = np.array([[model.log_likelihood(z, [0]) for z in chain] for chain in states])
    program = model.report(states, routes, likelihood)['programs']['reported-program']
    assert not program['conditional_duration_headline_eligible']
    assert program['conditional_case_frame']['all_observations_lower_bounds']
    assert 'pending' in program['ascertainment']['qualification']
    assert program['ascertainment']['unselected_case_count'] == 0


@pytest.mark.parametrize('lower,upper', [(0.,None),(3.,4.),(True,None),(3.,float('inf'))])
def test_v3_terminal_neutral_requires_positive_finite_lower_and_null_upper(lower, upper):
    data = terminal_neutral_frame_data()
    data['programs'][0]['observations'][1].update(lower=lower, upper=upper)
    with pytest.raises(ValueError, match='Lower-bound observation kinds'):
        VisitHierarchy(data, frame_config())


def test_v3_report_does_not_call_terminal_neutral_row_completed_or_pending():
    model = VisitHierarchy(terminal_neutral_frame_data(), frame_config())
    frame = model.conditional_case_frames['reported-program']
    assert frame['observation_kind_counts'] == dict(completed_interval=1,
        completed_lower_bound=0, pending_right_censored=0, terminal_neutral_lower_bound=1)


def test_conditional_provenance_must_bind_clock_and_evidence_cells():
    data=frame_data()
    data["programs"][0]["observations"][0]["provenance"]["clock_id"]="other"
    with pytest.raises(ValueError,match="bind its clock"):
        VisitHierarchy(data,frame_config())


@pytest.mark.parametrize("field,value", [
    ("agency_sd", 1.), ("task_sd", .5), ("operation_sd", .5),
    ("source_sd", .25), ("selection_sd", .4), ("common_case_sd", .25),
    ("population_integration", "analytic_single_phase"),
    ("modeled_channels", ("elapsed","payer_hours")),
])
def test_frame_refuses_unidentified_or_out_of_scope_model_components(field,value):
    with pytest.raises(ValueError,match=field):
        VisitHierarchy(frame_data(),frame_config(**{field:value}))


@pytest.mark.parametrize("cohort_kind,prefix", [
    ("quantile", "quantile_cohort:dashboard"),
    ("histogram", "histogram_cohort:published_histogram"),
])
def test_generated_cohort_factor_keys_cannot_collide_with_ordinary_rows(cohort_kind,prefix):
    data=data_fixture(); program=data["programs"][0]
    program["observations"][0]["id"]=prefix
    if cohort_kind=="quantile": program["quantile_cohorts"]=[cohort_fixture()]
    else: program["histogram_cohorts"]=[histogram_fixture()]
    with pytest.raises(ValueError,match="Likelihood factor key collision"):
        VisitHierarchy(data,Config(population_size=16))


def test_generated_rate_and_selection_factor_keys_cannot_collide_with_rows():
    rate_data=data_fixture(); program=rate_data["programs"][0]
    program["observations"][0]["id"]="cohort:0"
    program["rate_observations"]=[dict(repeat_key="corrections",event="any_correction_per_case",
        successes=2,trials=5,cohort_scope="completed_cases_for_repeat_block",independent_cohort=True)]
    with pytest.raises(ValueError,match="Likelihood factor key collision"):
        VisitHierarchy(rate_data,Config(population_size=16))
    selected=data_fixture(); program=selected["programs"][0]
    program["observations"][0]["id"]="selection:c"
    for row in program["observations"]: row["sampling"]="delay_selected"
    with pytest.raises(ValueError,match="Likelihood factor key collision"):
        VisitHierarchy(selected,Config(population_size=16,selection_sd=.5))


def test_collision_free_factors_all_contribute_and_parts_sum_to_full_likelihood():
    data=data_fixture(); program=data["programs"][0]
    program["quantile_cohorts"]=[cohort_fixture()]
    model=VisitHierarchy(data,Config(population_size=16,cohort_quadrature_size=16))
    z=np.zeros(model.layout.size)
    parts=model.log_likelihood(z,[0],parts=True)
    assert "J__P:total" in parts and "J__P:quantile_cohort:dashboard" in parts
    assert len(parts)==len(program["observations"])+1
    assert model.log_likelihood(z,[0])==pytest.approx(sum(parts.values()))


def test_likelihood_factor_keys_are_globally_unique_across_program_delimiters():
    data=data_fixture()
    first=data["programs"][0]
    first["id"]="a"
    first["observations"]=[copy.deepcopy(first["observations"][0])]
    first["observations"][0]["id"]="b:c"
    second=copy.deepcopy(first)
    second["id"]="a:b"
    second["observations"][0]["id"]="c"
    data["programs"]=[first,second]
    with pytest.raises(ValueError,match="Likelihood factor key collision"):
        VisitHierarchy(data,Config(population_size=16))


def _mixed_path_and_plain_routes():
    data=data_fixture(); program=data["programs"][0]
    plain=program["routes"][0]
    plain["prior_weight"]=1.
    path=copy.deepcopy(plain)
    path["id"]="path-alternative"
    blocks=path.pop("blocks")
    path["paths"]=[dict(id="complete", probability_weight=1., blocks=blocks)]
    program["routes"].append(path)
    return data


def test_mixed_route_guard_checks_plain_emission_against_always_on_cohort():
    data=_mixed_path_and_plain_routes(); program=data["programs"][0]
    program["observations"][0]["id"]="quantile_cohort:dashboard"
    program["quantile_cohorts"]=[cohort_fixture()]
    with pytest.raises(ValueError,match="Likelihood factor key collision"):
        VisitHierarchy(data,Config(population_size=16))


def test_mixed_route_guard_allows_same_key_from_mutually_exclusive_modes():
    data=_mixed_path_and_plain_routes(); program=data["programs"][0]
    program["observations"][0]["id"]="case:c"
    model=VisitHierarchy(data,Config(population_size=16))
    z=np.zeros(model.layout.size)
    path_parts=model.log_likelihood(z,[1],parts=True)
    plain_parts=model.log_likelihood(z,[0],parts=True)
    assert "J__P:case:c" in path_parts and "J__P:case:c" in plain_parts
    assert model.log_likelihood(z,[1])==pytest.approx(sum(path_parts.values()))
    assert model.log_likelihood(z,[0])==pytest.approx(sum(plain_parts.values()))


def test_distinct_cross_program_factors_are_all_retained_in_full_likelihood():
    data=data_fixture()
    first=data["programs"][0]
    first["id"]="first"
    first["observations"]=[copy.deepcopy(first["observations"][0])]
    second=copy.deepcopy(first)
    second["id"]="second"
    second["observations"][0]["id"]="other-clock"
    data["programs"]=[first,second]
    model=VisitHierarchy(data,Config(population_size=16))
    z=np.zeros(model.layout.size)
    parts=model.log_likelihood(z,[0,0],parts=True)
    assert set(parts)=={"first:total", "second:other-clock"}
    assert model.log_likelihood(z,[0,0])==pytest.approx(sum(parts.values()))
