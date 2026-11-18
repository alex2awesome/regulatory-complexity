"""Summarize every condition of a frozen single-clock report-frame plan.

No sampling, condition selection, population transport, or numerical-gate
override. Reusable for completed and censored report frames in integrated V6.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from .bayes_trace_hierarchy import Config, VisitHierarchy
from .marginal_conditional_frames import INTEGRATION_KIND, MarginalConditionalFrame
from .infra.manifest import source_closure


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite_sample_median_bounds(observations: list[dict]) -> dict:
    """Bounds for the median of these records, treating supplied bounds literally.

    This is an order-statistic calculation, not a posterior, confidence interval,
    population estimator, or baseline for source/reporting bias. For even n the
    sample median is the average of the two central order statistics. A null
    upper bound represents infinity, including potentially never-ending cases.
    """
    if not observations:
        raise ValueError('Sample-median bounds require at least one observation')
    lower, upper = [], []
    for observation in observations:
        lo, hi = observation['lower'], observation['upper']
        if (isinstance(lo, bool) or not isinstance(lo, (int, float))
                or not math.isfinite(lo) or lo < 0
                or (hi is not None and (isinstance(hi, bool)
                    or not isinstance(hi, (int, float))
                    or not math.isfinite(hi) or hi <= lo))):
            raise ValueError('Finite nonnegative lower and larger finite or null upper required')
        lower.append(float(lo))
        upper.append(math.inf if hi is None else float(hi))
    lower.sort(); upper.sort()
    left, right = (len(lower)-1)//2, len(lower)//2
    lo = lower[left]/2 + lower[right]/2
    hi = upper[left]/2 + upper[right]/2
    return dict(cases=len(lower), lower=lo, upper=None if math.isinf(hi) else hi,
        median_convention='average of central order statistics for even n',
        qualification='Descriptive bounds for this finite set of reported case intervals, '
            'assuming the supplied intervals literally contain their reported durations. '
            'Not a population interval, posterior interval, reporting-error correction, '
            'or evidence of ignorable posting/censoring. Open boundaries are reported by '
            'their infimum/supremum. Null upper means unbounded.')


def summarize(packet: Path, out: Path, root: Path, *, display_unit='days') -> dict:
    if display_unit not in ('days', 'minutes'):
        raise ValueError('Display unit must be days or minutes')
    if out.exists():
        raise FileExistsError(out)
    manifest = json.loads((packet/'manifest.json').read_text())
    for item in manifest['inputs'] + manifest['outputs']:
        if _sha(root/item['path']) != item['sha256']:
            raise ValueError('Prepared input changed: '+item['path'])
    plan = json.loads((packet/'plan.json').read_text())
    lineage_path = packet/'model_input_lineage.json'
    lineage_rows = json.loads(lineage_path.read_text())
    lineage = {r['observation_id']: r for r in lineage_rows}
    if len(lineage) != len(lineage_rows):
        raise ValueError('Source-to-input lineage must have distinct observation IDs')
    for row in lineage_rows:
        if _sha(root/row['artifact']) != row['artifact_sha256']:
            raise ValueError('Source artifact changed: '+row['artifact'])
        for source in row.get('supporting_sources', []):
            path = root/source['path']
            if _sha(path) != source['sha256']:
                raise ValueError('Supporting artifact changed: '+source['path'])
            if any(quote not in path.read_text() for quote in source['quote_segments']):
                raise ValueError('Supporting quotation changed: '+source['path'])
    results, bindings, consumed = [], [], []
    for condition in plan['conditions']:
        fit = packet/('fit_'+condition['id'])
        data = json.loads((fit/'data.json').read_text())
        posterior = json.loads((fit/'posterior.json').read_text())
        fit_manifest = json.loads((fit/'manifest.json').read_text())
        if (fit_manifest.get('status') != 'completed'
                or fit_manifest.get('config') != posterior['config']
                or fit_manifest.get('posterior_sha256') != _sha(fit/'posterior.json')
                or fit_manifest.get('draws_sha256') != _sha(fit/'draws.npz')):
            raise ValueError('Fit lifecycle or output hash mismatch: '+condition['id'])
        prepared = json.loads((packet/(condition['id']+'_data.json')).read_text())
        if data != prepared or posterior['config'] != condition['config']:
            raise ValueError('Fit differs from the frozen condition: '+condition['id'])
        if posterior.get('inference') != condition.get('inference'):
            raise ValueError('Fit differs from frozen inference settings: '+condition['id'])
        if posterior.get('inference', {}).get('kind') == INTEGRATION_KIND:
            model = MarginalConditionalFrame(data, Config(**posterior['config']),
                posterior['inference']['quadrature_size'])
            if model.inference != posterior['inference']:
                raise ValueError('Unknown marginal inference settings')
        elif posterior.get('inference') is not None:
            raise ValueError('Unknown inference contract')
        else:
            model = VisitHierarchy(data, Config(**posterior['config']))
        entry = ('marginal_conditional_frames.py' if posterior.get('inference')
                 else 'bayes_trace_hierarchy.py')
        for name, raw in source_closure(Path(__file__).parent, [entry]).items():
            expected_hash = fit_manifest.get('source_sha256', {}).get(name)
            if (expected_hash != hashlib.sha256(raw).hexdigest()
                    or not (fit/'source'/name).is_file()
                    or _sha(fit/'source'/name) != expected_hash):
                raise ValueError('Fit likelihood dependency differs from current/saved code: '+name)
        if display_unit == 'minutes' and model.cfg.elapsed_time_unit != 'calendar_days':
            raise ValueError('Business days cannot be displayed as continuous elapsed minutes')
        if len(model.conditional_case_frames) != 1 or len(data['programs']) != 1:
            raise ValueError('This analysis requires one declared conditional clock frame')
        with np.load(fit/'draws.npz') as saved:
            states = saved['z']
            structures = saved['structures']
            likelihood = saved['log_likelihood']
        expected = (model.cfg.chains, model.cfg.draws, model.layout.size)
        if states.shape != expected or likelihood.shape != expected[:2]:
            raise ValueError('Saved draws do not match the frozen configuration')
        flat = states.reshape(-1, states.shape[-1])
        routes = structures.reshape(-1, 1)
        indices = np.linspace(0, len(flat)-1, min(8, len(flat)), dtype=int)
        delta = max(abs(model.log_likelihood(flat[i], routes[i])-likelihood.ravel()[i]) for i in indices)
        if not math.isfinite(delta) or delta > 1e-8:
            raise ValueError('Saved likelihood target does not replay')
        program = data['programs'][0]
        for obs in program['observations']:
            source = lineage[obs['id']]
            if obs['case_id'] != source['case_id']:
                raise ValueError('Source-to-input case mismatch: '+obs['id'])
            if 'bounds_calendar_days' in source and [obs['lower'],obs['upper']] != source['bounds_calendar_days']:
                raise ValueError('Source-to-input interval mismatch: '+obs['id'])
            if 'bounds' in source and ([obs['lower'],obs['upper']] != source['bounds']
                    or model.cfg.elapsed_time_unit != source['elapsed_time_unit']):
                raise ValueError('Source-to-input interval/unit mismatch: '+obs['id'])
            consumed.append(dict(condition=condition['id'], observation_id=obs['id'],
                case_id=obs['case_id'], observation_kind=obs.get('observation_kind','completed_interval'),
                source_artifact=source['artifact'], source_artifact_sha256=source['artifact_sha256']))
        frame = model.conditional_case_frames[program['id']]
        p = posterior['programs'][program['id']]
        results.append(dict(condition=condition['id'], cases=len(program['observations']),
            elapsed_time_unit=model.cfg.elapsed_time_unit,
            observation_kind_counts=frame.get('observation_kind_counts',{'completed_interval':len(program['observations'])}),
            numerically_usable=posterior['numerically_usable'], diagnostics_flagged=posterior['diagnostics_flagged'],
            likelihood_replay_max_difference=delta,
            report_frame_median_days=p['metrics']['modeled_work_end_median_days'],
            finite_record_sample_median_bounds=finite_sample_median_bounds(program['observations']),
            all_lower_bounds=frame.get('all_observations_lower_bounds',False),
            clock_estimand=program['clock_estimand']))
        for name in ['data.json','posterior.json','draws.npz','manifest.json']:
            path=fit/name
            bindings.append(dict(path=str(path.relative_to(root)),sha256=_sha(path)))
    result=dict(conditions=results,unique_forum_cases_consumed=len({r['case_id'] for r in consumed}),
        no_best_condition_selection=True, numerical_gate_overridden=False,
        qualification='Selected conditional report frames, not population burden or learned source/agency effects. Numerical success does not establish model adequacy or ignorable posting/censoring.')
    out.mkdir(parents=True)
    def write(name,value):
        (out/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    write('results.json',result)
    write('actual_model_consumption.json',consumed)
    has_terminal_neutral = any(row['observation_kind_counts'].get(
        'terminal_neutral_lower_bound', 0) for row in results)
    if has_terminal_neutral:
        lines=['# Conditional forum-frame results','',
            f'| Condition | Cases | Completed-status | Pending | Terminal-neutral | Numerical gate | Report-frame median, {display_unit} (90% interval) |',
            '|---|---:|---:|---:|---:|---|---|']
    else:
        lines=['# Conditional forum-frame results','',
            f'| Condition | Cases | Pending | Numerical gate | Report-frame median, {display_unit} (90% interval) |',
            '|---|---:|---:|---|---|']
    for row in results:
        m=row['report_frame_median_days']
        factor = 1440. if display_unit == 'minutes' else 1.
        value=(f"{m['median']*factor:.2f} ({m['ci90'][0]*factor:.2f}–{m['ci90'][1]*factor:.2f})"
               if row['numerically_usable'] and not row['all_lower_bounds'] else 'Not headline eligible; raw diagnostics retained')
        counts = row['observation_kind_counts']
        if has_terminal_neutral:
            completed = counts.get('completed_interval',0) + counts.get('completed_lower_bound',0)
            lines.append(f"| {row['condition']} | {row['cases']} | {completed} | {counts.get('pending_right_censored',0)} | {counts.get('terminal_neutral_lower_bound',0)} | {'PASS' if row['numerically_usable'] else 'FAIL'} | {value} |")
        else:
            lines.append(f"| {row['condition']} | {row['cases']} | {counts.get('pending_right_censored',0)} | {'PASS' if row['numerically_usable'] else 'FAIL'} | {value} |")
    lines += ['',result['qualification'],'',
        ('All prespecified conditions are retained. Adding pending histories or terminal-neutral elapsed bounds changes the'
         if has_terminal_neutral else 'All prespecified conditions are retained. Adding pending histories changes the'),
        'selected frame; this is not an estimated correction for forum selection. The',
        'clock is exactly the declared clock_estimand, not an interchangeable whole-process total.',
        'Source semantics and date/rounding assumptions remain those in the prepared packet.',
        'Days use each condition\'s declared elapsed_time_unit in results.json; no calendar/business conversion is performed.',
        ('This table displays calendar days ×1440 as elapsed minutes; native posterior values remain in results.json.'
         if display_unit == 'minutes' else 'The table uses the native declared day unit.'),
        'See actual_model_consumption.json for every fitted factor and its source.', '',
        '## Direct bounds from the supplied case intervals', '',
        'These bound the median of the finite reported records, not the median of',
        'the modeled distribution. They assume the compiled intervals literally',
        'contain the reports; source ambiguity and rounding assumptions remain.',
        'They are neither credible nor confidence intervals and do not correct',
        'reporting error, censoring selection, or population selection.', '',
        *(['A terminal-neutral [lower, null] row enters these direct bounds as [lower, infinity]. '
           'It supplies elapsed-time information but makes no completed-versus-pending assertion.', '']
          if has_terminal_neutral else []),
        f'| Condition | Finite-record sample-median bounds, {display_unit} |',
        '|---|---:|']
    for row in results:
        bounds = row['finite_record_sample_median_bounds']
        factor = 1440. if display_unit == 'minutes' else 1.
        upper = 'unbounded' if bounds['upper'] is None else f"{bounds['upper']*factor:.2f}"
        lines.append(f"| {row['condition']} | {bounds['lower']*factor:.2f}–{upper} |")
    lines.append('')
    (out/'README.md').write_text('\n'.join(lines))
    write('manifest.json',dict(inputs=bindings, prepared_manifest_sha256=_sha(packet/'manifest.json'),
        lineage_sha256=_sha(lineage_path), analysis_code_sha256=_sha(Path(__file__)),
        current_model_code_sha256=_sha(Path(__file__).with_name('bayes_trace_hierarchy.py')),
        marginal_helper_code_sha256=_sha(Path(__file__).with_name('marginal_conditional_frames.py')),
        display_unit=display_unit,
        outputs=[dict(path=name,sha256=_sha(out/name)) for name in ['results.json','actual_model_consumption.json','README.md']],
        no_sampling=True,hidden_truth_read=False))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--display-unit',choices=('days','minutes'),default='days')
    args=parser.parse_args()
    print(json.dumps(summarize(args.packet.resolve(),args.out.resolve(),Path.cwd(),
                              display_unit=args.display_unit),indent=2))


if __name__=='__main__': main()
