#!/usr/bin/env python3
"""Shared append-only work log for the county scoping effort.

Two or more agents work the packets in docs/scoping/WORK_PACKETS.json at the
same time. Those packet definitions are stable and rarely edited. Everything
that changes — who is working on what, what was found, what is blocked — goes
here as one JSON object per line. JSONL is append-safe: concurrent writers
append whole lines and a crash costs at most one line, whereas a shared JSON
file corrupts.

Read the log before you start, and poll it while you work, so you pick up what
the other agent has found and do not duplicate it.

    # before starting anything
    python3 pipeline/recon/scoping_log.py tail -n 40
    python3 pipeline/recon/scoping_log.py status          # per-packet latest state

    # claim a packet, then work it
    python3 pipeline/recon/scoping_log.py claim P3-ADU-PROCESS-DOCS --by codex
    python3 pipeline/recon/scoping_log.py looking P3-ADU-PROCESS-DOCS \
        --note "HCD findings letters: trying hcd.ca.gov letters index"
    python3 pipeline/recon/scoping_log.py found P3-ADU-PROCESS-DOCS \
        --note "Sonoma County ADU page + ordinance" --url https://... --value "60-day ministerial, no pre-app"
    python3 pipeline/recon/scoping_log.py blocked P3-ADU-PROCESS-DOCS \
        --note "Colusa County site 403 to scripts" --url https://...
    python3 pipeline/recon/scoping_log.py done P3-ADU-PROCESS-DOCS \
        --note "48 of 58 counties; 10 have no ADU page" --output docs/scoping/2026-09-16-adu-58-counties.md

    # see only what someone else added since you last looked
    python3 pipeline/recon/scoping_log.py since 2026-09-16T18:30 --not-by fable

Entry kinds: claim, release, looking, found, blocked, question, note, done.
`looking` is the running list of what an agent is searching right now, so the
other agent can avoid the same query.
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sys

LOG = pathlib.Path(__file__).resolve().parents[2] / "docs/scoping/FINDINGS.jsonl"
KINDS = ("claim", "release", "looking", "found", "blocked", "question", "note", "done")


def _now() -> str:
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def append(kind: str, packet: str | None, by: str, note: str = "", url: str = "",
           value: str = "", output: str = "") -> dict:
    if kind not in KINDS:
        raise SystemExit("kind must be one of %s" % (KINDS,))
    entry = {"ts": _now(), "kind": kind, "by": by}
    for k, v in (("packet", packet), ("note", note), ("url", url), ("value", value), ("output", output)):
        if v:
            entry[k] = v
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:                     # one atomic-ish line append
        f.write(json.dumps(entry, sort_keys=False) + "\n")
    return entry


def read() -> list[dict]:
    if not LOG.exists():
        return []
    out = []
    for line in LOG.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:             # a torn line from a concurrent writer
            continue
    return out


def _fmt(e: dict) -> str:
    bits = [e["ts"], "%-8s" % e["kind"], "%-10s" % e.get("by", "?")]
    if e.get("packet"):
        bits.append("%-22s" % e["packet"])
    if e.get("note"):
        bits.append(e["note"])
    if e.get("value"):
        bits.append("= " + e["value"])
    if e.get("url"):
        bits.append("<" + e["url"] + ">")
    if e.get("output"):
        bits.append("-> " + e["output"])
    return "  ".join(bits)


def cmd_tail(a):
    rows = read()
    for e in rows[-a.n:]:
        print(_fmt(e))
    print("\n%d entries total" % len(rows))


def cmd_since(a):
    rows = [e for e in read() if e["ts"] >= a.ts]
    if a.not_by:
        rows = [e for e in rows if e.get("by") != a.not_by]
    if a.by:
        rows = [e for e in rows if e.get("by") == a.by]
    for e in rows:
        print(_fmt(e))
    print("\n%d entries since %s%s" % (len(rows), a.ts, (" excluding %s" % a.not_by) if a.not_by else ""))


def cmd_status(a):
    packets = {}
    manifest = LOG.parent / "WORK_PACKETS.json"
    if manifest.exists():
        for p in json.loads(manifest.read_text())["packets"]:
            packets[p["id"]] = dict(title=p["title"], priority=p["priority"], state="open",
                                    owner=None, found=0, blocked=0, looking=None, outputs=[])
    for e in read():
        pid = e.get("packet")
        if not pid:
            continue
        slot = packets.setdefault(pid, dict(title="(not in manifest)", priority=99, state="open",
                                            owner=None, found=0, blocked=0, looking=None, outputs=[]))
        if e["kind"] == "claim":
            slot["state"], slot["owner"] = "claimed", e.get("by")
        elif e["kind"] == "release":
            slot["state"], slot["owner"] = "open", None
        elif e["kind"] == "done":
            slot["state"] = "done"
            if e.get("output"):
                slot["outputs"].append(e["output"])
        elif e["kind"] == "found":
            slot["found"] += 1
        elif e["kind"] == "blocked":
            slot["blocked"] += 1
        elif e["kind"] == "looking":
            slot["looking"] = e.get("note", "")
    for pid, s in sorted(packets.items(), key=lambda kv: (kv[1]["priority"], kv[0])):
        line = "P%-2s %-24s %-8s" % (s["priority"], pid, s["state"])
        if s["owner"]:
            line += " owner=%-9s" % s["owner"]
        line += " found=%-3d blocked=%-2d" % (s["found"], s["blocked"])
        print(line)
        if s["state"] == "claimed" and s["looking"]:
            print("      now: %s" % s["looking"])
        for o in s["outputs"]:
            print("      -> %s" % o)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for kind in KINDS:
        p = sub.add_parser(kind)
        p.add_argument("packet", nargs="?")
        p.add_argument("--by", default="fable")
        p.add_argument("--note", default="")
        p.add_argument("--url", default="")
        p.add_argument("--value", default="")
        p.add_argument("--output", default="")
        p.set_defaults(fn=lambda a, k=kind: print(_fmt(append(k, a.packet, a.by, a.note, a.url, a.value, a.output))))
    t = sub.add_parser("tail"); t.add_argument("-n", type=int, default=30); t.set_defaults(fn=cmd_tail)
    s = sub.add_parser("since"); s.add_argument("ts"); s.add_argument("--by"); s.add_argument("--not-by", dest="not_by")
    s.set_defaults(fn=cmd_since)
    st = sub.add_parser("status"); st.set_defaults(fn=cmd_status)
    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
