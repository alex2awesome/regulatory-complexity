"""Prepare W1 rendered-claim/spec link review, not automatically invented gold.

Legacy render logs identify documents, not individual claim spans. Their specs
contain omissions, noisy reports and renderer contradictions. This tool prepares
the auditable crosswalk needed before semantic_calibration accepts a truth label.
The separate source packet contains no generator specifications or truth.
"""
import argparse
from collections import Counter
import json
import pathlib

from .infra.manifest import digest, write


def prepare_review(world_root, compilations):
    world_root = pathlib.Path(world_root).resolve()
    world = json.loads((world_root/'world.json').read_text())
    if world['world'] != 'W1':
        raise ValueError('This legacy-label review is W1 development only; never open a new reserved world')
    render_entries = {}
    for line in (world_root/'render_log.jsonl').read_text().splitlines():
        if line.strip():
            event = json.loads(line)
            render_entries.setdefault(event['artifact_id'], []).append(event)
    rows, packets, seen = [], [], set()
    for path in map(pathlib.Path, compilations):
        compilation = json.loads(path.read_text())
        snapshots = path.parent/'inputs'
        inputs = json.loads((snapshots/'inputs.json').read_text())
        source_rows = []
        for disposition in compilation['dispositions']:
            if disposition['status'] == 'outside_elapsed_compiler':
                continue
            m = disposition['source']
            ident = compilation['program_id'] + ':' + m['id']
            if ident in seen:
                raise ValueError('Repeated claim in calibration review')
            seen.add(ident)
            doc = m['doc_id']
            spec_path = (world_root/'specs'/(doc+'.json')).resolve()
            if spec_path.parent != world_root/'specs':
                raise ValueError('Document identity must not escape the specs directory')
            specification = json.loads(spec_path.read_text()) if spec_path.exists() else None
            rows.append(dict(id=ident, world_id='W1', program_id=compilation['program_id'],
                measurement_id=m['id'], doc_id=doc, quote=m['quote'],
                group_id=m['source_family'], case_id=m['case_id'],
                link_status='needs_review', split=None, top_labels=None, true_labels=None,
                extraction=m, original_visit_audit=disposition['visit_audit'],
                original_semantic_audit=disposition['semantic_audit'],
                generator_spec=(dict(path=str(spec_path), sha256=digest(spec_path.read_bytes()),
                    candidate_reveals=specification.get('reveals', []),
                    observation_metadata={key: specification[key] for key in ('persona', 'thread', 'statistics')
                                          if key in specification}) if specification is not None else None),
                render_log_entries=render_entries.get(doc, []),
                truth_provenance=None,
                instructions='Link this exact rendered claim, checking renderer contradictions and report noise; do not label by matching numbers alone.'))
            source_rows.append(dict(measurement=m, visit_audit=disposition['visit_audit'],
                                    semantic_audit=disposition['semantic_audit']))
        packets.append(dict(program_id=compilation['program_id'], documents=inputs['documents'],
                            claims=source_rows, generator_truth_provided=False))
    return dict(schema_version='semantic-label-review/1', world_id='W1', purpose='development_calibration',
        status='Unlabeled review queue; not a measured confusion matrix', rows=rows,
        summary=dict(claims=len(rows), with_generator_spec=sum(r['generator_spec'] is not None for r in rows),
                     with_render_log=sum(bool(r['render_log_entries']) for r in rows),
                     verified_labels=0, by_program=dict(Counter(r['program_id'] for r in rows))),
        requirements=['Obtain top readings from source-only packets with a pinned prompt, not this review file.',
            'Verify rendered span to intended generator report; retain conflicts as renderer/source errors, not extractor mistakes.',
            'Assign disjoint source/case groups to fit and validation; W1 supplies no fresh reserved evaluation.',
            'For step merges calibrate k-vote predictors on linked pairs; do not count votes as independent labels.',
            'For agencies include unknown/out-of-chart rather than forcing a wrong closed-set identity.']), packets


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--world-root', default='benchmark/synth/worlds/W1')
    parser.add_argument('--compilations', nargs='+', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    out = pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Preserve prior review records; choose a fresh directory')
    review, packets = prepare_review(args.world_root, args.compilations)
    write(out/'review.json', review)
    for packet in packets:
        write(out/'source_only'/f"{packet['program_id']}.json", packet)
    write(out/'manifest.json', dict(source_sha256=digest(pathlib.Path(__file__).read_bytes()),
        input_sha256={str(path): digest(pathlib.Path(path).read_bytes()) for path in args.compilations},
        review_sha256=digest((out/'review.json').read_bytes()),
        generator_specs_read_for_label_review=True, new_reserved_world_read=False,
        extractor_called=False, labels_verified=False))
    print(json.dumps(review['summary']))


if __name__ == '__main__':
    main()
