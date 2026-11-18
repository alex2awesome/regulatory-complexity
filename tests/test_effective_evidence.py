import copy

import pytest

from pipeline.procbench.effective_evidence import (
    REVIEW_VERSION, document_digests, documents_digest, evidence_digest, gate_id,
    materialize, validate,
)


def fixture():
    documents = [
        {"id": "source", "text": "The review took exactly 30 calendar days. A duplicate report repeated it."},
        {"id": "scope", "text": "The fee report is outside this timing analysis."},
    ]
    evidence = {
        "schema_version": "process-evidence/2",
        "program_id": "demo",
        "actors": [{"id": "agency", "name": "Agency", "role": "agency", "aliases": [],
                    "evidence": [{"doc_id": "source", "quote": "The review took exactly 30 calendar days."}]}],
        "activities": [{"id": "review", "name": "Review", "actor_id": "agency",
                        "task_type": "technical_review", "stage": "review", "scope": "core",
                        "condition": None, "existence": "explicit",
                        "evidence": [{"doc_id": "source", "quote": "The review took exactly 30 calendar days."}],
                        "notes": ""}],
        "relations": [],
        "measurements": [
            {"id": "elapsed", "metric": "elapsed", "scope": "step", "activity_ids": ["review"],
             "start": "activity_start", "end": "activity_end", "statistic": "individual",
             "value": 3, "lower": None, "upper": None, "unit": "calendar_days",
             "qualitative": False, "n": None, "case_id": "case-1", "cohort": None,
             "source_family": "official", "doc_id": "source",
             "quote": "The review took exactly 30 calendar days.", "interpretation": "review duration"},
            {"id": "copy", "metric": "elapsed", "scope": "step", "activity_ids": ["review"],
             "start": "activity_start", "end": "activity_end", "statistic": "individual",
             "value": 30, "lower": None, "upper": None, "unit": "calendar_days",
             "qualitative": False, "n": None, "case_id": "case-1", "cohort": None,
             "source_family": "official", "doc_id": "source",
             "quote": "A duplicate report repeated it.", "interpretation": "duplicate"},
            {"id": "fee", "metric": "fee", "scope": "process", "activity_ids": [],
             "start": "unspecified", "end": "unspecified", "statistic": "estimate",
             "value": None, "lower": None, "upper": None, "unit": "USD",
             "qualitative": True, "n": None, "case_id": None, "cohort": None,
             "source_family": "official", "doc_id": "scope",
             "quote": "The fee report is outside this timing analysis.", "interpretation": "scope note"},
        ],
        "ambiguities": [],
        "excluded": [],
    }
    return evidence, documents


def ref(quote="The review took exactly 30 calendar days.", doc_id="source"):
    return {"doc_id": doc_id, "quote": quote}


def row(ident, disposition="admitted", *, reason="reviewed", quotes=None, changes=None,
        duplicate_of=None):
    return {"measurement_id": ident, "disposition": disposition, "reason": reason,
            "source_quotes": quotes or [ref()], "changes": changes or [],
            "duplicate_of": duplicate_of}


def review_for(evidence, documents, rows, *, mode="all", selected=None, namespace="three-family.v1"):
    return {"schema_version": REVIEW_VERSION, "program_id": evidence["program_id"],
            "namespace": namespace, "evidence_sha256": evidence_digest(evidence),
            "document_sha256": document_digests(documents),
            "policy": {"mode": mode, "selected_measurement_ids": selected or [],
                       "unselected_disposition": "held"},
            "measurements": rows}


def test_materializes_exact_correction_and_complete_disposition_report_without_mutation():
    evidence, documents = fixture()
    original = copy.deepcopy(evidence)
    change = {"field": "value", "old": 3, "new": 30, "reason": "transcription correction",
              "source_quotes": [ref()], "source_value_text": "30"}
    review = review_for(evidence, documents, [
        row("elapsed", changes=[change]),
        row("copy", "duplicate", quotes=[ref("A duplicate report repeated it.")], duplicate_of="elapsed"),
        row("fee", "out_of_scope", quotes=[ref("The fee report is outside this timing analysis.", "scope")]),
    ])
    corrected, report = materialize(evidence, review, documents)
    assert evidence == original and corrected is not evidence
    assert corrected["measurements"][0]["id"] == "elapsed"
    assert corrected["measurements"][0]["value"] == 30
    assert report["admitted_measurement_ids"] == ["elapsed"]
    assert report["residual_only_measurement_ids"] == []
    assert report["excluded_measurement_ids"] == ["copy", "fee"]
    assert report["compiler_excluded_measurement_ids"] == ["copy", "fee"]
    assert report["compiler_excluded_gate_ids"] == [gate_id("three-family.v1", "copy"),
                                                     gate_id("three-family.v1", "fee")]
    assert report["requires_downstream_review_measurement_ids"] == ["elapsed"]
    assert report["downstream_review_evidence_sha256"] == evidence_digest(corrected)
    assert report["output_evidence_sha256"] != report["input_evidence_sha256"]
    assert report["all_measurements_accounted"] and not report["model_consumption_asserted"]
    assert report["dispositions"][0]["changes"] == [change]


