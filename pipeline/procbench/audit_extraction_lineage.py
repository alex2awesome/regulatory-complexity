"""Reconstruct historical extraction lineage without rewriting original runs."""
import argparse
import json
import pathlib

from .evidence_contract import validate
from .reconcile_evidence import digest, write


def audit_lineage(root, programs):
    root = pathlib.Path(root)
    rows = []
    for program in programs:
        original = root/'extraction'/program
        imported = root/'extraction'/(program+'_first_validated')
        paths = dict(first=original/'attempt_0.json', repaired=original/'attempt_1.json',
                     original_final=original/'evidence.json', downstream_import=imported/'evidence.json')
        values = {name: json.loads(path.read_text()) for name, path in paths.items()}
        old_manifest = json.loads((original/'manifest.json').read_text())
        import_manifest = json.loads((imported/'manifest.json').read_text())
        downstream_manifest = json.loads((root/'granularity'/program/'manifest.json').read_text())
        documents = json.loads((original/'inputs.json').read_text())['documents']
        validation = {}
        for name, value in values.items():
            try:
                validate(value, documents)
                validation[name] = dict(valid=True)
            except (ValueError, __import__('jsonschema').ValidationError) as error:
                validation[name] = dict(valid=False, error=str(error))
        hashes = {name: digest(path.read_bytes()) for name, path in paths.items()}
        row = dict(program=program, paths={k: str(v) for k, v in paths.items()}, sha256=hashes,
            first_attempt_equal_to_downstream_import=values['first'] == values['downstream_import'],
            repaired_attempt_equal_to_original_final=values['repaired'] == values['original_final'],
            downstream_uses_imported_hash=downstream_manifest['input_sha256'] == hashes['downstream_import'],
            original_rejection_messages=old_manifest.get('validation_repairs', []),
            retrospective_import_note=import_manifest.get('note'),
            prospective_attempt_selection_rule_recorded=False,
            historical_validator_snapshot_identified=False,
            current_validation=validation)
        if not (row['first_attempt_equal_to_downstream_import'] and row['downstream_uses_imported_hash']):
            raise ValueError('Lineage differs from the audited path: ' + program)
        rows.append(row)
    source = pathlib.Path(__file__).with_name('evidence_contract.py')
    return dict(schema_version='extraction-lineage-audit/1', programs=rows,
        current_validator_sha256=digest(source.read_bytes()),
        qualifications=['Retrospective reconstruction, not a claim the original validator accepted attempt zero.',
            'Current validation cannot reconstruct an unarchived historical validator.',
            'Earlier reports and matched controls used the imported first attempt, not repaired attempt one.',
            'No old inputs, manifests, posteriors or scores were rewritten; no truth was read.'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='runs/bayes_v4')
    parser.add_argument('--programs', nargs='+', default=['J1__S01', 'J1__S03', 'J2__S07'])
    parser.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    out = pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Choose a fresh audit directory')
    report = audit_lineage(args.root, args.programs)
    write(out/'lineage.json', report)
    target = out/'source'/'audit_extraction_lineage.py'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(pathlib.Path(__file__).read_bytes())
    target.with_name('evidence_contract.py').write_bytes(pathlib.Path(__file__).with_name('evidence_contract.py').read_bytes())
    print(json.dumps([dict(program=r['program'], import_matches_first=r['first_attempt_equal_to_downstream_import'],
                           downstream_hash_matches=r['downstream_uses_imported_hash']) for r in report['programs']]))


if __name__ == '__main__':
    main()
