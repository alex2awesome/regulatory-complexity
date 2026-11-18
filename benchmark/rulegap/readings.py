"""Panel evaluation, behavioural classes and the live-reading report."""
from .cases import candidate_actions
from .compile import DecisionFunction, intended_verdict, purpose_verdict, UNDEFINED
from .spec import key


def evaluate_panel(spec, rung, panel):
    """One record per (case, candidate action): verdict under every admissible
    assignment (in spec.admissible order), I* and P."""
    adm = spec.admissible(rung)
    judged = spec.skeleton(rung)['judged_action']
    out = []
    for case in panel:
        for j, action in enumerate(candidate_actions(spec, case['situation'])):
            if action.get('kind') != judged:
                continue
            cache, open_j = {}, set()
            sit = action.get('_situation', case['situation'])   # state after the action's declared pre-steps
            verdicts = tuple(DecisionFunction(spec, a, rung).apply(sit, action, cache) for a in adm)
            out.append(dict(case_id=case['case_id'], action_index=j, action=action, situation=sit,
                verdicts=verdicts, i_star=intended_verdict(spec, rung, sit, action, None, open_j),
                p=purpose_verdict(spec, rung, sit, action), open_judgments=sorted(open_j)))
    return out


def behavioral_classes(spec, rung, records):
    """Group assignments with identical verdict vectors over the panel."""
    adm = spec.admissible(rung)
    classes = {}
    for i, a in enumerate(adm):
        classes.setdefault(tuple(r['verdicts'][i] for r in records), []).append(a)
    return classes


def live_readings(spec, rung, records, mass=0.95, prior=None):
    prior = prior or spec.prior(rung)
    intended = {key(a) for a in spec.intended(rung)}
    istar = tuple(r['i_star'] for r in records)
    rows = []
    for vec, members in behavioral_classes(spec, rung, records).items():
        both = [(v, s) for v, s in zip(vec, istar) if s != UNDEFINED]
        rows.append(dict(rung=rung, reading_scope=spec.reading_scope,
            admissibility_validated=spec.reading_scope=='validated', equivalence_scope='declared finite panel',
            representative=key(members[0]), n_assignments=len(members),
            prior_mass=sum(prior[key(a)] for a in members),
            disagrees_with_istar_share=sum(v != s for v, s in both) / len(both) if both else None,
            contains_istar=any(key(a) in intended for a in members)))
    rows.sort(key=lambda r: -r['prior_mass'])
    total = 0.0
    for i, r in enumerate(rows):
        r['class_id'] = i
        r['live'] = total < mass
        total += r['prior_mass']
    return rows