def test_selected_subset_explicitly_holds_every_unselected_original():
    evidence, documents = fixture()
    review = review_for(evidence, documents,
                        [row("elapsed", "residual_only", reason="clock remains ambiguous")],
                        mode="selected", selected=["elapsed"])
    corrected, report = materialize(evidence, review, documents)
    assert corrected == evidence
    assert report["residual_only_measurement_ids"] == ["elapsed"]
    assert report["excluded_measurement_ids"] == ["copy", "fee"]
    assert report["compiler_excluded_measurement_ids"] == ["elapsed", "copy", "fee"]
    assert [x["reason"] for x in report["dispositions"][1:]] == [
        "not_selected_for_review", "not_selected_for_review"]
    assert report["counts"] == {"admitted": 0, "duplicate": 0, "held": 2,
                                "out_of_scope": 0, "residual_only": 1}


@pytest.mark.parametrize("mutation, match", [
    (lambda review, evidence: review["measurements"].pop(), "coverage differs"),
    (lambda review, evidence: review["measurements"].append(row("unknown")), "unknown measurement_id"),
    (lambda review, evidence: review.update(evidence_sha256="0" * 64), "evidence_sha256"),
    (lambda review, evidence: review["document_sha256"].update(source="0" * 64), "document_sha256"),
    (lambda review, evidence: review["measurements"][0].update(disposition="maybe"), "unknown disposition"),
])
def test_hash_coverage_and_unknown_decisions_fail_closed(mutation, match):
    evidence, documents = fixture()
    rows = [row("elapsed"), row("copy"), row("fee")]
    review = review_for(evidence, documents, rows)
    mutation(review, evidence)
    with pytest.raises(ValueError, match=match):
        validate(evidence, review, documents)


def test_quote_and_exact_old_value_are_mandatory():
    evidence, documents = fixture()
    change = {"field": "value", "old": 4, "new": 30, "reason": "correction",
              "source_quotes": [ref()], "source_value_text": "30"}
    review = review_for(evidence, documents,
                        [row("elapsed", changes=[change]), row("copy"), row("fee")])
    with pytest.raises(ValueError, match="exact current value"):
        validate(evidence, review, documents)
    change["old"] = 3
    review["measurements"][0]["source_quotes"] = [ref("not in source")]
    with pytest.raises(ValueError, match="nonverbatim support"):
        validate(evidence, review, documents)


@pytest.mark.parametrize("new, source_value, match", [
    (31, "30", "does not equal"),
    (30, None, "requires source_value_text"),
    (30, "30.0", "absent from"),
    (float("inf"), "30", "finite JSON number"),
])
def test_numeric_corrections_require_finite_exact_quoted_value(new, source_value, match):
    evidence, documents = fixture()
    change = {"field": "value", "old": 3, "new": new, "reason": "correction",
              "source_quotes": [ref()], "source_value_text": source_value}
    review = review_for(evidence, documents,
                        [row("elapsed", changes=[change]), row("copy"), row("fee")])
    with pytest.raises(ValueError, match=match):
        validate(evidence, review, documents)


def test_final_contract_rejects_dangling_corrected_activity_id():
    evidence, documents = fixture()
    change = {"field": "activity_ids", "old": ["review"], "new": ["missing"],
              "reason": "proposed relink", "source_quotes": [ref()], "source_value_text": None}
    review = review_for(evidence, documents,
                        [row("elapsed", changes=[change]), row("copy"), row("fee")])
    validate(evidence, review, documents)  # Preconditions are valid; result is not.
    with pytest.raises(ValueError, match="unknown activity"):
        materialize(evidence, review, documents)


def test_numeric_support_must_be_the_effective_measurements_own_provenance():
    evidence, documents = fixture()
    documents[1]["text"] += " The separate corrected value is 30."
    support = ref("The separate corrected value is 30.", "scope")
    change = {"field": "value", "old": 3, "new": 30, "reason": "correction",
              "source_quotes": [support], "source_value_text": "30"}
    review = review_for(evidence, documents, [
        row("elapsed", changes=[change], quotes=[support]), row("copy"), row("fee")])
    with pytest.raises(ValueError, match="final measurement doc_id/quote"):
        validate(evidence, review, documents)


def test_duplicate_must_target_reviewed_retained_row():
    evidence, documents = fixture()
    rows = [row("elapsed", "held"),
            row("copy", "duplicate", quotes=[ref("A duplicate report repeated it.")], duplicate_of="elapsed"),
            row("fee")]
    with pytest.raises(ValueError, match="must target an admitted or residual-only"):
        validate(evidence, review_for(evidence, documents, rows), documents)


def test_hashes_and_gate_ids_are_deterministic_and_unambiguous():
    evidence, documents = fixture()
    assert evidence_digest(copy.deepcopy(evidence)) == evidence_digest(evidence)
    assert documents_digest(list(reversed(documents))) == documents_digest(documents)
    assert gate_id("a", "b::c") != gate_id("a::b", "c")
