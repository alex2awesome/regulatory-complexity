"""Kripke control: 'add' read as plus or as quus. Under the declared case range
the two agree everywhere, so the rule is fully settled there."""


def build_case(x, y):
    return dict(x=x, y=y)


def uniform_pairs(rng, i, params, spec):
    lo, hi = params.get('range', [0, 56])
    return build_case(int(rng.integers(lo, hi + 1)), int(rng.integers(lo, hi + 1)))


def candidate_actions(spec, situation):
    total = situation['x'] + situation['y']
    return [dict(kind='report', value=v) for v in dict.fromkeys([total, 5])]


DOMAIN = dict(features={}, generators=dict(uniform_pairs=uniform_pairs), reading_sets={},
              candidate_actions=candidate_actions, build_case=build_case)


DOMAIN.update(role='You are a clerk totalling two quantities.', apply=lambda situation, action: situation,
    completed=lambda s0, s: None, tools={
        'report': dict(desc='Report the result.', args=dict(value='integer')),
        'ask': dict(desc='Put a question to your supervisor. The task then waits for their answer.', args=dict(question='string')),
        'done': dict(desc='Finish.', args={})})
