"""Optional fixed source-type scales for elapsed report kernels.

The declaration is a compiler policy, not evidence that a calibration has been
verified and not a learned reliability model.  Resolved annotations are carried
on observations/cohorts so V6 does not need to guess source taxonomy.  Absence
of an annotation is the historical ``Config.report_sd`` path.
"""

from __future__ import annotations

import math

from .burden_channels import SOURCE_FAMILY_TYPES


SCHEMA_VERSION = "source-type-report-scales/1"
FALLBACK = "config_report_sd"
FIXED_KIND = "fixed_source_type_declaration"
FALLBACK_KIND = "config_report_sd_fallback"
UNVERIFIED = "declared_reference_unverified"
NOT_APPLICABLE = "not_applicable"
FALLBACK_REASONS = {"source_type_not_declared", "source_type_unresolved"}


def _nonempty_string(value):
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def _positive_scale(value):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and value > 0)


def validate_source_type_report_scales(declaration, source_types):
    """Validate the complete opt-in compiler declaration without mutating it."""
    if (not isinstance(declaration, dict)
            or set(declaration) != {"schema_version", "elapsed", "fallback"}
            or declaration.get("schema_version") != SCHEMA_VERSION
            or declaration.get("fallback") != FALLBACK
            or not isinstance(declaration.get("elapsed"), dict)
            or not declaration["elapsed"]):
        raise ValueError("Source-type report scales require the versioned elapsed declaration and config fallback")
    allowed = set(source_types)
    if set(declaration["elapsed"]) - allowed:
        raise ValueError("Source-type report scales contain an unknown source type")
    for source_type, spec in declaration["elapsed"].items():
        if (not _nonempty_string(source_type) or not isinstance(spec, dict)
                or set(spec) != {"report_log_scale", "calibration_id"}
                or not _positive_scale(spec.get("report_log_scale"))
                or not _nonempty_string(spec.get("calibration_id"))):
            raise ValueError("Each source-type report scale needs a positive finite scale and calibration reference")
    return declaration


def resolved_precision_annotation(source_type, declaration):
    """Return one strict row/cohort annotation for an active declaration."""
    if declaration is None:
        return None
    spec = declaration["elapsed"].get(source_type)
    if spec is not None:
        return dict(source_type=source_type,
                    report_log_scale=float(spec["report_log_scale"]),
                    report_scale_basis=dict(kind=FIXED_KIND,
                        calibration_id=spec["calibration_id"],
                        calibration_provenance=UNVERIFIED))
    reason = ("source_type_unresolved" if source_type is None
              else "source_type_not_declared")
    return dict(source_type=source_type,
                report_scale_basis=dict(kind=FALLBACK_KIND, reason=reason,
                    calibration_provenance=NOT_APPLICABLE))


def precision_annotation(record):
    """Strictly validate and return an annotation, or ``None`` for legacy rows."""
    provenance = record.get("provenance")
    basis = provenance.get("report_scale_basis") if isinstance(provenance, dict) else None
    basis_present = isinstance(provenance, dict) and "report_scale_basis" in provenance
    present = "report_log_scale" in record or basis_present
    if not present:
        return None
    if not isinstance(basis, dict) or not _nonempty_string(basis.get("kind")):
        raise ValueError("Resolved source precision requires explicit provenance")
    kind = basis["kind"]
    if kind == FIXED_KIND:
        if (set(basis) != {"kind", "calibration_id", "calibration_provenance"}
                or basis.get("calibration_provenance") != UNVERIFIED
                or not _nonempty_string(basis.get("calibration_id"))
                or not _nonempty_string(record.get("source_type"))
                or record.get("source_type") not in SOURCE_FAMILY_TYPES
                or not _positive_scale(record.get("report_log_scale"))):
            raise ValueError("Fixed source precision needs a type, finite scale, and unverified calibration reference")
        return dict(kind=kind, source_type=record["source_type"],
                    report_log_scale=float(record["report_log_scale"]),
                    calibration_id=basis["calibration_id"],
                    calibration_provenance=UNVERIFIED)
    if kind == FALLBACK_KIND:
        if (set(basis) != {"kind", "reason", "calibration_provenance"}
                or basis.get("reason") not in FALLBACK_REASONS
                or basis.get("calibration_provenance") != NOT_APPLICABLE
                or "report_log_scale" in record):
            raise ValueError("Source-precision fallback must use Config.report_sd without a scale override")
        source_type = record.get("source_type")
        if ((basis["reason"] == "source_type_unresolved" and source_type is not None)
                or (basis["reason"] == "source_type_not_declared"
                    and (not _nonempty_string(source_type)
                         or source_type not in SOURCE_FAMILY_TYPES))):
            raise ValueError("Source-precision fallback reason must match the resolved source type")
        return dict(kind=kind, source_type=source_type, report_log_scale=None,
                    reason=basis["reason"], calibration_provenance=NOT_APPLICABLE)
    raise ValueError("Unknown resolved source-precision basis")


def elapsed_report_log_scale(record, default, unknown_n_floor=None):
    """Resolve one elapsed regular-kernel scale, optionally applying unknown-n floor."""
    if not _positive_scale(default):
        raise ValueError("Default report scale must be finite and positive")
    annotation = precision_annotation(record)
    scale = default if annotation is None or annotation["report_log_scale"] is None else annotation["report_log_scale"]
    if unknown_n_floor is not None:
        if (isinstance(unknown_n_floor, bool) or not isinstance(unknown_n_floor, (int, float))
                or not math.isfinite(unknown_n_floor) or unknown_n_floor < 0):
            raise ValueError("Unknown-n report floor must be finite and nonnegative")
        scale = max(scale, unknown_n_floor)
    return float(scale)


def attach_precision_annotation(record, annotation):
    """Attach a compiler-resolved annotation to a fresh record in place."""
    if annotation is None:
        return record
    record["source_type"] = annotation["source_type"]
    if "report_log_scale" in annotation:
        record["report_log_scale"] = annotation["report_log_scale"]
    record.setdefault("provenance", {})["report_scale_basis"] = annotation["report_scale_basis"]
    precision_annotation(record)
    return record
