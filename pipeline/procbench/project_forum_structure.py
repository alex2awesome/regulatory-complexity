"""Preserve forum speaker, quotation and signature boundaries from frozen HTML.

Writes public-source companions; does not extract claims or rewrite old artifacts.
The original HTML hash must match the existing freeze's origin receipt.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import tempfile

from bs4 import BeautifulSoup


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def project(raw):
    soup = BeautifulSoup(raw, 'html.parser')
    canonical = soup.select_one('link[rel="canonical"]')
    canonical_url = canonical.get('href') if canonical else None
    if not canonical_url:
        raise ValueError('No canonical URL for logical page identity')
    page_match = re.search(r'/page(\d+)(?:[/?#]|$)', canonical_url)
    logical_page = int(page_match[1]) if page_match else 1
    nav_pages = {int(n['data-page']) for n in soup.select('.js-pagenav-current-button[data-page]')}
    if nav_pages and nav_pages != {logical_page}:
        raise ValueError('Canonical URL and current-page navigation disagree')
    page_metadata = dict(canonical_url=canonical_url, logical_page=logical_page,
                         current_navigation_pages=sorted(nav_pages))
    posts = []
    for node in soup.select('li.js-post'):
        body = node.select_one('.js-post__content-text')
        if body is None:
            raise ValueError('Post container has no recognized body')
        author = node.select_one('[itemprop="author"]')
        time = node.select_one('time[itemprop="dateCreated"]')
        signature = node.select_one('.post-signature')
        body_html = str(body)
        own = BeautifulSoup(body_html, 'html.parser')
        quotations = []
        for quote in body.select('.bbcode_quote'):
            attribution = quote.select_one('.bbcode_postedby')
            message = quote.select_one('.message')
            by = attribution.select_one('strong') if attribution else None
            link = attribution.select_one('a[href]') if attribution else None
            quotations.append(dict(speaker=by.get_text(' ', strip=True) if by else None,
                attribution_text=attribution.get_text(' ', strip=True) if attribution else None,
                source_post_url=link.get('href') if link else None,
                text=(message or quote).get_text('\n', strip=True)))
        # Remove quotation regions only in the separate own-body view. All
        # quotation content remains present in body_text and quotations.
        for quote in own.select('.bbcode_quote'):
            quote.decompose()
        posts.append(dict(post_id=node.get('data-node-id'),
            author=author.get_text(' ', strip=True) if author else None,
            posted_at=time.get('datetime') if time else None,
            posted_at_display=time.get_text(' ', strip=True) if time else None,
            publish_timestamp_raw=node.get('data-node-publishdate'),
            body_text=body.get_text('\n', strip=True),
            own_body_text=own.get_text('\n', strip=True), quotations=quotations,
            signature_text=signature.get_text('\n', strip=True) if signature else None,
            signature_effective_date=None))
    if not posts:
        raise ValueError('No recognized posts; do not mark page projected')
    ids = [p['post_id'] for p in posts]
    if None in ids or len(ids) != len(set(ids)):
        raise ValueError('Missing or repeated source post IDs')
    return posts, page_metadata


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--threads', nargs='*')
    ap.add_argument('--repair-empty-outputs', action='store_true',
                    help='Archive zero-byte generated companions left by failed writes before retrying')
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    code_sha = digest(Path(__file__).read_bytes())
    done, failed = [], []
    for slice_name in ('calguns_a', 'calguns_g', 'calguns_q'):
        base = args.root / slice_name
        frozen = json.loads((base / 'frozen_index.json').read_text())
        origins = {d['doc_id']: d for d in frozen['documents']}
        index = json.loads((base / 'artifact_only_index.json').read_text())
        for item in index['documents']:
            doc_id = item['document_id']
            thread = re.fullmatch(r'calguns_(\d+)_page\d+(?:_.*)?', doc_id).group(1)
            if args.threads and thread not in args.threads:
                continue
            output = args.out / (doc_id + '.json')
            try:
                origin = origins[doc_id]
                raw_path = Path(origin['origin'])
                raw = raw_path.read_bytes()
                raw_sha = digest(raw)
                expected_raw_sha = origin.get('origin_sha256', origin.get('raw_sha256'))
                if expected_raw_sha is None or raw_sha != expected_raw_sha:
                    raise ValueError('Origin bytes differ from freeze')
                artifact_path = base / 'artifacts' / (doc_id + '.md')
                if digest(artifact_path.read_bytes()) != item['sha256']:
                    raise ValueError('Rendered artifact bytes differ from index')
                if output.exists() and output.stat().st_size == 0 and args.repair_empty_outputs:
                    archived = args.out / 'failed_empty_outputs' / output.name
                    archived.parent.mkdir(exist_ok=True)
                    if archived.exists():
                        raise ValueError('An empty-output archive already exists')
                    output.rename(archived)
                if output.exists():
                    prior = json.loads(output.read_text())
                    if (prior['origin_sha256'], prior['artifact_sha256']) != (raw_sha, item['sha256']):
                        raise ValueError('Existing companion has different lineage; use a new output directory')
                    if prior.get('schema_version') != 'forum-source-structure/1' or 'page_metadata' not in prior:
                        raise ValueError('Existing companion lacks required structure metadata')
                    done.append(dict(document_id=doc_id, posts=len(prior['posts']), resumed=True,
                                     projection_code_sha256=prior['projection_code_sha256']))
                    continue
                posts, page_metadata = project(raw)
                payload = dict(schema_version='forum-source-structure/1', document_id=doc_id,
                    source_slice=slice_name, source_path=str(raw_path), origin_sha256=raw_sha,
                    artifact_path=str(artifact_path), artifact_sha256=item['sha256'],
                    projection_code_sha256=code_sha, page_metadata=page_metadata, posts=posts,
                    limitations=['Posted date describes the post, not the mutable signature.',
                        'Quotation attribution is copied from HTML; it does not prove the original claim.',
                        'Application episodes and policy regimes still require semantic reconciliation.'])
                # Numeric HTML entities can decode into lone surrogate codepoints.
                # Escape them in JSON and finish encoding before creating an output;
                # preserve original bytes via the source receipt, not lossy replacement.
                encoded = (json.dumps(payload, indent=2, ensure_ascii=True) + '\n').encode('utf-8')
                with tempfile.NamedTemporaryFile(dir=args.out, prefix=doc_id + '.', suffix='.tmp', delete=False) as temp:
                    temp.write(encoded)
                    temporary_path = Path(temp.name)
                temporary_path.replace(output)
                done.append(dict(document_id=doc_id, posts=len(posts), resumed=False))
            except (ValueError, KeyError, OSError) as error:
                failed.append(dict(document_id=doc_id, error=str(error)))
                print(json.dumps(dict(failed_document=doc_id, error=str(error))), flush=True)
            if (len(done) + len(failed)) % 100 == 0:
                print(json.dumps(dict(completed=len(done), failed=len(failed))), flush=True)
    receipt = dict(schema_version='forum-structure-projection-receipt/1',
        completed_utc=datetime.now(timezone.utc).isoformat(),
        selected_threads=args.threads, documents_completed=len(done), documents_failed=len(failed),
        posts=sum(d['posts'] for d in done), documents=done, failures=failed,
        projection_code_sha256=code_sha, semantic_extraction_performed=False)
    label = '-'.join(args.threads) if args.threads else 'all'
    receipt_path = args.out / ('receipt_' + label + '.json')
    if receipt_path.exists():
        label += '_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
        receipt_path = args.out / ('receipt_' + label + '.json')
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ('documents_completed','documents_failed','posts')}), flush=True)
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
