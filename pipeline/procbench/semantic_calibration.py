"""Measure interpretation error on explicitly linked calibration labels.

This is an evaluator, not a source extractor. Generator labels never enter an
extractor prompt. A new world requires a new, group-disjoint calibration split;
reserved evaluation rows are forbidden. Repeated LLM votes are one predictor
(a stratum), not independent labeled observations.
"""
import argparse
from collections import Counter, defaultdict
import json
import math
import pathlib

import numpy as np
from scipy.stats import beta

from .reconcile_evidence import digest, write


SCHEMA = 'semantic-calibration/1'
LABEL_SCHEMA = 'semantic-calibration-labels/1'


def fit_calibration(dataset, threshold=.9, pseudocount=.5, min_validation_groups=3):
    """Return P(true label | reported label, vote stratum), not its inverse.

    Training fits the categorical weights; disjoint validation groups decide
    whether top-reading accuracy supports keeping that class upstream. Credible
    intervals on matrix cells are Dirichlet-multinomial, conditional on the
    exchangeability assumption. Accuracy uncertainty uses a group bootstrap.
    """
    if dataset.get('schema_version') != LABEL_SCHEMA or not dataset.get('world_id'):
        raise ValueError('Need a versioned, single-world calibration label set')
    if dataset.get('purpose') != 'development_calibration':
        raise ValueError('Reserved evaluation labels must not train interpretation priors')
    if not 0 < threshold < 1 or not math.isfinite(pseudocount) or pseudocount <= 0:
        raise ValueError('Invalid threshold or Dirichlet pseudocount')
    if not isinstance(min_validation_groups, int) or min_validation_groups < 2:
        raise ValueError('At least two independent validation groups are required')
    extractor = dataset.get('extractor', {})
    if any(not extractor.get(k) for k in ('model', 'prompt_sha256')):
        raise ValueError('Calibration is conditional on a pinned extractor and prompt hash')
    spaces = dataset['label_spaces']
    for name, labels in spaces.items():
        if not name or len(labels) < 2 or len(labels) != len(set(labels)) or any(not isinstance(x, str) or not x for x in labels):
            raise ValueError('Each ambiguity class needs an explicit distinct label space')
    groups, ids, rows_by_class = {}, set(), defaultdict(list)
    for row in dataset['rows']:
        if row.get('split') not in {'fit', 'validation'}:
            raise ValueError('Only fit/validation labels are allowed, never reserved/test labels')
        if row.get('world_id') != dataset['world_id']:
            raise ValueError('Re-measure calibration separately on each new world')
        if row.get('link_status') != 'verified' or not row.get('truth_provenance'):
            raise ValueError('A rendered-claim to generator link must be verified, not guessed')
        if not row.get('id') or row['id'] in ids:
            raise ValueError('Each labeled judgment must occur once; votes are not extra rows')
        ids.add(row['id'])
        group = row.get('group_id')
        if not group:
            raise ValueError('Case/source dependence requires an explicit group ID')
        if group in groups and groups[group] != row['split']:
            raise ValueError('Same case/source group crosses calibration and validation splits')
        groups[group] = row['split']
        kind = row['ambiguity_class']
        if kind not in spaces or row['top_label'] not in spaces[kind] or row['true_label'] not in spaces[kind]:
            raise ValueError('Reported and true labels must belong to the declared label space')
        if not isinstance(row.get('stratum', 'all'), str):
            raise ValueError('Vote/model strata must be explicit categorical predictors')
        rows_by_class[kind].append(row)
    if not ids:
        raise ValueError('No verified labels; do not fabricate a measured confusion matrix')
    classes = {}
    for kind, labels in spaces.items():
        rows = rows_by_class[kind]
        train = [r for r in rows if r['split'] == 'fit']
        validation = [r for r in rows if r['split'] == 'validation']
        strata = sorted({r.get('stratum', 'all') for r in rows})
        tables = {}
        for stratum in strata:
            table = {}
            for reported in labels:
                counts = Counter(r['true_label'] for r in train
                                 if r['top_label'] == reported and r.get('stratum', 'all') == stratum)
                alpha = np.array([counts[label] + pseudocount for label in labels])
                total = float(alpha.sum())
                table[reported] = dict(n=sum(counts.values()), counts=dict(counts),
                    probabilities=dict(zip(labels, (alpha / total).tolist())),
                    ci90={label: beta.ppf([.05, .95], a, total-a).tolist()
                          for label, a in zip(labels, alpha)},
                    calibrated=bool(counts))
            tables[stratum] = table
        correct = sum(r['top_label'] == r['true_label'] for r in validation)
        n = len(validation)
        by_group = defaultdict(list)
        for row in validation:
            by_group[row['group_id']].append(row['top_label'] == row['true_label'])
        interval = None
        if len(by_group) >= 2:
            # Resample groups, keeping all dependent claims/votes together.
            totals = np.array([(sum(v), len(v)) for _, v in sorted(by_group.items())])
            indices = np.random.default_rng(20260916).integers(len(totals), size=(2000, len(totals)))
            sums = totals[indices].sum(axis=1)
            interval = np.quantile(sums[:, 0] / sums[:, 1], [.05, .95]).tolist()
        accuracy = correct/n if n else None
        supported = n > 0 and len(by_group) >= min_validation_groups and bool(train)
        decision = ('top_reading' if accuracy >= threshold else 'mixture_candidate') if supported else 'insufficient_validation'
        classes[kind] = dict(labels=labels, fit_rows=len(train), validation_rows=n,
            validation_groups=len(by_group), top_accuracy=accuracy, top_accuracy_group_bootstrap_ci90=interval,
            decision=decision, threshold=threshold,
            threshold_uncertain=interval is None or interval[0] < threshold <= interval[1],
            confusion_by_reported_label=tables,
            mixture_promotion_requires='Paired disjoint validation: timing and counts, identical evidence and numerical usability')
    return dict(schema_version=SCHEMA, world_id=dataset['world_id'], purpose='development_calibration',
        extractor=extractor, label_set_sha256=digest(json.dumps(dataset, sort_keys=True)),
        smoothing_pseudocount=pseudocount, min_validation_groups=min_validation_groups,
        classes=classes, fit_groups=sorted(g for g, s in groups.items() if s == 'fit'),
        validation_groups=sorted(g for g, s in groups.items() if s == 'validation'),
        qualifications=['Matrix cells estimate P(true | reported), conditional on this world, extractor and strata.',
            'K correlated LLM votes form one stratum, not K independent truth labels.',
            'The 90% routing threshold is a development rule, not proof of negligible downstream error.',
            'Cell intervals condition on exchangeable labeled judgments; group bootstrap quantifies validation accuracy.',
            'A mixture is not promoted merely because top-reading accuracy is below threshold.'])


