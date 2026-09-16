"""Report which burden quantities have direct numerical support, without fitting.

An estimate borrowed from another program is not a direct measurement. Hours,
elapsed time, staffing, money and workload remain separate evidence channels.
"""


def burden_support(evidences):
    results = {}
    for evidence in evidences:
        contexts = {c['measurement_id']: c for c in evidence.get('observation_contexts', [])}
        historical_cases = {m.get('case_id') for m in evidence['measurements'] if m.get('case_id')
            and m['scope']=='process' and contexts.get(m['id'],{}).get('temporal_scope')=='historical'}
        channels = {}
        for metric in ('elapsed','payer_work','agency_work','fee','staffing_fte','annual_volume'):
            claims = [m for m in evidence['measurements'] if m['metric']==metric]
            numerical = [m for m in claims if any(m[k] is not None for k in ('value','lower','upper'))
                         and m['statistic'] not in {'statutory_cap','target'}
                         and m.get('case_id') not in historical_cases
                         and contexts.get(m['id'],{}).get('temporal_scope') not in {'historical','hypothetical'}]
            work = metric in {'payer_work','agency_work'}
            eligible = [m for m in numerical if not work or m['scope']!='standing']
            channels[metric] = {'direct_numerical_claims':len(eligible),
                'measurement_ids':[m['id'] for m in eligible],
                'source_families':sorted({m['source_family'] for m in eligible}),
                'claims':[{k:m[k] for k in ('id','scope','statistic','value','lower','upper','unit','quote')}
                          for m in eligible],
                'standing_claim_ids':[m['id'] for m in numerical if m['scope']=='standing']}
        results[evidence['program_id']] = channels
    for pid,channels in results.items():
        for metric in ('payer_work','agency_work'):
            channels[metric]['borrowed_only_if_estimated'] = (not channels[metric]['direct_numerical_claims'] and
                any(other[metric]['direct_numerical_claims'] for other in results.values()))
            channels[metric]['qualification'] = ('Work-hour estimates are independent of elapsed days; '
                'cost-study estimates are not observed individual labor samples. '
                'An unspecified estimate statistic is interpreted as typical/median by the current likelihood.')
    return results
