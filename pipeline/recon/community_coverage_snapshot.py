"""Build a read-only community coverage snapshot from held Reddit trees."""
import ast, collections, datetime, json, pathlib
import glob

ROOT = pathlib.Path(__file__).resolve().parents[2]
COLLECTOR = ROOT / "pipeline/recon/solar_forum_collect.py"
POST_DIR = ROOT / "runs/solar_forum_20260922/acquisition/forum/posts"
MANIFEST = ROOT / "runs/solar_forum_20260922/queue_latest/reviewed_coverage_manifest.json"
STATUS = ROOT / "runs/solar_forum_20260922/acquisition/forum/status.json"
QUERY = ROOT / "runs/solar_forum_20260922/acquisition/forum/query_frontier.json"
LISTING = ROOT / "runs/solar_forum_20260922/acquisition/forum/national_listing_frontier.json"
COMMENTS = ROOT / "runs/solar_forum_20260922/acquisition/forum/national_comment_frontier.json"
OUT = ROOT / "runs/solar_forum_20260922/acquisition"

tree = ast.parse(COLLECTOR.read_text())
registry = []
for node in tree.body:
    if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in {"NATIONAL", "LOCAL", "GENERAL"}):
        registry.extend((node.targets[0].id, v) for v in ast.literal_eval(node.value))

held = collections.Counter()
comments = collections.Counter()
for path in sorted(POST_DIR.glob("*.json")):
    d = json.loads(path.read_text())
    post = d.get("post", {})
    key = post.get("subreddit", "").strip().lower()
    held[key] += 1
    comments[key] += len(d.get("comments", []))

manifest = json.loads(MANIFEST.read_text())
status_receipt = json.loads(STATUS.read_text())
query_frontier = json.loads(QUERY.read_text())
listing_frontier = json.loads(LISTING.read_text())
comment_frontier = json.loads(COMMENTS.read_text())
read_ids = {x.get("thread_id") for x in manifest.get("threads", [])}
query_by_venue = collections.defaultdict(list)
for item in query_frontier:
    query_by_venue[item.get("subreddit", "").lower()].append(item)
listing_by_venue = {x.get("subreddit", "").lower(): x for x in listing_frontier}
comment_by_venue = {x.get("subreddit", "").lower(): x for x in comment_frontier}
read_by_venue = collections.Counter()
for path in sorted(POST_DIR.glob("*.json")):
    if path.stem in read_ids:
        key = json.loads(path.read_text()).get("post", {}).get("subreddit", "").strip().lower()
        read_by_venue[key] += 1

def qcount(group):
    return 6 if group == "NATIONAL" else 4

rows = []
for group, venue in registry:
    key = venue.lower()
    n = held[key]
    qitems = query_by_venue[key]
    qstatus = collections.Counter(x.get("status", "unknown") for x in qitems)
    qrows = sum(x.get("returned_rows", 0) for x in qitems)
    listing = listing_by_venue.get(key)
    comment = comment_by_venue.get(key)
    rows.append({
        "community": venue, "registry_group": group, "registered_queries": qcount(group),
        "query_status": dict(qstatus) if qitems else {"not_in_frontier_receipt": 1},
        "query_returned_rows": qrows,
        "query_status_basis": "Actual query_frontier.json status counts; held trees are reported separately.",
        "pagination_status": ("archive_tree_returned per held source; subreddit frontier not certified." if n else
                              "no retained tree/page status in snapshot"),
        "national_listing_frontier": ({"status": listing.get("status"), "pages": listing.get("pages"), "returned_rows": listing.get("returned_rows")} if listing else None),
        "national_comment_frontier": ({"status": comment.get("status"), "pages": comment.get("pages"), "returned_rows": comment.get("returned_rows")} if comment else None),
        "held_unique_posts": n, "held_full_trees": n, "held_comments": comments[key],
        "read_full_trees": read_by_venue[key], "downloaded": n > 0,
        "fit_consumed_threads": None, "fit_status": "not_reportable_per_thread"
    })

registry_keys = {v.lower() for _, v in registry}
unregistered = [{"community": k, "held_unique_posts": v,
                "note": "Held cross-post or unrelated venue; not in collector registry."}
               for k, v in sorted(held.items()) if k not in registry_keys]
