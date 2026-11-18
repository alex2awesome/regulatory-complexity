"""Resumable solar discovery and complete-comment retrieval; no geographic hard filter.

National solar discussions are retained even when their OP is outside California:
commenters can describe a different installation. Lexicon hits prioritize reading,
not decide jurisdiction or eligibility. API errors are recorded, never empty data.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import pathlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from functools import lru_cache

ROOT = pathlib.Path(__file__).resolve().parents[2]
API = "https://arctic-shift.photon-reddit.com/api"
UA = "Mozilla/5.0 (research; regulatory-complexity process recon)"
NATIONAL = ("solar", "TeslaSolar", "SolarDIY", "solarenergy", "SolarUSA", "Powerwall", "Solarbusiness", "enphase",
            "SunPower", "diySolar", "FranklinWH")
TOPICS = ("permit", "inspection", "PTO", "interconnection", "timeline", "California")
LOCAL = ("California", "bayarea", "sanfrancisco", "AskSF", "LosAngeles",
         "AskLosAngeles", "sandiego", "SanDiegan", "SanJose", "Sacramento",
         "orangecounty", "InlandEmpire", "Fresno", "Bakersfield", "Oakland",
         "Berkeley", "Davis", "SantaBarbara", "Ventura", "SantaCruz", "Monterey",
         "Humboldt", "Redding", "slo", "Sonoma", "Marin", "SanLuisObispo",
         "BayAreaRealEstate", "Fremont", "SantaRosa", "visalia", "Riverside", "Stockton", "Temecula",
    # Claude registry expansion 2026-09-23 (user: "cast far and wide"): recall only, never a location rule.
    "LongBeach",
    "Pasadena",
    "glendale",
    "burbank",
    "santaclarita",
    "SanFernandoValley",
    "SantaMonica",
    "Torrance",
    "AntelopeValley",
    "HighDesert",
    "Irvine",
    "HuntingtonBeach",
    "anaheim",
    "Murrieta",
    "PalmSprings",
    "coachellavalley",
    "Redlands",
    "SanBernardino",
    "Escondido",
    "oceanside",
    "carlsbad",
    "ChulaVista",
    "NorthCounty",
    "Modesto",
    "merced",
    "chico",
    "Roseville",
    "ElkGrove",
    "Folsom",
    "Vacaville",
    "napa",
    "Petaluma",
    "Livermore",
    "Pleasanton",
    "WalnutCreek",
    "Concord",
    "Hayward",
    "SanLeandro",
    "Vallejo",
    "Alameda",
    "EastBay",
    "SanMateo",
    "PaloAlto",
    "MountainView",
    "sunnyvale",
    "Cupertino",
    "SantaClara",
    "Salinas",
    "Tahoe",
    "Truckee",
    "GrassValley",
    "Lodi",
    "Tracy",
    "Manteca",
    "Turlock",
    "mendocino",
    "SantaMaria",
    "oxnard",
    "ThousandOaks",
    "simivalley",
    "Camarillo",
    "norcal",
    "socal",
    "CentralValley",
    "centralcoast",
)
GENERAL = ("homeowners", "HomeImprovement", "DIY", "AskElectricians", "electricians",
           "electrical", "Roofing", "FirstTimeHomeBuyer", "AskRealEstateAgents",
           "BuildingCodes", "Construction", "ElectricalEngineering", "homebuilding",
           "energy", "HOA", "fuckHOA", "RenewableEnergy", "OffGrid",
    # Claude registry expansion 2026-09-23 (user: "cast far and wide"): recall only, never a location rule.
    "personalfinance",
    "legaladvice",
    "RealEstate",
    "realestateinvesting",
    "Landlord",
    "teslamotors",
    "electricvehicles",
    "evcharging",
    "HVAC",
    "heatpumps",
    "Insurance",
    "Scams",
    "ADU",
    "Contractor",
    "solarpanels",
    "SolarCity",
    "sunrun",
    "EnergyStorage",
)
# Local applicants may describe batteries or permission to operate without the
# word solar. These are recall queries; none is an eligibility or location rule.
LOCAL_RECALL_TERMS = ("solar", "photovoltaic", "Powerwall", "PTO",
    # Claude registry expansion 2026-09-23 (user: "cast far and wide"): recall only, never a location rule.
    "net metering",
    "interconnection",
)
PROCESS_CLUES = re.compile(r"\b(?:permit\w*|inspec\w*|pto|permission to operate|"
                          r"interconnect\w*|hoa|approv\w*|plan check|paperwork|"
                          r"bureaucr\w*|timeline|wait\w*|finally|city|county|utility|"
                          r"solarapp\w*|resubmit\w*|red tag|green tag|setback\w*)\b", re.I)
BURDEN_PRIORITY = re.compile(r"\b(?:permit\w*|inspec\w*|pto|permission to operate|"
    r"interconnect\w*|approv\w*|plan check|paperwork|timeline|delay\w*|"
    r"install\w*|contractor|solarapp\w*|resubmit\w*|red tag|green tag)\b", re.I)
CLUES = {
    "california": r"\b(california|calif|nor\s*cal|so\s*cal|cali)\b",
    "weak_geographic_abbreviation": r"\b(?:CA|SF|LA)\b",
    "pge": r"\b(?:pg\s*&(?:amp;)?\s*e|pge|pacific gas)\b",
    "sce": r"\b(?:sce|southern california edison)\b",
    "sdge": r"\b(?:sdg\s*&(?:amp;)?\s*e|sdge|san diego gas)\b",
    "ladwp": r"\b(?:ladwp|los angeles department of water)\b",
    "smud": r"\b(?:smud|sacramento municipal utility)\b",
    "california_community_energy": r"\b(?:silicon valley clean energy|east bay community energy|"
        r"ava community energy|redwood coast energy authority|san diego community power|"
        r"clean power alliance|marin clean energy)\b",
    "california_agencies": r"\b(?:cslb|cpuc|cec|california energy commission)\b",
    "nem_transition": r"\bnem\s*[23](?:\.0)?\b",
    "cities": r"\b(?:san francisco|los angeles|san diego|san jose|sacramento|"
              r"oakland|berkeley|fresno|bakersfield|san bernardino|riverside|"
              r"vallejo|palo alto|san mateo|santa clara|orange county|bay area)\b",
}


@lru_cache(maxsize=1)
def place_lexicon():
    """Recall-oriented county/AHJ names, NOT a jurisdiction assignment rule."""
    names = set()
    panel = ROOT / "runs/solar_panel_20260920/panel_v1.csv"
    with panel.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["owner_kind"] == "ahj":
                name = re.sub(r"\s+(?:city|town|County)$", "", row["owner_name"], flags=re.I)
                if len(name) >= 4:
                    names.add(name)
    # Include counties absent from the administrative panel too. Place names
    # such as Orange remain weak recall clues, never a hard location assignment.
    with (ROOT / "corpus/counties/ca_counties_covariates.csv").open(newline="", encoding="utf-8") as handle:
        names.update(r["county"] for r in csv.DictReader(handle))
    return re.compile(r"\b(?:" + "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True)) + r")\b", re.I)


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def query_specs():
    queries = [(s, q) for s in NATIONAL for q in TOPICS]
    queries += [(s, q) for s in LOCAL for q in LOCAL_RECALL_TERMS]
    queries += [(s, "solar") for s in GENERAL]
    queries += [(s, "solar " + q) for s in GENERAL for q in ("permit", "inspection", "PTO")]
    return queries


def flatten(tree):
    out = []
    for node in tree:
        d = node.get("data", node)
        if node.get("kind") == "more":
            continue
        out.append({k: d[k] for k in ("id", "link_id", "parent_id", "subreddit",
                                      "author", "author_flair_text", "body", "created_utc", "score") if k in d})
        kids = d.get("replies") or node.get("children") or []
        if isinstance(kids, dict):
            kids = kids.get("data", {}).get("children", [])
        out.extend(flatten(kids))
    return out


def collapsed_comment_ids(value):
    """Keep archive pagination gaps visible instead of silently calling them read."""
    if isinstance(value, dict):
        if value.get("kind") == "more":
            return value.get("data", value).get("children", ["unknown_collapsed_block"])
        return [ident for child in value.values() for ident in collapsed_comment_ids(child)]
    if isinstance(value, list):
        return [ident for child in value for ident in collapsed_comment_ids(child)]
    return []


def clues(post, comments=()):
    text = "\n".join([post.get(k) or "" for k in
                      ("title", "selftext", "author_flair_text", "link_flair_text")]
                      + [(c.get("body") or "") + "\n" + (c.get("author_flair_text") or "") for c in comments])
    hits = [key for key, pattern in CLUES.items() if re.search(pattern, text, re.I)]
    if post.get("subreddit", "").lower() in {s.lower() for s in LOCAL}:
        hits.append("local_subreddit")
    if place_lexicon().search(text):
        # Some names (e.g. Orange, Paradise) are ambiguous ordinary words.
        # Preserve these weak hits for reading; never hard-assign a city.
        hits.append("weak_ahj_name_lexicon")
    return hits


class Collector:
    def __init__(self, out, pause):
        self.out, self.pause, self.last = out, pause, 0.0
        self.requests = 0

    def get(self, path, params):
        cooldown_path = self.out / "api_cooldown.json"
        if cooldown_path.exists():
            cooldown = json.loads(cooldown_path.read_text())
            if time.time() < cooldown["retry_not_before_epoch"]:
                raise RuntimeError("HTTP 429 cooldown: retry no earlier than " + cooldown["retry_not_before_utc"])
        url = API + path + "?" + urllib.parse.urlencode(params)
        time.sleep(max(0., self.pause - (time.monotonic() - self.last)))
        self.last = time.monotonic()
        self.requests += 1
        stamp = dt.datetime.now(dt.timezone.utc).isoformat()
        request = urllib.request.Request(url, headers={"User-Agent": UA})
        key = hashlib.sha256(url.encode()).hexdigest()[:20]
        try:
            with urllib.request.urlopen(request, timeout=35) as handle:
                payload = handle.read()
                status = handle.status
            payload_hash = hashlib.sha256(payload).hexdigest()
            raw = self.out / "responses" / (key + "_" + payload_hash[:12] + ".json")
            raw.parent.mkdir(parents=True, exist_ok=True)
            if not raw.exists():
                raw.write_bytes(payload)
            data = json.loads(payload)
            if "error" in data or not isinstance(data.get("data"), list):
                raise RuntimeError(str(data)[:300])
            self.log({"time": stamp, "url": url, "http_status": status,
                      "response": str(raw.relative_to(ROOT)), "count": len(data["data"]),
                      "sha256": hashlib.sha256(payload).hexdigest()})
            return data["data"]
        except Exception as exc:
            if isinstance(exc, urllib.error.HTTPError):
                if exc.code == 429:
                    seconds = exc.headers.get("X-RateLimit-Reset") or exc.headers.get("Retry-After")
                    try:
                        delay = max(60., float(seconds))
                    except (TypeError, ValueError):
                        delay = 300.
                    retry = time.time()+delay
                    dump(cooldown_path, dict(retry_not_before_epoch=retry,
                        retry_not_before_utc=dt.datetime.fromtimestamp(retry, dt.timezone.utc).isoformat(),
                        response_headers=dict(exc.headers),
                        fallback_assumption="300-second pause when numeric server retry/reset header is unavailable"))
                detail = exc.read().decode("utf-8", errors="replace")[:500]
                exc = RuntimeError(f"HTTP {exc.code}: {detail}")
            self.log({"time": stamp, "url": url, "status": "blocked_or_error",
                      "error": str(exc)[:400]})
            raise exc

    def log(self, row):
        self.out.mkdir(parents=True, exist_ok=True)
        with (self.out / "requests.jsonl").open("a") as handle:
            handle.write(json.dumps(row) + "\n")

    def frontier(self):
        path = self.out / "query_frontier.json"
        if path.exists():
            return json.loads(path.read_text())
        queries = query_specs()
        result = [{"subreddit": s, "query": q, "after": "2015-01-01",
                   "before": "2026-09-23", "status": "pending", "pages": 0,
                   "returned_rows": 0} for s, q in queries]
        dump(path, result)
        return result

    def extend_history(self):
        """Declare pre-2015 coverage without relabeling a previous search complete.

        Keep listing page counters (comment page filenames depend on them),
        archive each prior frontier, and reopen only exhausted lower boundaries.
        No network request is made by this migration.
        """
        start = "2005-01-01"
        def epoch(value):
            return int(value) if str(value).isdigit() else int(
                dt.datetime.fromisoformat(str(value)).replace(tzinfo=dt.timezone.utc).timestamp())
        changes = []
        for filename in ("national_listing_frontier.json", "national_comment_frontier.json"):
            path = self.out / filename
            if not path.exists():
                continue
            raw = path.read_bytes()
            frontier = json.loads(raw)
            dump(self.out / "frontier_history" / (filename[:-5]+"_"+hashlib.sha256(raw).hexdigest()[:16]+".json"), frontier)
            for query in frontier:
                if epoch(query["after"]) <= epoch(start):
                    continue
                old = {k: query[k] for k in ("after", "before", "status", "pages", "returned_rows")}
                query.setdefault("coverage_extensions", []).append(dict(
                    previous_window=old, extended_at=dt.datetime.now(dt.timezone.utc).isoformat()))
                if query["status"] == "exhausted":
                    query["before"] = epoch(query["after"]) + 1
                    query["status"] = "pending"
                query["after"] = start
                changes.append(dict(frontier=filename, subreddit=query["subreddit"], previous=old))
            dump(path, frontier)
        frontier = self.frontier()
        raw = json.dumps(frontier, sort_keys=True).encode()
        dump(self.out / "frontier_history" / ("query_"+hashlib.sha256(raw).hexdigest()[:16]+".json"), frontier)
        for subreddit, query in query_specs():
            if any(q["subreddit"].lower() == subreddit.lower() and q["query"].lower() == query.lower()
                   and epoch(q["after"]) <= epoch(start) for q in frontier):
                continue
            frontier.append(dict(subreddit=subreddit, query=query, after=start,
                before="2015-01-01T00:00:01", status="pending", pages=0,
                returned_rows=0, coverage_window="pre2015_historical_extension"))
            changes.append(dict(frontier="query_frontier.json", subreddit=subreddit, query=query))
        dump(self.out / "query_frontier.json", frontier)
        print(json.dumps({"historical_extension_changes": len(changes),
                          "earliest_requested_date": start, "network_requests": 0}), flush=True)

    def refine(self):
        """Keep receipts and split timed-out date spans, rather than retrying forever.

        Arctic Shift documents narrower dates/smaller limits for timeouts. Child
        windows overlap by one second; post IDs deduplicate that overlap. A
        refined parent is not exhausted until all descendants are exhausted.
        """
        frontier = self.frontier()
        before = json.dumps(frontier, sort_keys=True).encode()
        dump(self.out / "frontier_history" / (hashlib.sha256(before).hexdigest()[:16]+".json"), frontier)
        queries = query_specs()
        known = {(q["subreddit"].lower(), q["query"].lower()) for q in frontier}
        for subreddit, query in queries:
            if (subreddit.lower(), query.lower()) not in known:
                frontier.append(dict(subreddit=subreddit, query=query, after="2015-01-01",
                    before="2026-09-23", status="pending", pages=0, returned_rows=0))
        def seconds(value):
            if str(value).isdigit():
                return int(value)
            return int(dt.datetime.fromisoformat(str(value)).replace(tzinfo=dt.timezone.utc).timestamp())
        children = []
        for index, query in enumerate(frontier):
            if query["status"] != "blocked" or "Timeout" not in query.get("error", ""):
                continue
            low, high = seconds(query["after"]), seconds(query["before"])
            if high-low <= 31*86400:
                continue  # A bounded unresolved gap, not an endless retry loop.
            width = min(366*86400, (high-low)//2)
            cursor = high
            while cursor > low:
                start = max(low, cursor-width)
                children.append(dict(subreddit=query["subreddit"], query=query["query"],
                    after=max(low, start-1), before=cursor, status="pending", pages=0,
                    returned_rows=0, limit=25, refined_parent=index))
                cursor = start
            query["status"] = "refined_to_subwindows"
        frontier.extend(children)
        dump(self.out / "query_frontier.json", frontier)
        self.summary()

    def posts(self):
        candidates = {}
        for directory in (ROOT / "corpus/realworld/solar_permit/reddit/posts",
                          ROOT / "runs/solar_forum_20260922/reddit_discovery/posts",
                          self.out / "discovered_posts", self.out / "national_posts"):
            for p in sorted(directory.glob("*.json")):
                row = json.loads(p.read_bytes().decode("utf-8"))
                if isinstance(row, dict) and row.get("id"):
                    candidates.setdefault(row["id"], (row, p))
        return candidates

    def seed(self, files, budget):
        """Resolve concrete web/cross-link leads without treating snippets as cases."""
        manifest = self.out / "seed_leads.json"
        leads = json.loads(manifest.read_bytes()) if manifest.exists() else {}
        for path in files:
            pattern = r"(?:reddit\.com/(?:r/[^/\s\"<>]+/)?comments/|redd\.it/)([a-z0-9]+)"
            for post_id in {x.lower() for x in re.findall(pattern, path.read_text(), re.I)}:
                item = leads.setdefault(post_id, {"sources": [], "status": "pending"})
                source = str(path.resolve().relative_to(ROOT))
                if source not in item["sources"]:
                    item["sources"].append(source)
        held = self.posts()
        for post_id in set(leads) & set(held):
            leads[post_id]["status"] = "post_already_held"
        pending = [post_id for post_id, item in leads.items()
                   if item["status"] in {"pending", "lookup_error"}]
        dump(manifest, leads)
        for start in range(0, len(pending), 500):
            if self.requests >= budget:
                break
            batch = pending[start:start+500]
            try:
                rows = self.get("/posts/ids", {"ids": ",".join(batch)})
            except Exception as exc:
                for post_id in batch:
                    leads[post_id].update(status="lookup_error", error=str(exc)[:400])
                dump(manifest, leads)
                break
            found = {row["id"] for row in rows}
            for row in rows:
                target = self.out / "discovered_posts" / (row["id"]+".json")
                if not target.exists():
                    dump(target, row)
            for post_id in batch:
                leads[post_id]["status"] = "post_fetched" if post_id in found else "not_returned_by_archive"
            dump(manifest, leads)
        print("web-seed", dict(Counter(x["status"] for x in leads.values())), flush=True)
        self.summary()

    def list_national(self, budget):
        """Enumerate national venues without expensive server full-text scans.

        Every returned post enters the comment queue. Broad local topic and
        California clues prioritize retrieval, never exclude a discussion:
        relevant California accounts may occur only in replies to a generic OP.
        This is an additional finite frontier, not a completeness certificate.
        """
        path = self.out / "national_listing_frontier.json"
        frontier = json.loads(path.read_text()) if path.exists() else [
            dict(subreddit=s, after="2015-01-01", before="2026-09-23",
                 status="pending", pages=0, returned_rows=0) for s in NATIONAL]
        known = {q["subreddit"].lower() for q in frontier}
        frontier.extend(dict(subreddit=s, after="2015-01-01", before="2026-09-23",
            status="pending", pages=0, returned_rows=0) for s in NATIONAL if s.lower() not in known)
        # One page per venue each round: r/solar must not spend the entire
        # request budget before the other national communities get a turn.
        attempted_failures = set()
        while self.requests < budget:
            eligible = [q for q in frontier
                        if q["status"] in {"pending", "paging", "blocked"}
                        and q["subreddit"] not in attempted_failures]
            if not eligible:
                break
            for query in sorted(eligible, key=lambda q: q["pages"]):
                if self.requests >= budget:
                    break
                try:
                    rows = self.get("/posts/search", {k: query[k] for k in
                        ("subreddit", "after", "before")} | {"limit": "auto", "sort": "desc"})
                except Exception as exc:
                    query.update(status="blocked", error=str(exc)[:400])
                    dump(path, frontier)
                    if "429" in str(exc):
                        self.summary()
                        return
                    attempted_failures.add(query["subreddit"])
                    continue
                query["pages"] += 1
                query["returned_rows"] += len(rows)
                promoted = 0
                for row in rows:
                    retained = self.out / "national_posts" / (row["id"]+".json")
                    if not retained.exists():
                        dump(retained, row)
                    text = (row.get("title") or "")+"\n"+(row.get("selftext") or "")
                    if PROCESS_CLUES.search(text) or clues(row):
                        candidate = self.out / "discovered_posts" / (row["id"]+".json")
                        if not candidate.exists():
                            dump(candidate, row)
                            promoted += 1
                # With limit=auto, page size varies; only zero results exhaust.
                if not rows:
                    query["status"] = "exhausted"
                else:
                    # Preserve equal-second boundary posts just as the comment
                    # and topical frontiers do; stalled ties are explicit gaps.
                    cursor = min(int(r["created_utc"]) for r in rows)+1
                    if str(cursor) == str(query["before"]):
                        query["status"] = "cursor_stalled_needs_tie_review"
                    else:
                        query.update(before=cursor, status="paging")
                dump(path, frontier)
                print("national-list", query["subreddit"], query["pages"], len(rows),
                      "new-candidates", promoted, query["status"], flush=True)
        self.summary()

    def discover(self, budget):
        frontier = self.frontier()
        # Fairness is by venue, not filename order or number of split windows.
        # A large national query must not consume a pass before local venues get
        # any attempt. Carry attempts across invocations: resetting this counter
        # after each rate-limit stop starves later/new venues indefinitely.
        # The request log counts failed attempts too, unlike frontier.pages.
        # A failed query is attempted at most once in this pass.
        attempted_failures = set()
        attempts_by_venue = Counter()
        request_log = self.out / "requests.jsonl"
        if request_log.exists():
            for line in request_log.read_text().splitlines():
                record = json.loads(line)
                parsed = urllib.parse.urlparse(record.get("url", ""))
                params = urllib.parse.parse_qs(parsed.query)
                if parsed.path.endswith("/posts/search") and "query" in params:
                    venue = params.get("subreddit", [""])[0].lower()
                    if venue:
                        attempts_by_venue[venue] += 1
        while self.requests < budget:
            eligible = [(i, q) for i, q in enumerate(frontier)
                        if q["status"] in {"pending", "paging", "blocked"}
                        and i not in attempted_failures]
            if not eligible:
                break
            index, query = min(eligible, key=lambda item: (
                attempts_by_venue[item[1]["subreddit"].lower()],
                item[1]["status"] == "blocked", item[1]["pages"], item[0]))
            attempts_by_venue[query["subreddit"].lower()] += 1
            try:
                limit = query.get("limit", 100)
                rows = self.get("/posts/search", {k: query[k] for k in
                    ("subreddit", "query", "after", "before")} | {"limit": limit, "sort": "desc"})
            except Exception as exc:
                query["status"], query["error"] = "blocked", str(exc)[:300]
                attempted_failures.add(index)
                dump(self.out / "query_frontier.json", frontier)
                if "429" in str(exc) or "Too many requests" in str(exc):
                    self.summary()
                    return
                continue
            query["pages"] += 1
            query["returned_rows"] += len(rows)
            for row in rows:
                p = self.out / "discovered_posts" / (row["id"] + ".json")
                if not p.exists():
                    dump(p, row)
            if not rows:
                query["status"] = "exhausted"
            else:
                cursor = min(int(r["created_utc"]) for r in rows)+1
                if str(cursor) == str(query["before"]):
                    query["status"] = "cursor_stalled_needs_tie_review"
                else:
                    query["before"] = cursor
                    query["status"] = "paging"
            dump(self.out / "query_frontier.json", frontier)
            print("discovery", query["subreddit"], query["query"], query["pages"],
                  query["returned_rows"], query["status"], flush=True)
        self.summary()

    def list_comments(self, budget):
        """Batch national comment rows before topic/location filtering.

        These are partial dated windows, not complete thread captures. Grouping
        retains parent/link IDs and raw receipts. Tree retrieval still resolves
        priority stories and missing parents; this mode never overwrites a tree.
        """
        path = self.out / "national_comment_frontier.json"
        frontier = json.loads(path.read_bytes()) if path.exists() else [
            dict(subreddit=s, after="2015-01-01", before="2026-09-23",
                 status="pending", pages=0, returned_rows=0) for s in NATIONAL]
        known = {q["subreddit"].lower() for q in frontier}
        frontier.extend(dict(subreddit=s, after="2015-01-01", before="2026-09-23",
            status="pending", pages=0, returned_rows=0) for s in NATIONAL if s.lower() not in known)
        failures = set()
        while self.requests < budget:
            eligible = [q for q in frontier if q["status"] in {"pending", "paging", "blocked"}
                        and q["subreddit"] not in failures]
            if not eligible:
                break
            for query in sorted(eligible, key=lambda q: q["pages"]):
                if self.requests >= budget:
                    break
                params = {k: query[k] for k in ("subreddit", "after", "before")}
                params.update(limit="auto", sort="desc",
                    fields="id,link_id,parent_id,subreddit,author,author_flair_text,body,created_utc,retrieved_on,score")
                try:
                    rows = self.get("/comments/search", params)
                except Exception as exc:
                    query.update(status="blocked", error=str(exc)[:400])
                    failures.add(query["subreddit"])
                    dump(path, frontier)
                    if "429" in str(exc):
                        self.summary()
                        return
                    continue
                page_number = query["pages"]+1
                page = self.out / "national_comment_pages" / query["subreddit"] / f"page_{page_number:07d}.json"
                # A crash before the frontier write can replay this page. Keep
                # its first capture and bind any changed response separately.
                value = dict(schema_version="solar-national-comment-page/1",
                    request=params, comments=rows, retrieved_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                    completeness="Partial dated comment window, not a complete thread or a parsed episode.")
                if page.exists():
                    suffix = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()[:12]
                    page = page.with_name(page.stem+"_replay_"+suffix+".json")
                dump(page, value)
                query["pages"] = page_number
                query["returned_rows"] += len(rows)
                if not rows:
                    query["status"] = "exhausted"
                else:
                    # One-second overlap protects equal-timestamp boundary rows.
                    # If all of a second cannot be enumerated, expose the gap.
                    cursor = min(int(r["created_utc"]) for r in rows)+1
                    if str(cursor) == str(query["before"]):
                        query["status"] = "cursor_stalled_needs_tie_review"
                    else:
                        query.update(before=cursor, status="paging")
                dump(path, frontier)
                print("national-comments", query["subreddit"], page_number, len(rows), query["status"], flush=True)
        self.summary()

    def resolve_ties(self, budget):
        """Resolve a stalled one-second overlap without skipping tied records.

        A fixed-size narrow timestamp query, unlike limit=auto, distinguishes
        an enumerated boundary from a saturated boundary requiring more work.
        This does not declare exhaustion; the next ordinary older-page request
        must return zero before its finite date frontier is exhausted.
        """
        families=(("national_listing_frontier.json","/posts/search","national_posts"),
                  ("query_frontier.json","/posts/search","discovered_posts"),
                  ("national_comment_frontier.json","/comments/search",None))
        for filename,endpoint,post_directory in families:
            path=self.out/filename
            if not path.exists():
                continue
            frontier=json.loads(path.read_bytes())
            for query in frontier:
                if self.requests>=budget:
                    self.summary(); return
                if query["status"]!="cursor_stalled_needs_tie_review":
                    continue
                boundary=int(query["before"])-1
                params={"subreddit":query["subreddit"],"after":boundary-1,
                        "before":boundary+1,"limit":100,"sort":"desc"}
                if "query" in query:
                    params["query"]=query["query"]
                try:
                    rows=self.get(endpoint,params)
                except Exception as exc:
                    query["tie_resolution_error"]=str(exc)[:400]
                    dump(path,frontier)
                    if "429" in str(exc):
                        self.summary(); return
                    continue
                key=hashlib.sha256((filename+json.dumps(params,sort_keys=True)).encode()).hexdigest()[:20]
                receipt=(self.out/"timestamp_boundary_checks"/(key+".json") if post_directory
                         else self.out/"national_comment_pages"/query["subreddit"]/("tie_"+key+".json"))
                content={"schema_version":"solar-timestamp-boundary-check/1",
                    "request":params,"endpoint":endpoint,"frontier":filename,
                    "retrieved_at":dt.datetime.now(dt.timezone.utc).isoformat(),
                    "comments" if post_directory is None else "posts":rows,
                    "qualification":"Narrow boundary enumeration only, not a complete thread or internet exhaustion."}
                if receipt.exists():
                    suffix=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()[:12]
                    receipt=receipt.with_name(receipt.stem+"_replay_"+suffix+receipt.suffix)
                dump(receipt,content)
                if post_directory:
                    for row in rows:
                        target=self.out/post_directory/(row["id"]+".json")
                        if not target.exists():
                            dump(target,row)
                query.setdefault("timestamp_boundary_checks",[]).append({
                    "boundary":boundary,"returned_rows":len(rows),"limit":100,
                    "receipt":str(receipt),"previous_before":query["before"]})
                query["returned_rows"]+=len(rows)
                if len(rows)<100:
                    query.update(before=boundary,status="paging")
                else:
                    query["status"]="timestamp_boundary_saturated_unresolved"
                dump(path,frontier)
                print("timestamp-boundary",filename,query["subreddit"],len(rows),query["status"],flush=True)
        self.summary()

    def comments(self, budget):
        posts = self.posts()
        failures_path = self.out / "comment_fetch_failures.json"
        failures = json.loads(failures_path.read_text()) if failures_path.exists() else {}
        seeds_path = self.out / "seed_leads.json"
        seeds = json.loads(seeds_path.read_bytes()) if seeds_path.exists() else {}
        consecutive_errors = 0
        # Relevance prioritizes retrieval; never removes an out-of-state OP's commenters.
        # A single repeatedly failing tree must not starve all other discussions.
        # 2026-09-23 (Claude, user asked to cast wide for California): order only,
        # never exclusion. Burden AND California-clue posts first, then posts from
        # registered California/local communities, then burden-only, then clue-only.
        local_names = {s.lower() for s in LOCAL}
        def priority(item):
            post = item[1][0]
            burden = bool(BURDEN_PRIORITY.search((post.get("title") or "")+"\n"+(post.get("selftext") or "")))
            clue = bool(clues(post))
            local = (post.get("subreddit") or "").lower() in local_names
            return (item[0] in failures,
                    not any("manual_web_leads" in source or "venue_expansion" in source
                            for source in seeds.get(item[0], {}).get("sources", [])),
                    item[0] not in seeds, -(burden and clue), -local, -burden, -clue, item[0])
        ordered = sorted(posts.items(), key=priority)
        for post_id, (post, source) in ordered:
            path = self.out / "posts" / (post_id + ".json")
            if path.exists():
                continue
            if self.requests >= budget:
                break
            try:
                tree = self.get("/comments/tree", {"link_id": "t3_" + post_id, "limit": 9999})
                comments = flatten(tree)
                collapsed = collapsed_comment_ids(tree)
            except Exception as exc:
                consecutive_errors += 1
                previous = failures.get(post_id, {})
                failures[post_id] = dict(attempts=previous.get("attempts", 0)+1,
                    error=str(exc)[:400], last_attempt=dt.datetime.now(dt.timezone.utc).isoformat())
                dump(failures_path, failures)
                if "429" in str(exc) or consecutive_errors >= 3:
                    self.summary()
                    return
                continue
            consecutive_errors = 0
            if post_id in failures:
                del failures[post_id]
                dump(failures_path, failures)
            unique = {c.get("id", str(i)): c for i, c in enumerate(comments)}
            dump(path, {"schema_version": "solar-thread-capture/1", "post": post,
                        "post_source": str(source.relative_to(ROOT)), "comments": list(unique.values()),
                        "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "california_screening_clues": clues(post, comments),
                        "comment_status": "archive_tree_partial" if collapsed else "archive_tree_returned",
                        "collapsed_comment_ids": collapsed,
                        "declared_num_comments": post.get("num_comments"),
                        "returned_comment_count": len(unique),
                        "limit_reached": len(comments) >= 9999,
                        "completeness_note": "Archive tree, not a guarantee of deleted/live Reddit completeness."})
            print("comments", post_id, len(unique), "declared", post.get("num_comments"), flush=True)
        self.summary()

    def summary(self):
        posts = self.posts()
        captures = list((self.out / "posts").glob("*.json"))
        rows = [json.loads(p.read_text()) for p in captures]
        frontier_path = self.out / "query_frontier.json"
        frontier = json.loads(frontier_path.read_text()) if frontier_path.exists() else []
        value = {"generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                 "logical_posts_held": len(posts), "archive_comment_trees": len(captures),
                 "comment_records": sum(r["returned_comment_count"] for r in rows),
                 "threads_with_california_clues": sum(bool(r["california_screening_clues"]) for r in rows),
                 "trees_with_explicit_collapsed_gaps": sum(bool(r.get("collapsed_comment_ids")) for r in rows),
                 "comment_fetch_pending": len(set(posts) - {p.stem for p in captures}),
                 "query_status": dict(Counter(q["status"] for q in frontier)),
                 "internet_exhaustive": False,
                 "national_queue_policy": "Every enumerated national post queued; topic/geography clues prioritize only, never exclude commenters.",
                 "note": "All-held comment coverage and finite query-frontier exhaustion are separate from internet completeness."}
        listing = self.out / "national_listing_frontier.json"
        if listing.exists():
            value["national_posts_retained_before_topic_screen"] = len(list((self.out / "national_posts").glob("*.json")))
            value["national_listing_status"] = dict(Counter(q["status"] for q in json.loads(listing.read_text())))
        comment_listing = self.out / "national_comment_frontier.json"
        if comment_listing.exists():
            comment_frontier = json.loads(comment_listing.read_bytes())
            value["national_comment_batch_status"] = dict(Counter(q["status"] for q in comment_frontier))
            value["national_comment_batch_returned_rows_not_deduplicated"] = sum(q["returned_rows"] for q in comment_frontier)
            value["national_comment_batch_qualification"] = "Partial dated windows; overlaps not yet deduplicated; not additional complete trees or read cases."
        dump(self.out / "status.json", value)
        print(json.dumps(value), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("discover", "comments", "status", "refine", "extend_history", "list_national", "list_comments", "resolve_ties", "seed"))
    ap.add_argument("--out", type=pathlib.Path, default=ROOT / "runs/solar_forum_20260922/acquisition/forum")
    ap.add_argument("--request-budget", type=int, default=300)
    ap.add_argument("--pause", type=float, default=2.)
    ap.add_argument("--lead-file", type=pathlib.Path, action="append", default=[])
    args = ap.parse_args()
    c = Collector(args.out.resolve(), args.pause)
    if args.mode == "status":
        c.summary()
    elif args.mode == "refine":
        c.refine()
    elif args.mode == "extend_history":
        c.extend_history()
    elif args.mode == "seed":
        if not args.lead_file:
            ap.error("seed requires at least one --lead-file")
        c.seed(args.lead_file, args.request_budget)
    else:
        getattr(c, args.mode)(args.request_budget)


if __name__ == "__main__":
    main()
