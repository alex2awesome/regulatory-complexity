"""Deterministic, source-bound review gate for process-evidence measurements.

The gate materializes human-reviewed corrections.  It does not interpret legacy
review prose and it does not claim that an admitted measurement was consumed by
any compiler or model.  Excluded measurements remain in the returned ledger;
the report is the explicit interface for downstream filtering.

Hash serialization is UTF-8 JSON with sorted object keys, compact separators,
``ensure_ascii=False`` and non-finite numbers forbidden.  Evidence hashes cover
the complete evidence object.  Each document hash covers the complete document
object (not merely its text), keyed by its exact document ID.
"""
from __future__ import annotations

import copy
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import re

from .evidence_contract import normalized_quote, validate as validate_evidence


REVIEW_VERSION = "effective-evidence-review/1"
REPORT_VERSION = "effective-evidence-report/1"
DISPOSITIONS = {"admitted", "residual_only", "held", "duplicate", "out_of_scope"}
EDITABLE_FIELDS = {
    "metric", "scope", "activity_ids", "start", "end", "statistic",
    "value", "lower", "upper", "unit", "qualitative", "n", "case_id",
    "cohort", "source_family", "doc_id", "quote", "interpretation",
}
NUMERIC_FIELDS = {"value", "lower", "upper", "n"}
_NAMESPACE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
_NUMERIC_TEXT = re.compile(r"\s*\$?\s*([+-]?(?:\d+(?:,\d{3})*(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?)\s*\Z")


