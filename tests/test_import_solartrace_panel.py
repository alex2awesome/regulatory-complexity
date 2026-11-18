"""Deterministic table-contract tests; invented rows, no real sources/labels."""
import csv
import io

import pytest

from pipeline.procbench.import_solartrace import build, build_phase_panel, main


FIELDS=('state','ahj','geo_id','utility','eia_id','year','size_class','technology','metric','value')


def row(ahj='Town A',geo='1',utility='Grid',eia='11',metric='Median AHJ Permit Time',value='3',year='2023'):
    return dict(zip(FIELDS,('CA',ahj,geo,utility,eia,year,'0-10kW','PV Only',metric,value)))


def files(tmp_path,rows):
    buf=io.StringIO()
    writer=csv.DictWriter(buf,fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    table=tmp_path/'long.csv'
    table.write_text(buf.getvalue())
    definitions=tmp_path/'definitions.csv'
    defs=io.StringIO()
    writer=csv.writer(defs)
    writer.writerow(['','Median AHJ Permit Time',
        'Median business days. AHJ-only level; utility-only level; duplicated. Same-day approvals are zero.'])
    for metric in ('Median Pre-Install IX (Interconnection) Time','Median Inspection Time','Median Final IX to PTO'):
        writer.writerow(['',metric,'Median business days.'])
    definitions.write_text(defs.getvalue())
    return table,definitions


def test_join_repetitions_collapse_without_losing_provenance(tmp_path):
    table,definitions=files(tmp_path,[row(),row(utility='Second grid',eia='22'),
        row(metric='Installs',value='99'),row(utility='Second grid',eia='22',metric='Installs',value='18'),
        row(metric='Median Final IX to PTO',value='5'),
        row(ahj='Town B',geo='2',metric='Median Final IX to PTO',value='5')])
    panel,report=build_phase_panel(table,definitions)
    assert len(panel['records'])==2
    assert report['repeated_timing_rows']==2
    assert report['timing_rows']==4
    permit=next(r for r in panel['records'] if r['phase']=='permit_review')
    assert [r['joined_install_count'] for r in permit['source_rows']]==[99,18]
    assert permit['sample_size'] is None
    assert permit['unit']=='business_days'
    assert permit['modeled_as_primitive_visit'] is False
    assert not report['fit_ready'] and not report['graph_compiled']


def test_zero_and_temporal_strata_are_not_dropped_or_combined(tmp_path):
    table,definitions=files(tmp_path,[row(value='0'),row(value='0',year='2024'),
        row(metric='Median Pre-Install IX Time',value='0')])
    panel,report=build_phase_panel(table,definitions)
    assert report['unique_zero_cells']==3
    assert {r['year'] for r in panel['records']}=={2023,2024}
    assert any('no_pre_install_requirement' in r['zero_semantics'] for r in panel['records'])
    assert sum(r['zero_semantics']=='same_day_approval' for r in panel['records'])==2


def test_unidentified_utilities_do_not_become_one_global_actor(tmp_path):
    table,definitions=files(tmp_path,[row(utility='NA',eia='NA',metric='Median Final IX to PTO',value='4'),
        row(ahj='Town B',geo='2',utility='NA',eia='NA',metric='Median Final IX to PTO',value='10')])
    panel,report=build_phase_panel(table,definitions)
    assert len(panel['records'])==2 and report['unidentified_owner_cells']==2
    assert panel['records'][0]['owner_key']!=panel['records'][1]['owner_key']


@pytest.mark.parametrize('different_join',[False,True])
def test_conflicting_values_never_silently_overwrite(tmp_path,different_join):
    conflict=row(value='9',utility='Other' if different_join else 'Grid',eia='22' if different_join else '11')
    table,definitions=files(tmp_path,[row(),conflict])
    with pytest.raises(ValueError,match='Contradictory'):
        build_phase_panel(table,definitions)


def test_panel_cli_refuses_overwrite_or_an_unacknowledged_legacy_fit(tmp_path):
    table,definitions=files(tmp_path,[row()])
    output=tmp_path/'panel'
    argv=['--long',str(table),'--definitions',str(definitions),'--panel-only','--out',str(output)]
    assert main(argv)==0
    assert (output/'phase_panel.json').exists() and not (output/'data.json').exists()
    with pytest.raises(FileExistsError):
        main(argv)
    with pytest.raises(SystemExit):
        main(['--long',str(table),'--out',str(tmp_path/'unsafe')])
    with pytest.raises(ValueError,match='never implemented'):
        build(table,12,cohort_phase='permit_review')
