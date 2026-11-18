"""Optional fixed-prior additive design for elapsed operation log locations."""

from __future__ import annotations

import math
from typing import Any

import numpy as np


SCHEMA_VERSION = "operation-location-design/1"
UNLISTED_POLICY = "zero_additive_effect"


def compile_operation_location_design(
    declaration: dict[str, Any], operations: list[dict[str, Any]]
) -> dict[str, Any]:
    """Validate a declaration and return its scaled operation-by-term design.

    Coordinates are standard normal.  Consequently each matrix column already
    includes the declared fixed ``prior_sd``; no hyper-scale is learned.
    """
    if not isinstance(declaration, dict) or declaration.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"Operation location design requires {SCHEMA_VERSION}")
    if declaration.get("unlisted_operations") != UNLISTED_POLICY:
        raise ValueError("Operation location design must declare unlisted_operations: zero_additive_effect")
    interpretation = declaration.get("interpretation")
    if not isinstance(interpretation, str) or not interpretation.strip():
        raise ValueError("Operation location design requires a nonempty interpretation")
    terms = declaration.get("terms")
    rows = declaration.get("rows")
    if not isinstance(terms, list) or not terms or not isinstance(rows, list):
        raise ValueError("Operation location design requires nonempty terms and a rows list")

    term_ids: list[str] = []
    normalized_terms = []
    for term in terms:
        if not isinstance(term, dict) or set(term) != {"id", "group", "prior_sd", "rationale"}:
            raise ValueError("Each operation location term requires id, group, prior_sd, and rationale")
        ident, group, rationale, sd = term["id"], term["group"], term["rationale"], term["prior_sd"]
        if (not isinstance(ident, str) or not ident.strip() or ident in term_ids
                or not isinstance(group, str) or not group.strip()
                or not isinstance(rationale, str) or not rationale.strip()
                or isinstance(sd, bool) or not isinstance(sd, (int, float))
                or not math.isfinite(sd) or sd <= 0):
            raise ValueError("Operation location terms need distinct IDs, labels, rationale, and positive finite prior_sd")
        term_ids.append(ident)
        normalized_terms.append(dict(term, prior_sd=float(sd)))

    operation_index = {(row["program"], row["op"].id): i for i, row in enumerate(operations)}
    if len(operation_index) != len(operations):
        raise ValueError("Operation location design requires unique program/operation identities")
    matrix = np.zeros((len(operations), len(terms)))
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"program_id", "operation_id", "loadings"}:
            raise ValueError("Each operation location row requires program_id, operation_id, and loadings")
        key = (row["program_id"], row["operation_id"])
        if key in seen:
            raise ValueError("Duplicate operation location design row: " + ":".join(map(str, key)))
        if key not in operation_index:
            raise ValueError("Unknown operation location design row: " + ":".join(map(str, key)))
        seen.add(key)
        loadings = row["loadings"]
        if not isinstance(loadings, dict) or set(loadings) - set(term_ids):
            raise ValueError("Operation location design row references an unknown term")
        for ident, value in loadings.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("Operation location loadings must be finite numbers")
            matrix[operation_index[key], term_ids.index(ident)] = float(value)
    matrix *= np.asarray([term["prior_sd"] for term in normalized_terms])[None, :]
    return dict(matrix=matrix, terms=normalized_terms, interpretation=interpretation,
                unlisted_operations=UNLISTED_POLICY, listed_rows=len(seen))
