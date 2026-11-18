import json

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.solar_panel.prepare_shared_journeys import compile_packets


def test_dated_timeline_uses_irredundant_increments_and_retains_total(tmp_path):
    packet = {"episodes": [{"thread": "t", "author": "a", "location": "County known; AHJ unknown",
        "timing": [
          {"clock":"contract_to_installation","start_date":"2023-01-01","end_date":"2023-01-11","refs":["p"]},
          {"clock":"installation_to_pto","start_date":"2023-01-11","end_date":"2023-01-21","refs":["p"]},
          {"clock":"contract_to_pto","start_date":"2023-01-01","end_date":"2023-01-21","refs":["p"]}
        ]}]}
    path = tmp_path / "packet.json"; path.write_text(json.dumps(packet))
    data, routes = compile_packets([path])
    assert routes == []
    program = data["programs"][0]
    assert len(program["observations"]) == 2
    assert program["derived_reconstructions"][0]["original_clock"] == "contract_to_pto"
    assert len(program["derived_reconstructions"][0]["activity_ids"]) == 2
    # Unknown AHJ/county context does not manufacture an actor identity.
    assert all(op["actor_id"] is None for op in program["routes"][0]["operations"])
    VisitHierarchy(data, Config(modeled_channels=("elapsed",)))


def test_value_only_named_endpoints_compile_but_unusable_clock_routes(tmp_path):
    packet = {"episodes": [
      {"thread":"a","author":"x","timing":[
        {"clock":"installation_to_inspection","value":2,"unit":"weeks"},
        {"clock":"inspection_to_pto","value":3,"unit":"weeks"}]},
      {"thread":"b","author":"y","timing":[
        {"clock":"unspecified","value":4,"unit":"weeks"},
        {"clock":"other_unspecified","value":5,"unit":"weeks"}]}
    ]}
    path = tmp_path / "packet.json"; path.write_text(json.dumps(packet))
    data, routes = compile_packets([path])
    assert len(data["programs"]) == 1
    assert routes[0]["route"] == "fewer_than_two_supported_completed_intervals"
