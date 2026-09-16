"""Score-node (point system) tests: a mini NY-style score sheet.

Run:  python3 tests/test_score.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "pipeline"))

from executor import reachable_outcomes

TREE = {
    "rule_id": "mini-scoresheet", "citation": "toy health code",
    "input_schema": {"fields": [
        {"name": "rats_observed", "type": "boolean", "question": "rats?", "supplier": "inspector",
         "provenance_class": "f", "acquisition": "inspection"},
        {"name": "mold_observed", "type": "boolean", "question": "mold?", "supplier": "inspector",
         "provenance_class": "f", "acquisition": "inspection"},
        {"name": "cleanliness_notes", "type": "string", "question": "general cleanliness", "supplier": "inspector",
         "provenance_class": "f", "acquisition": "inspection"},
    ]},
    "nodes": [
        {"id": "n_score",
         "span": {"quote": "violations shall be scored", "cite": "toy §1"},
         "score": {
            "decider": "inspector",
            "items": [
                {"text": "rats present", "type": "objective", "points": 6,
                 "expr": {"var": "rats_observed"}, "inputs": ["rats_observed"]},
                {"text": "mold present", "type": "objective", "points": 4,
                 "expr": {"var": "mold_observed"}, "inputs": ["mold_observed"]},
                {"text": "generally unsanitary", "type": "judgment", "points": 5,
                 "inputs": ["cleanliness_notes"]},
            ],
            "thresholds": [
                {"min": 0, "max": 9, "target": "o_grade_a"},
                {"min": 10, "target": "o_grade_b"},
            ],
         }},
        {"id": "o_grade_a", "outcome": {"label": "approve", "description": "grade A"}},
        {"id": "o_grade_b", "outcome": {"label": "conditional_approve", "description": "grade B"}},
    ],
    "root": "n_score",
}

# clean kitchen: objective 0; judgment slack 0..5 -> [0,5] -> only grade A
r = reachable_outcomes(TREE, {"rats_observed": False, "mold_observed": False, "cleanliness_notes": "spotless"})
assert r.outcomes == {"approve"}, r.outcomes
assert not r.discretion_exposed

# rats only: [6, 11] straddles the 9/10 boundary -> BOTH grades reachable, judgment is pivotal
r = reachable_outcomes(TREE, {"rats_observed": True, "mold_observed": False, "cleanliness_notes": "meh"})
assert r.outcomes == {"approve", "conditional_approve"}, r.outcomes
assert r.discretion_exposed and r.pivotal_judgment == {"n_score"}

# rats + mold: [10, 15] -> grade B regardless of the judgment call
r = reachable_outcomes(TREE, {"rats_observed": True, "mold_observed": True, "cleanliness_notes": "bad"})
assert r.outcomes == {"conditional_approve"}, r.outcomes
assert not r.discretion_exposed

# missing inspection fact -> schema gap widens the interval, not judgment pivotality alone
r = reachable_outcomes(TREE, {"mold_observed": False, "cleanliness_notes": "spotless"})
assert "rats_observed" in r.missing_inputs
assert r.outcomes == {"approve", "conditional_approve"}, r.outcomes

assert r.inputs_demanded == {"rats_observed", "mold_observed", "cleanliness_notes"}

print("test_score OK — point-system identified sets behave")