generated = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
out = {
    "schema_version": "solar-community-coverage/1", "generated_at": generated,
    "revision": {"supersedes_generated_at": "2026-09-22T17:41:32Z", "reason": "Corrected query_status to use actual frontier receipts; added 86034 logical-post accounting and refreshed 635-entry manifest intersection."},
    "snapshot_scope": "Collector registry joined to query_frontier, national listing/comment frontier receipts, status.json, current forum trees, and refreshed queue_latest reviewed manifest.",
    "registry_counts": {"NATIONAL": sum(g == "NATIONAL" for g, _ in registry), "LOCAL": sum(g == "LOCAL" for g, _ in registry), "GENERAL": sum(g == "GENERAL" for g, _ in registry), "total_communities": len(registry)},
    "query_plan": {"NATIONAL": "6 topic queries/community", "LOCAL": "4 recall-term queries/community", "GENERAL": "solar plus permit/inspection/PTO queries/community"},
    "collector_post_accounting": {"logical_posts_held": status_receipt.get("logical_posts_held"), "national_posts_retained_before_topic_screen": status_receipt.get("national_posts_retained_before_topic_screen"), "national_posts_metadata_files": len(list((OUT / "national_posts").glob("*.json"))), "discovery_posts_metadata_files": len(list((OUT / "discovered_posts").glob("*.json"))), "seed_lead_posts": len(json.loads((OUT / "forum/seed_leads.json").read_text()))},
    "held_tree_totals": {"archive_comment_trees": sum(held.values()), "unique_communities_casefolded": len(held), "comments": sum(comments.values()), "manifest_entries": len(read_ids), "manifest_reddit_entries_intersecting_held_trees": len(read_ids & {p.stem for p in POST_DIR.glob("*.json")}), "manifest_external_entries_not_in_tree_dir": len(read_ids - {p.stem for p in POST_DIR.glob("*.json")})},
    "frontier_status_totals": {"query_frontier": status_receipt.get("query_status"), "national_listing": status_receipt.get("national_listing_status"), "national_comment": status_receipt.get("national_comment_batch_status")},
    "fit_accounting": {"fit_consumed_threads": None, "reason": "Existing fits report packets/case identities, not per-community/thread consumption; read/download is not fit consumption.", "component_manifest": str(MANIFEST.relative_to(ROOT))},
    "communities": rows, "unregistered_held_communities": unregistered,
    "limitations": ["Query status is artifact-based, not a fresh API receipt; no held tree does not prove unqueried or absent.", "Retained trees are archive-tree returns, not an exhaustive subreddit pagination certificate.", "Downloaded, read, and fit/consumed remain separate fields."]
}
(OUT / "community_coverage_20260922.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
lines = ["# Community coverage snapshot", "", f"Generated: `{generated}` (UTC)", "", "Finite artifact-based snapshot, not an exhaustive internet certificate. Registry: 63 communities (11 national, 34 local, 18 general).", "", "## Counts", "", "- Registered plan: 6 national, 4 local, and 4 general queries per community.", f"- Collector logical posts held: {status_receipt.get('logical_posts_held')} (metadata/frontier accounting, not full-tree reads).", f"- National listing retained before topic screen: {status_receipt.get('national_posts_retained_before_topic_screen')}; archive trees: {sum(held.values())}; comments: {sum(comments.values())}.", f"- Refreshed manifest entries: {len(read_ids)} total; {len(read_ids & {p.stem for p in POST_DIR.glob('*.json')})} intersect held Reddit trees; {len(read_ids - {p.stem for p in POST_DIR.glob('*.json')})} older external entries.", "- Fit consumption is not assigned per community/thread; no read/download count is promoted to fit consumption.", "", "## Per-community table", "", "| Community | Group | Queries | Actual query status counts | National listing | National comments | Held trees | Comments | Read trees | Fit consumed |", "|---|---:|---:|---|---|---|---:|---:|---:|---|"]
for r in rows:
    ls = r['national_listing_frontier']['status'] if r['national_listing_frontier'] else '—'
    cs = r['national_comment_frontier']['status'] if r['national_comment_frontier'] else '—'
    lines.append(f"| {r['community']} | {r['registry_group']} | {r['registered_queries']} | {r['query_status']} | {ls} | {cs} | {r['held_full_trees']} | {r['held_comments']} | {r['read_full_trees']} | not reportable per thread |")
noheld = [r["community"] for r in rows if not r["held_unique_posts"]]
lines += ["", "## Interpretation", "", "Per-community query statuses come from `forum/query_frontier.json`; held trees are a separate artifact count. A community can have searched/refined/blocked/pending query windows without a retained tree. The 13 registered communities with zero retained trees in this snapshot are: " + ", ".join(noheld) + ". Their actual frontier status counts remain in the JSON table; this is not an absence claim.", "", "National listing/comment pagination is reported from the dedicated frontier receipts. Collector logical posts (86,034) and metadata-only national/discovery/seed inventories must not be conflated with 2,621 archived comment trees or 632 refreshed-manifest Reddit reads.", "", "Cross-post/unrelated held venues are preserved in JSON under `unregistered_held_communities`."]
(OUT / "community_coverage_20260922.md").write_text("\n".join(lines) + "\n")