def canonical_json_bytes(value):
    """Return the bytes used by all hashes in this contract."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def evidence_digest(evidence):
    return hashlib.sha256(canonical_json_bytes(evidence)).hexdigest()


def document_digests(documents):
    """Return exact-ID -> full-document digest, rejecting ambiguous IDs."""
    result = {}
    for document in documents:
        if not isinstance(document, dict) or not isinstance(document.get("id"), str):
            raise ValueError("Every document needs an exact string ID")
        if not isinstance(document.get("text"), str):
            raise ValueError(f"Document {document['id']!r} needs string text")
        ident = document["id"]
        if not ident or ident in result:
            raise ValueError("Document IDs must be nonempty and unique")
        result[ident] = hashlib.sha256(canonical_json_bytes(document)).hexdigest()
    return dict(sorted(result.items()))


def documents_digest(documents):
    """Digest the ID-keyed document digest map, independent of list order."""
    return hashlib.sha256(canonical_json_bytes(document_digests(documents))).hexdigest()


def gate_id(namespace, measurement_id):
    """Unambiguous string encoding of the structured (namespace, local ID) key."""
    return canonical_json_bytes([namespace, measurement_id]).decode("utf-8")


def _exact_keys(value, expected, where):
    if not isinstance(value, dict) or set(value) != set(expected):
        missing = sorted(set(expected) - set(value) if isinstance(value, dict) else set(expected))
        extra = sorted(set(value) - set(expected) if isinstance(value, dict) else [])
        raise ValueError(f"{where} fields differ; missing={missing}, extra={extra}")


def _exact_equal(left, right):
    """JSON equality that does not treat True == 1 or 1 == 1.0 as exact."""
    try:
        return canonical_json_bytes(left) == canonical_json_bytes(right)
    except (TypeError, ValueError):
        return False


def _validate_ref(ref, texts, where):
    _exact_keys(ref, {"doc_id", "quote"}, where)
    if not isinstance(ref["doc_id"], str) or not isinstance(ref["quote"], str):
        raise ValueError(f"{where} document ID and quote must be strings")
    quote = normalized_quote(ref["quote"])
    if not quote or quote not in texts.get(ref["doc_id"], ""):
        raise ValueError(f"{where} has nonverbatim support in {ref['doc_id']!r}")


def _validate_refs(refs, texts, where):
    if not isinstance(refs, list) or not refs:
        raise ValueError(f"{where} requires at least one source quote")
    signatures = set()
    for index, ref in enumerate(refs):
        _validate_ref(ref, texts, f"{where}.source_quotes[{index}]")
        signature = canonical_json_bytes(ref)
        if signature in signatures:
            raise ValueError(f"{where} repeats a source quote")
        signatures.add(signature)


def _finite_number(value):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value))


def _validate_numeric_support(change, where):
    new = change["new"]
    if new is None:
        if change["source_value_text"] is not None:
            raise ValueError(f"{where}.source_value_text must be null when clearing a number")
        return
    if not _finite_number(new):
        raise ValueError(f"{where}.new must be a finite JSON number or null")
    source_value = change["source_value_text"]
    if not isinstance(source_value, str) or not source_value:
        raise ValueError(f"{where} numeric correction requires source_value_text")
    match = _NUMERIC_TEXT.fullmatch(source_value)
    if not match:
        raise ValueError(f"{where}.source_value_text must be one exact numeric token")
    try:
        parsed = Decimal(match.group(1).replace(",", ""))
        expected = Decimal(str(new))
    except InvalidOperation as error:
        raise ValueError(f"{where} has invalid numeric source support") from error
    if parsed != expected:
        raise ValueError(f"{where} source_value_text does not equal corrected value")
    token = re.escape(source_value.strip())
    # A following period may be sentence punctuation; only reject it when it
    # continues the number.  This still prevents matching ``3`` inside ``3.0``.
    pattern = re.compile(r"(?<!\d)" + token + r"(?!\d|[.,]\d)")
    if not any(pattern.search(normalized_quote(ref["quote"])) for ref in change["source_quotes"]):
        raise ValueError(f"{where} numeric token is absent from its supporting quotes")


def validate(evidence, review, documents):
    """Validate a v1 review against exact evidence and source documents.

    All policy-selected IDs must appear exactly once.  Under ``mode=all`` this
    means every measurement.  Under ``mode=selected``, nonselected measurements
    are deterministically held by :func:`materialize`.
    """
    validate_evidence(evidence, documents)
    doc_hashes = document_digests(documents)
    texts = {d["id"]: normalized_quote(d["text"]) for d in documents}
    top_fields = {"schema_version", "program_id", "namespace", "evidence_sha256",
                  "document_sha256", "policy", "measurements"}
    _exact_keys(review, top_fields, "review")
    if review["schema_version"] != REVIEW_VERSION:
        raise ValueError(f"Unsupported review schema: {review['schema_version']!r}")
    if review["program_id"] != evidence["program_id"]:
        raise ValueError("Review program_id does not match evidence")
    namespace = review["namespace"]
    if not isinstance(namespace, str) or not _NAMESPACE.fullmatch(namespace):
        raise ValueError("Review namespace must match [A-Za-z0-9][A-Za-z0-9._-]*")
    expected_evidence_hash = evidence_digest(evidence)
    if review["evidence_sha256"] != expected_evidence_hash:
        raise ValueError("Review evidence_sha256 does not match the exact evidence input")
    if not _exact_equal(review["document_sha256"], doc_hashes):
        raise ValueError("Review document_sha256 does not match the exact document inputs")

    _exact_keys(review["policy"], {"mode", "selected_measurement_ids", "unselected_disposition"},
                "review.policy")
    mode = review["policy"]["mode"]
    selected = review["policy"]["selected_measurement_ids"]
    if mode not in {"all", "selected"}:
        raise ValueError("Review policy mode must be 'all' or 'selected'")
    if review["policy"]["unselected_disposition"] != "held":
        raise ValueError("The explicit unselected disposition must be 'held'")
    if not isinstance(selected, list) or any(not isinstance(x, str) for x in selected):
        raise ValueError("selected_measurement_ids must be a string list")
    if len(selected) != len(set(selected)):
        raise ValueError("selected_measurement_ids contains duplicates")

    measurements = evidence["measurements"]
    by_id = {m["id"]: m for m in measurements}
    all_ids = set(by_id)
    selected_ids = set(selected)
    if mode == "all" and selected:
        raise ValueError("all-mode review uses an empty selected_measurement_ids list")
    if mode == "selected" and not selected:
        raise ValueError("selected-mode review requires an explicit nonempty subset")
    if not selected_ids <= all_ids:
        raise ValueError("Review policy selects unknown measurement IDs: " +
                         ", ".join(sorted(selected_ids - all_ids)))
    required_ids = all_ids if mode == "all" else selected_ids

    rows = review["measurements"]
    if not isinstance(rows, list):
        raise ValueError("review.measurements must be a list")
    row_fields = {"measurement_id", "disposition", "reason", "source_quotes",
                  "changes", "duplicate_of"}
    change_fields = {"field", "old", "new", "reason", "source_quotes", "source_value_text"}
    reviewed_ids = []
    dispositions = {}
    duplicate_links = {}
    for index, row in enumerate(rows):
        where = f"review.measurements[{index}]"
        _exact_keys(row, row_fields, where)
        ident = row["measurement_id"]
        if not isinstance(ident, str) or ident not in all_ids:
            raise ValueError(f"{where} has an unknown measurement_id")
        reviewed_ids.append(ident)
        disposition = row["disposition"]
        if disposition not in DISPOSITIONS:
            raise ValueError(f"{where} has unknown disposition {disposition!r}")
        dispositions[ident] = disposition
        if not isinstance(row["reason"], str) or not row["reason"].strip():
            raise ValueError(f"{where} requires a nonempty reason")
        _validate_refs(row["source_quotes"], texts, where)
        duplicate_of = row["duplicate_of"]
        if disposition == "duplicate":
            if not isinstance(duplicate_of, str) or duplicate_of not in all_ids or duplicate_of == ident:
                raise ValueError(f"{where}.duplicate_of must name another known measurement")
            duplicate_links[ident] = duplicate_of
        elif duplicate_of is not None:
            raise ValueError(f"{where}.duplicate_of is only valid for duplicate disposition")
        if not isinstance(row["changes"], list):
            raise ValueError(f"{where}.changes must be a list")
        changed_fields = set()
        for change_index, change in enumerate(row["changes"]):
            change_where = f"{where}.changes[{change_index}]"
            _exact_keys(change, change_fields, change_where)
            field = change["field"]
            if field not in EDITABLE_FIELDS:
                raise ValueError(f"{change_where} cannot edit field {field!r}")
            if field in changed_fields:
                raise ValueError(f"{where} changes field {field!r} more than once")
            changed_fields.add(field)
            if not _exact_equal(change["old"], by_id[ident][field]):
                raise ValueError(f"{change_where}.old is not the exact current value")
            if _exact_equal(change["old"], change["new"]):
                raise ValueError(f"{change_where} is not a change")
            if not isinstance(change["reason"], str) or not change["reason"].strip():
                raise ValueError(f"{change_where} requires a nonempty reason")
            _validate_refs(change["source_quotes"], texts, change_where)
            review_refs = {canonical_json_bytes(ref) for ref in row["source_quotes"]}
            if any(canonical_json_bytes(ref) not in review_refs for ref in change["source_quotes"]):
                raise ValueError(f"{change_where} support must also appear in the row source_quotes")
            if field in NUMERIC_FIELDS:
                _validate_numeric_support(change, change_where)
            elif change["source_value_text"] is not None:
                raise ValueError(f"{change_where}.source_value_text is only for numeric fields")

        # A corrected number must not live only in gate metadata while the
        # effective measurement continues to cite a different source passage.
        prospective = dict(by_id[ident])
        for change in row["changes"]:
            prospective[change["field"]] = change["new"]
        final_ref = {"doc_id": prospective["doc_id"], "quote": prospective["quote"]}
        for change_index, change in enumerate(row["changes"]):
            if change["field"] in NUMERIC_FIELDS and change["new"] is not None:
                if canonical_json_bytes(final_ref) not in {
                        canonical_json_bytes(ref) for ref in change["source_quotes"]}:
                    raise ValueError(
                        f"{where}.changes[{change_index}] numeric support must be the final "
                        "measurement doc_id/quote")

    if len(reviewed_ids) != len(set(reviewed_ids)):
        raise ValueError("Review contains duplicate measurement IDs")
    if set(reviewed_ids) != required_ids:
        missing = sorted(required_ids - set(reviewed_ids))
        extra = sorted(set(reviewed_ids) - required_ids)
        raise ValueError(f"Review coverage differs from policy; missing={missing}, extra={extra}")
    for ident, target in duplicate_links.items():
        if target not in required_ids:
            raise ValueError(f"Duplicate {ident!r} targets an unreviewed measurement")
        if dispositions.get(target) not in {"admitted", "residual_only"}:
            raise ValueError(f"Duplicate {ident!r} must target an admitted or residual-only measurement")
    return review


def materialize(evidence, review, documents):
    """Return ``(corrected_evidence, disposition_report)`` without mutating inputs."""
    validate(evidence, review, documents)
    corrected = copy.deepcopy(evidence)
    corrected_by_id = {m["id"]: m for m in corrected["measurements"]}
    review_by_id = {r["measurement_id"]: r for r in review["measurements"]}
    for ident, row in review_by_id.items():
        for change in row["changes"]:
            corrected_by_id[ident][change["field"]] = copy.deepcopy(change["new"])

    # This catches corrected dangling activity/context IDs, invalid case requirements,
    # incompatible units, changed document links/quotes, and all schema violations.
    validate_evidence(corrected, documents)
    namespace = review["namespace"]
    dispositions = []
    for measurement in evidence["measurements"]:
        ident = measurement["id"]
        reviewed = review_by_id.get(ident)
        if reviewed is None:
            disposition = "held"
            reason = "not_selected_for_review"
            quotes, changes, duplicate_of = [], [], None
        else:
            disposition = reviewed["disposition"]
            reason = reviewed["reason"]
            quotes = copy.deepcopy(reviewed["source_quotes"])
            changes = copy.deepcopy(reviewed["changes"])
            duplicate_of = reviewed["duplicate_of"]
        dispositions.append({
            "measurement_id": ident,
            "gate_id": gate_id(namespace, ident),
            "gate_identity": {"namespace": namespace, "measurement_id": ident},
            "disposition": disposition,
            "reason": reason,
            "source_quotes": quotes,
            "changes": changes,
            "corrected": bool(changes),
            "compiler_eligible": disposition == "admitted",
            "duplicate_of": duplicate_of,
            "duplicate_of_gate_id": (gate_id(namespace, duplicate_of)
                                     if duplicate_of is not None else None),
        })

    def ids_for(statuses, key="measurement_id"):
        return [row[key] for row in dispositions if row["disposition"] in statuses]

    excluded_statuses = {"held", "duplicate", "out_of_scope"}
    compiler_excluded = excluded_statuses | {"residual_only"}
    report = {
        "schema_version": REPORT_VERSION,
        "review_schema_version": REVIEW_VERSION,
        "program_id": evidence["program_id"],
        "namespace": namespace,
        "input_evidence_sha256": evidence_digest(evidence),
        "output_evidence_sha256": evidence_digest(corrected),
        "review_sha256": hashlib.sha256(canonical_json_bytes(review)).hexdigest(),
        "document_sha256": document_digests(documents),
        "documents_sha256": documents_digest(documents),
        "policy": copy.deepcopy(review["policy"]),
        "dispositions": dispositions,
        "admitted_measurement_ids": ids_for({"admitted"}),
        "residual_only_measurement_ids": ids_for({"residual_only"}),
        "excluded_measurement_ids": ids_for(excluded_statuses),
        "compiler_excluded_measurement_ids": ids_for(compiler_excluded),
        "admitted_gate_ids": ids_for({"admitted"}, "gate_id"),
        "residual_only_gate_ids": ids_for({"residual_only"}, "gate_id"),
        "excluded_gate_ids": ids_for(excluded_statuses, "gate_id"),
        "compiler_excluded_gate_ids": ids_for(compiler_excluded, "gate_id"),
        "corrected_measurement_ids": [row["measurement_id"] for row in dispositions if row["corrected"]],
        "requires_downstream_review_measurement_ids": [
            row["measurement_id"] for row in dispositions if row["corrected"]
        ],
        "downstream_review_evidence_sha256": evidence_digest(corrected),
        "counts": {status: sum(row["disposition"] == status for row in dispositions)
                   for status in sorted(DISPOSITIONS)},
        "all_measurements_accounted": (
            len(dispositions) == len(evidence["measurements"])
            and {row["measurement_id"] for row in dispositions}
                == {m["id"] for m in evidence["measurements"]}
        ),
        "model_consumption_asserted": False,
    }
    return corrected, report
