import copy
import hashlib

import pytest

from pipeline.procbench.process_structure.calfresh import COUNTY_SOURCES, compile_county_readings
from pipeline.procbench.process_structure.occupancy import Evidence


def fixture(tmp_path):
    scope = dict(scope="source-free initial-decision fixture", source_scope=list(COUNTY_SOURCES),
                 steps=[dict(id="file_application"), dict(id="interview_encounter")])
    readings = []
    for sid in COUNTY_SOURCES:
        path = f"corpus/realworld/calfresh/raw/{sid}.txt"
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        text = f"Fixture {sid}. Application. Interview."
        target.write_text(text)
        readings.append(dict(source_id=sid, path=path, sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                             complete_reading=True, root_adopted=True, character_count=len(text), rows=[
                                 dict(step_id=s["id"], detected=False, quotes=[]) for s in scope["steps"]]))
    return scope, readings


def positive(reading, step, text, quote):
    row = next(row for row in reading["rows"] if row["step_id"] == step)
    start = text.index(quote)
    row.update(detected=True, quotes=[dict(text=quote, start=start, end=start+len(quote))])


def test_fixed_frame_keeps_silence_and_collapses_related_sf_pages(tmp_path):
    scope, readings = fixture(tmp_path)
    for reading in readings:
        if reading["source_id"] in {"S7", "S8"}:
            positive(reading, "interview_encounter", (tmp_path / reading["path"]).read_text(), "Interview")
    data = compile_county_readings(scope, readings, source_root=tmp_path)
    e = Evidence(data)
    assert len(data["observations"]) == 8  # 4 county groups times 2 actions, not 5 pages times 2.
    assert e.positive.sum() == 1
    assert e.negative.sum() == 7
    assert data["known_presence"] == []
    sf = next(r for r in data["observations"] if r["jurisdiction_id"] == "San_Francisco" and r["detected"])
    assert sf["source_ids"] == ["S7", "S8"]
    assert len(sf["lineage_refs"]) == 2
    assert e.support_report()["cells_with_repeated_readings"] == 0


@pytest.mark.parametrize("change,error", [
    ("not_adopted", "root-adopted"), ("not_read", "complete"),
    ("missing_source", "Every selected"), ("duplicate_source", "duplicate"),
    ("missing_negative", "exactly one"), ("changed_bytes", "Changed source"),
    ("incomplete_range", "whole-reading"), ("unquoted_positive", "quotations"),
    ("bad_quote", "Quotation"), ("nonboolean", "boolean"),
])
def test_rejects_incomplete_or_unbound_review(tmp_path, change, error):
    scope, readings = fixture(tmp_path)
    if change == "not_adopted":
        readings[0]["root_adopted"] = False
    elif change == "not_read":
        readings[0]["complete_reading"] = False
    elif change == "missing_source":
        readings.pop()
    elif change == "duplicate_source":
        readings.append(copy.deepcopy(readings[0]))
    elif change == "missing_negative":
        readings[0]["rows"].pop()
    elif change == "changed_bytes":
        (tmp_path / readings[0]["path"]).write_text("Changed.")
    elif change == "incomplete_range":
        readings[0]["character_count"] -= 1
    elif change == "unquoted_positive":
        readings[0]["rows"][0]["detected"] = True
    elif change == "bad_quote":
        readings[0]["rows"][0].update(detected=True, quotes=[dict(text="Wrong", start=0, end=5)])
    elif change == "nonboolean":
        readings[0]["rows"][0]["detected"] = 1
    with pytest.raises(ValueError, match=error):
        compile_county_readings(scope, readings, source_root=tmp_path)
