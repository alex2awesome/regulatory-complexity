import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pytest

from pipeline.procbench.process_structure import occupancy


@pytest.mark.parametrize("changed", [None, "input", "config", "source", "logical_implementation"])
def test_cli_binds_consumed_bytes_and_rejects_midfit_changes(tmp_path, monkeypatch, changed):
    source = tmp_path / "source.md"
    source.write_text("Source-free CLI fixture.\n")
    ref = dict(path="source.md", locator="whole fixture", sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    data = dict(schema_version=occupancy.SCHEMA, scope="source-free fixture",
                jurisdictions=["A"], steps=["step"], source_types=["forum"],
                source_models={"forum": {"detection_beta": [1, 1], "false_positive_probability": .1}},
                opportunity_frame="reviewed_units_not_selected_for_step_mentions",
                conditional_independence="assumed_given_presence_and_source_type_detection",
                assumption_note="Fixture only.", known_presence=[],
                observations=[dict(unit_id="unit", dependence_group_id="unit", jurisdiction_id="A",
                                   step_id="step", source_type="forum", detected=True,
                                   reviewed_scope=True, evidence_refs=[ref])])
    input_path, config_path, out = tmp_path / "input.json", tmp_path / "config.json", tmp_path / "out"
    input_path.write_text(json.dumps(data))
    config_path.write_text("{}")
    input_digest = hashlib.sha256(input_path.read_bytes()).hexdigest()
    paths = {"input": input_path, "config": config_path, "source": source}

    def fake_fit(data, config):
        if changed == "logical_implementation":
            original = Path.read_bytes
            helper = Path(occupancy.__file__).with_name("logical_support.py")
            # Simulate mutation without ever writing to the real source file.
            monkeypatch.setattr(Path, "read_bytes", lambda path:
                original(path) + (b"\n# changed during fit" if path == helper else b""))
        elif changed:
            paths[changed].write_text("Changed during source-free fixture sampling.\n")
        return {"numerically_usable": False}, {"fixture": np.zeros((2, 8))}

    monkeypatch.setattr(occupancy, "fit", fake_fit)
    monkeypatch.setattr(sys, "argv", ["occupancy", "--input", str(input_path), "--config", str(config_path),
                                     "--source-root", str(tmp_path), "--out", str(out)])
    if changed:
        with pytest.raises(ValueError, match="[Cc]hanged"):
            occupancy.main()
        assert not out.exists()
    else:
        occupancy.main()
        manifest = json.loads((out / "manifest.json").read_text())
        assert manifest["input_sha256"] == input_digest
        assert manifest["source_bindings_verified"] == 1
        assert manifest["detection_implementation_sha256"] == hashlib.sha256(
            Path(occupancy.__file__).with_name("detection_hierarchy.py").read_bytes()).hexdigest()
        assert manifest["logical_support_implementation_sha256"] == hashlib.sha256(
            Path(occupancy.__file__).with_name("logical_support.py").read_bytes()).hexdigest()
        assert not manifest["scientific_validation_complete"]
