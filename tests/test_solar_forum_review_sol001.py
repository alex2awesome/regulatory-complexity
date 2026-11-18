from pipeline.procbench.process_structure.forum import quoted_reference
from pipeline.procbench.process_structure.solar_forum_bridge import BLOCK, ROOT
from pipeline.procbench.process_structure.solar_forum_review_sol001 import THREADS, build


def test_sol001_coverage_checklists_and_quote_replay():
    packet, coverage = build()
    assert packet["root_adopted"] is False
    assert {r["thread_id"] for r in coverage} == set(THREADS)
    assert len(packet["episodes"]) >= 15
    for episode in packet["episodes"]:
        assert episode["reviewed_step_ids"] == BLOCK
        assert [r["step_id"] for r in episode["readings"]] == BLOCK
        for quote in episode["identity_context_quotes"]:
            quoted_reference(quote, ROOT)
        for reading in episode["readings"]:
            assert reading["detected"] == bool(reading["quotes"])
            for quote in reading["quotes"]:
                quoted_reference(quote, ROOT)
