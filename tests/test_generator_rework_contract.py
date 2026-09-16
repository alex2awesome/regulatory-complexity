import json
from pathlib import Path
import random

import jsonschema
import pytest

from benchmark.synth.generator.simulate import observed_rework_summary
from benchmark.synth.generator.visibility import reveals_for


def record(arrived, *dates):
    return dict(arrived=arrived,rework_events=[dict(triggered_at=date) for date in dates])


def reveal(kind,summary,probability=.3):
    activity=dict(id='review',name='review',visibility='applicant_facing',element_ref=None,
        local_name=None,artifacts_out=[],timing=dict(median_days=5),fee=None,
        rework=dict(p_trigger=probability,back_to='file'))
    process=dict(stat_id='S01',activities=[activity],prior_version=None,terminal_artifact='letter')
    return reveals_for(kind,{'knobs':{}},process,{}, {'S01':{}},summary,random.Random(4),False,False)[0]


def summary():
    return dict(elapsed_days=dict(median=20,n=2),n_completed=2,n_applicants=4,
        outcomes=dict(approved=2,in_progress=2),share_with_rework=1.,per_activity_median_days={'review':5})


def test_observed_cohort_excludes_future_arrivals_and_corrections():
    rows=[record('2026-01-01','2026-01-03','2026-03-01'),
          record('2026-01-02','2026-03-01'),record('2026-01-03'),
          record('2026-04-01','2026-04-05')]
    result=observed_rework_summary(rows,'2026-01-31')
    assert result['n_cases']==3
    assert result['cases_with_observed_rework']==1
    assert result['observed_correction_rounds']==1
    assert result['share_with_observed_rework']==1/3
    assert result['stage_scope']=='all_modeled_stages_including_after_decision'


def test_missing_observed_cohort_is_not_zero_risk_or_lifetime_rework():
    assert observed_rework_summary([],'2026-01-31')['share_with_observed_rework'] is None
    with pytest.raises(ValueError,match='timestamped'):
        observed_rework_summary([dict(arrived='2026-01-01',total_rework_rounds=2)],'2026-01-31')


@pytest.mark.parametrize('probability,phrase',[(0.,'about 0 percent'),(.03,'about 3 percent'),(.3,'about 30 percent')])
def test_faq_preserves_per_visit_probability_without_inventing_a_case_cohort(probability,phrase):
    row=next(r for r in reveal('faq',summary(),probability) if r['field']=='rework')
    assert phrase in row['value']
    assert 'eligible visits to this checkpoint' in row['value']
    assert 'not the share of applications' in row['value']
    assert row['count_observation']['statistic']=='planning_probability'
    assert 'sample_size' not in row['count_observation']


def test_dashboard_reports_actual_observed_rework_counts_and_date():
    s=summary()
    s['observed_rework']=observed_rework_summary([
        record('2026-01-01','2026-01-04'),record('2026-01-01','2026-04-01'),
        record('2026-01-01'),record('2026-01-01')],'2026-01-31')
    row=next(r for r in reveal('official_stats',s) if r['field']=='rework')
    assert '1 of 4 received applications (about 25 percent)' in row['value']
    assert 'as of 2026-01-31' in row['value']
    assert 'not an eventual-risk estimate' in row['value']
    assert row['count_observation']['sample_size']==4
    assert row['count_observation']['numerator']==1
    schema=json.loads((Path(__file__).resolve().parents[1]/'benchmark/synth/schemas/artifact_spec.schema.json').read_text())
    jsonschema.validate(row['count_observation'],schema['properties']['reveals']['items']['properties']['count_observation'])


def test_old_or_empty_summaries_do_not_fabricate_an_observed_fraction():
    s=summary()
    assert not any(r['field']=='rework' for r in reveal('official_stats',s))
    s['observed_rework']=observed_rework_summary([],'2026-01-31')
    assert not any(r['field']=='rework' for r in reveal('official_stats',s))
