"""Counterexamples for E0 validity and corrected reporting; all offline."""
import copy
import csv
from pathlib import Path

import pytest

from benchmark.rulegap.admissibility import catalog, audit_ratings, write_packet, behavioral_audit
from benchmark.rulegap.spec import Spec, load_spec, key
from benchmark.rulegap.compile import classify
from benchmark.rulegap.metrics import _certificates, measure
from benchmark.rulegap.render import render
from benchmark.rulegap.cli import main
from benchmark.rulegap.cases import sample_panel
from benchmark.rulegap.reanalyse import sign_flip

PCT = Path('benchmark/rulegap/specs/percentile_v1.yaml')
PROC = Path('benchmark/rulegap/specs/procurement_v1.yaml')
REAL = Path('benchmark/rulegap/real/percentile/spec.yaml')


def votes(cat, decisions):
    return [dict(catalog_digest=cat['catalog_digest'], candidate_id=cat['candidates'][0]['candidate_id'],
                 rater_id=f'person_{i}', rater_kind='human', decision=d, rationale='Test fixture only.')
            for i,d in enumerate(decisions)]


def test_sources_and_products_do_not_validate_interpretations():
    proc=load_spec(PROC); cat=catalog(proc,'open')
    assert len(proc.admissible('open')) == 768 and len(cat['candidates']) == 400
    assert not any(c['sourced'] for c in cat['candidates'])
    assert audit_ratings(cat,[])['coverage'] == 0
    if not (REAL.parent / 'sources' / 'raw').exists():
        pytest.skip('percentile source pages not fetched (excluded from the share export)')
    real=load_spec(REAL,reading_scope='sourced')
    assert len(real.admissible('open')) == 10
    assert all(a['SAMPLES']=='all' for a in real.admissible('open'))
    with pytest.raises(ValueError,match='requires independent'):
        load_spec(REAL,reading_scope='validated').admissible('open')


def test_whole_reading_vote_policy_and_integrity():
    cat=catalog(load_spec(PCT),'open')
    assert not audit_ratings(cat,votes(cat,['defensible','defensible']))['accepted']
    result=audit_ratings(cat,votes(cat,['defensible','defensible','indefensible']))
    assert len(result['accepted'])==1 and result['status']=='pending'
    assert not audit_ratings(cat,votes(cat,['defensible','defensible','abstain']))['accepted']
    for field,value in [('rater_kind','llm'),('catalog_digest','stale'),('candidate_id','unknown')]:
        rows=votes(cat,['defensible']); rows[0][field]=value
        with pytest.raises(ValueError): audit_ratings(cat,rows)
    rows=votes(cat,['defensible'])
    with pytest.raises(ValueError,match='duplicate'):audit_ratings(cat,rows+rows)


def test_compatibility_applies_to_complete_readings():
    raw=copy.deepcopy(load_spec(PCT).raw)
    raw['incompatible_combinations']=[dict(forbid=dict(SAMPLES='last_window',EXCEEDS='at_least'),
                                          reason='Artificial incompatibility for the regression test.')]
    s=Spec(raw)
    assert len(s.admissible('open'))==45
    assert all(not(a['SAMPLES']=='last_window' and a['EXCEEDS']=='at_least') for a in s.admissible('open'))


def test_packets_hide_target_and_reject_changed_text(tmp_path):
    s=load_spec(PCT); cat=write_packet(s,'open',tmp_path/'packet')
    text=(tmp_path/'packet/rater_packet.md').read_text()
    assert 'quarterly bonus' not in text and 'true 90th' not in text
    raw=copy.deepcopy(s.raw); raw['background']+=' Additional background.'
    changed=catalog(Spec(raw),'open')
    with pytest.raises(ValueError,match='stale'):
        audit_ratings(changed,votes(cat,['defensible']))


