"""Freeze complete-thread parse work orders from existing public artifact indexes.

No extraction or content-based exclusion is performed. Windows checkpoint work
within one thread owner; they are not independently reconciled process ledgers.
Historical parse manifests are references, not proof of semantic completeness.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_text())


def build(root, out, window_pages=10, source_structure=None):
    if out.exists():
        raise FileExistsError(f'Preserve previous plan: {out}')
    if window_pages < 1:
        raise ValueError('window_pages must be positive')
    threads = defaultdict(list)
    ordinary, doc_ids, index_receipts = [], set(), []
    for slice_name in ('calguns_a', 'calguns_g', 'calguns_q'):
        base = root / slice_name
        index_path = base / 'artifact_only_index.json'
        index = read(index_path)
        index_receipts.append(dict(path=str(index_path), sha256=sha(index_path.read_bytes())))
        rows = {r['document_id']: r for r in index['documents']}
        if len(rows) != len(index['documents']):
            raise ValueError(f'Duplicate document IDs within {slice_name}')
        partition = read(base / 'partition.json')
        ordinary_ids = set()
        for batch in partition['batches']:
            ids = batch['pages']
            if ordinary_ids.intersection(ids):
                raise ValueError('Overlapping ordinary batches')
            ordinary_ids.update(ids)
            ordinary.append(dict(slice=slice_name, batch=batch['batch'],
                document_ids=ids, legacy_output=str(base / ('batch' + str(batch['batch']))),
                acceptance='requires_verified_receipt'))
        if not ordinary_ids <= rows.keys():
            raise ValueError('Partition references absent artifacts')
        for doc_id, entry in rows.items():
            if doc_id in doc_ids:
                raise ValueError('Document ID overlaps frozen slices: ' + doc_id)
            doc_ids.add(doc_id)
            match = re.fullmatch(r'calguns_(\d+)_page(\d+)(?:_.*)?', doc_id)
            if match is None:
                raise ValueError('Unrecognized thread/page identity: ' + doc_id)
            path = base / 'artifacts' / (doc_id + '.md')
            raw = path.read_bytes()
            if sha(raw) != entry['sha256']:
                raise ValueError('Artifact changed since freeze: ' + str(path))
            page = int(match[2])
            page_provenance = dict(basis='filename', filename_page=page)
            if source_structure is not None:
                companion_path = source_structure / (doc_id + '.json')
                companion = read(companion_path)
                if companion['document_id'] != doc_id or companion['artifact_sha256'] != entry['sha256']:
                    raise ValueError('Source structure does not describe this frozen artifact')
                if sha(Path(companion['source_path']).read_bytes()) != companion['origin_sha256']:
                    raise ValueError('Source structure origin has changed')
                page = companion['page_metadata']['logical_page']
                if not isinstance(page, int) or page < 1:
                    raise ValueError('Invalid logical page')
                page_provenance.update(basis='canonical_url_and_navigation',
                    companion_path=str(companion_path), companion_sha256=sha(companion_path.read_bytes()),
                    canonical_url=companion['page_metadata']['canonical_url'])
            threads[match[1]].append(dict(document_id=doc_id, page=page, page_provenance=page_provenance,
                path=str(path), slice=slice_name, bytes=len(raw), sha256=sha(raw),
                ordinary=doc_id in ordinary_ids))
    jobs = []
    for thread, docs in sorted(threads.items(), key=lambda item: int(item[0])):
        docs.sort(key=lambda d: (d['page'], d['document_id']))
        modes = {d['ordinary'] for d in docs}
        if len(modes) != 1:
            raise ValueError('Thread split between ordinary and megathread work: ' + thread)
        if modes == {True}:
            owners = [b for b in ordinary if set(b['document_ids']) & {d['document_id'] for d in docs}]
            if len(owners) != 1:
                raise ValueError('Ordinary thread split across owners: ' + thread)
            continue
        page_groups = defaultdict(list)
        for doc in docs:
            page_groups[doc['page']].append(doc)
        page_numbers = sorted(page_groups)
        windows = []
        for start in range(0, len(page_numbers), window_pages):
            numbers = page_numbers[start:start + window_pages]
            windows.append(dict(window=len(windows) + 1, page_numbers=numbers,
                document_ids=[d['document_id'] for n in numbers for d in page_groups[n]],
                status='pending'))
        present = set(page_numbers)
        missing = [n for n in range(1, max(present) + 1) if n not in present]
        jobs.append(dict(thread_id=thread, status='pending',
            owner=None, document_count=len(docs), unique_page_count=len(present),
            byte_count=sum(d['bytes'] for d in docs), slices=sorted({d['slice'] for d in docs}),
            documents=docs, windows=windows,
            absent_page_numbers_through_highest_frozen=missing,
            multiple_artifacts_same_page={str(n): [d['document_id'] for d in ds]
                                         for n, ds in page_groups.items() if len(ds) > 1},
            source_completeness='unknown; page gaps and thread terminal page require separate retrieval audit',
            output_directory=str(out.parent / ('calguns_' + thread))))
    assigned = [d['document_id'] for j in jobs for d in j['documents']]
    assigned += [d for b in ordinary for d in b['document_ids']]
    if len(assigned) != len(set(assigned)) or set(assigned) != doc_ids:
        raise ValueError('Work partition does not cover frozen documents exactly once')
    result = dict(schema_version='forum-parse-work-plan/1', created_utc=datetime.now(timezone.utc).isoformat(),
        source_indexes=index_receipts, frozen_document_count=len(doc_ids),
        ordinary_batch_count=len(ordinary), ordinary_document_count=sum(len(b['document_ids']) for b in ordinary),
        megathread_count=len(jobs), megathread_document_count=sum(j['document_count'] for j in jobs),
        semantic_extraction_performed=False, ordinary_batches=ordinary, megathreads=jobs,
        rules=[
            'Assign one owner per complete thread, including every frozen slice.',
            'Read windows in numeric page order; save coverage and extracted claims after each window.',
            'Track author, application episode and policy period; usernames alone do not establish same case.',
            'Mark quoted prior posts and repeated claims; preserve source speaker separately from current poster.',
            'Do not infer agency delay causation or policy intent from absence of contrary statements.',
            'Do not pass prior corpus conclusions into extraction prompts.',
            'Separate full reading coverage, validated quotations, semantic review and fit readiness.',
            'A provenance declaration is not a technical proof of restricted file access.',
            'Reconcile all windows before accepting one thread ledger; preserve incomplete attempts.'])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--window-pages', type=int, default=10)
    parser.add_argument('--source-structure', type=Path)
    args = parser.parse_args()
    plan = build(args.root, args.out, args.window_pages, args.source_structure)
    print(json.dumps({k: plan[k] for k in ('frozen_document_count', 'ordinary_batch_count',
        'ordinary_document_count', 'megathread_count', 'megathread_document_count')}))


if __name__ == '__main__':
    main()