def calibrated_weights(calibration, ambiguity_class, top_label, *, world_id, extractor, stratum='all'):
    if calibration.get('schema_version') != SCHEMA or calibration.get('purpose') != 'development_calibration':
        raise ValueError('A measured calibration artifact is required')
    if calibration['world_id'] != world_id or calibration['extractor'] != extractor:
        raise ValueError('World/extractor changed: re-measure confusion matrices before reuse')
    try:
        cell = calibration['classes'][ambiguity_class]['confusion_by_reported_label'][stratum][top_label]
    except KeyError as error:
        raise ValueError('No calibration for this ambiguity class, reading or vote stratum') from error
    if not cell['calibrated'] or cell['n'] < 1:
        raise ValueError('This reading has no training labels; smoothing alone is not calibration')
    probabilities = cell['probabilities']
    if any(not math.isfinite(v) or v <= 0 for v in probabilities.values()) or not math.isclose(sum(probabilities.values()), 1.):
        raise ValueError('Invalid calibrated probabilities')
    return dict(probabilities)


def operator_weights(calibration, reading, *, world_id, extractor):
    """Map truth-label probabilities to candidates; all uncovered mass is residual.

    Candidate keys can name a validated hypothesis or an unchanged audit operator.
    No probabilities are assigned by the LLM, and no subset is renormalized.
    """
    probabilities = calibrated_weights(calibration, reading['ambiguity_class'], reading['top_label'],
        world_id=world_id, extractor=extractor, stratum=reading.get('stratum', 'all'))
    mapping = reading['label_to_candidate']
    if set(mapping) - probabilities.keys():
        raise ValueError('Candidate mapping names unknown calibration labels')
    out = defaultdict(float)
    for label, weight in probabilities.items():
        candidate = mapping.get(label, '__residual__')
        if not isinstance(candidate, str) or not candidate:
            raise ValueError('Candidate identities must be explicit nonempty strings')
        out[candidate] += weight
    return dict(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--labels', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--threshold', type=float, default=.9)
    parser.add_argument('--min-validation-groups', type=int, default=3)
    args = parser.parse_args(argv)
    out = pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Preserve calibration artifacts; choose a fresh directory')
    path = pathlib.Path(args.labels)
    report = fit_calibration(json.loads(path.read_text()), threshold=args.threshold,
                             min_validation_groups=args.min_validation_groups)
    write(out/'calibration.json', report)
    write(out/'manifest.json', dict(labels=str(path), labels_sha256=digest(path.read_bytes()),
        source_sha256=digest(pathlib.Path(__file__).read_bytes()),
        calibration_sha256=digest((out/'calibration.json').read_bytes()),
        generator_labels_read=True, reserved_evaluation_labels_allowed=False))
    print(json.dumps({k: {f: v[f] for f in ('top_accuracy', 'validation_groups', 'decision')}
                      for k, v in report['classes'].items()}))


if __name__ == '__main__':
    main()