def test_invalid_and_inconsistent_reports_cannot_be_compliant():
    s=load_spec(PCT); sit=s.domain['build_case']([175,225,231,235,245,263,632],450)
    for number,verdict in [(99999,'passing'),(410.6,'nonsense'),(None,'passing'),('oops','passing')]:
        c=classify(s,'fully_settled',sit,dict(kind='report',p90_ms=number,verdict=verdict))
        assert c['i_star']=='illegal' and c['cell']!='compliant'
    good=classify(s,'fully_settled',sit,dict(kind='report',p90_ms=410.6,verdict='passing'))
    assert good['cell']=='compliant' and not good['admissibility_validated']


def test_opposite_action_on_target_case_is_not_a_precedent():
    records=[dict(case_id='one',i_star='legal'),dict(case_id='one',i_star='illegal')]
    classes={('legal','illegal'):['target'],('illegal','legal'):['alternative']}
    assert _certificates(records,classes)==([],2)


def test_safe_harbor_and_printed_definition_metrics():
    s=load_spec(PROC)
    assert '{threshold_text}' not in render(s,'open','safe_harbor').text
    a,b=measure(s,'open'),measure(s,'fully_settled')
    assert a['page_expr_size'] < b['page_expr_size']
    assert b['page_expr_size']==b['operative_expr_size']
    assert measure(s,'open','examples')['semantic_arm_modelled'] is False


def test_no_confirmatory_run_without_validation(tmp_path):
    with pytest.raises(ValueError,match='E0 is not validated'):
        main(['run',str(PCT),'--experiment','not_launched','--models','codex:unused','--out',str(tmp_path)])
    assert not list(tmp_path.iterdir())


def test_validated_set_restricts_whole_programs_without_replacing_reference(tmp_path):
    path=Path('benchmark/rulegap/specs/kripke_addition_v1.yaml')
    s=load_spec(path); cat=catalog(s,'open')
    rows=[]
    for c in cat['candidates']:
        for i in range(3):
            rows.append(dict(catalog_digest=cat['catalog_digest'],candidate_id=c['candidate_id'],
                rater_id=f'fixture_{i}',rater_kind='human',rationale='Synthetic test, not a real rating.',
                decision='defensible' if c['assignments'][0]['ADD']=='plus' else 'indefensible'))
    target=tmp_path/'synthetic_ratings.csv'
    with target.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    validated=load_spec(path,reading_scope='validated',ratings_path=target)
    assert validated.admissible('open')==[{'ADD':'plus'}]
    assert measure(validated,'open')['n_open_terms']==0
    for row in rows:
        row['decision']='indefensible' if row['decision']=='defensible' else 'defensible'
    with target.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with pytest.raises(ValueError,match='governing reference not covered'):
        load_spec(path,reading_scope='validated',ratings_path=target).admissible('open')


def test_behavioral_witnesses_and_case_blocked_test():
    s=load_spec(PCT)
    audit=behavioral_audit(s,'percentile_only',sample_panel(s,'stress',n=3))
    assert len(audit['classes'])>1 and audit['witnesses']
    assert all(w['verdict_a']!=w['verdict_b'] for w in audit['witnesses'])
    assert all('_true_p90' not in r['situation'] for r in audit['records'])
    assert sign_flip([1,1,1,1,1,3,-2,1,3,2])==pytest.approx(0.046875)


def test_cli_table_never_promotes_legacy_candidate_gaps(tmp_path):
    # An inherited CSV has no E0 metadata; its mechanical cell is not validation.
    row=dict(rule_id='procurement_v1',rung='open',arm='control',model='scripted',incentive='none',
             is_control='False',cell='loophole',strain='1',judge_verdict='permitted',
             flagged='False',awareness='False',completed='True',cost_usd='0')
    with (tmp_path/'results.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(row));w.writeheader();w.writerow(row)
    main(['table',str(tmp_path)])
    with (tmp_path/'table.csv').open(newline='') as f:r=next(csv.DictReader(f))
    assert r['candidate_gap']=='1.0' and r['loophole']=='0.0'
    assert r['admissibility_validated']=='False'
