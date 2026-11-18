"""Merge the two reviewed SOLAR episode packets after root adoption."""
from __future__ import annotations

import hashlib, json
from pathlib import Path

from .solar_sources import ROOT

ROOT_PACKET = ROOT / "runs/solar_forum_20260922/parse/reviewed_root001.json"
SOL_PACKET = ROOT / "runs/solar_forum_20260922/model_bridge/parse/reviewed_sol001.json"
OUT = ROOT / "runs/solar_forum_20260922/model_bridge/parse/reviewed_combined001.json"
RECEIPT = ROOT / "runs/solar_forum_20260922/model_bridge/parse/reviewed_combined001_receipt.json"


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUT.exists() or RECEIPT.exists():
        raise ValueError("combined packet paths are write-once")
    left, right = json.loads(ROOT_PACKET.read_text()), json.loads(SOL_PACKET.read_text())
    if left["jurisdictions"] != right["jurisdictions"]:
        raise ValueError("candidate universes differ")
    adopted_right = json.loads(json.dumps(right))
    adopted_right["root_adopted"] = True
    for episode in adopted_right["episodes"]: episode["root_adopted"] = True
    episodes = left["episodes"] + adopted_right["episodes"]
    ids = [e["episode_id"] for e in episodes]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate episode ID across packets")
    author_keys = [(e.get("thread_id"), e.get("author"), e.get("episode_id", "").rsplit("__", 1)[-1])
                   for e in episodes]
    if len(author_keys) != len(set(author_keys)):
        raise ValueError("duplicate thread/author/installation across packets")
    packet = {
        "schema_version": "reviewed-forum-occupancy-episodes/1",
        "packet_id": "reviewed_combined001",
        "root_adopted": True,
        "dependence_reviewed": True,
        "dependence_qualification": (left["dependence_qualification"] + " " +
                                     adopted_right["dependence_qualification"]),
        "selected_thread_count": left["selected_thread_count"] + right["selected_thread_count"],
        "jurisdictions": left["jurisdictions"], "episodes": episodes,
        "adoption_decision": "Root adopted corrected SOL001 after representative spot check and specified fixes; root001 was already root-adopted.",
        "scope_status": "interim_30_threads_not_full_corpus",
    }
    receipt = {
        "schema_version": "solar-forum-combined-receipt/1",
        "decision_authority": "root task message requesting merge and run",
        "inputs": [{"path": str(p.relative_to(ROOT)), "sha256": sha(p)}
                   for p in (ROOT_PACKET, SOL_PACKET)],
        "sol001_adoption_change": "packet and all 19 episode root_adopted fields changed false to true after root spot check",
        "episodes": len(episodes), "selected_threads": packet["selected_thread_count"],
        "episode_ids_unique": True, "thread_author_installation_keys_unique": True,
        "scope_status": packet["scope_status"],
        "interpretation_guards": [
            "Eleven action indicators are not additive applicant encounters; final inspection and final approval are nested.",
            "Survey Required=No answers the named survey question and is not global absence outside that question.",
            "This is an interim 30-thread evidence packet while broader discovery continues."
        ]
    }
    OUT.write_text(json.dumps(packet, indent=2) + "\n")
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"out": str(OUT), "episodes": len(episodes),
                      "threads": packet["selected_thread_count"]}, indent=2))


if __name__ == "__main__": main()
