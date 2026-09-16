"""Versioned, quote-checked interface between semantic interpretation and inference.

This module deliberately imports neither a benchmark truth reader nor an LLM.
JSON Schema is also the constrained-output contract given to the interpreter.
"""
from __future__ import annotations

import json
import math
import re
import copy

VERSION = "process-evidence/2"


def obj(**properties):
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


def arr(items):
    return {"type": "array", "items": items}


def enum(*values):
    return {"type": "string", "enum": list(values)}


STR = {"type": "string"}
NUM = {"type": ["number", "null"]}
TEXT = {"type": ["string", "null"]}
REF = obj(doc_id=STR, quote=STR)
STAGES = ("preparation", "submission", "intake", "review", "decision", "closeout",
          "enforcement", "appeal", "standing", "unknown")
TASKS = ("preparation", "filing", "payment", "completeness", "technical_review",
         "specialist_review", "handoff", "decision", "notification", "records",
         "inspection", "hearing", "enforcement", "publication", "reporting", "other")

SCHEMA = obj(
    schema_version=enum(VERSION), program_id=STR,
    actors=arr(obj(id=STR, name=STR, role=enum("payer", "agency", "third_party", "unknown"),
                   aliases=arr(STR), evidence=arr(REF))),
    activities=arr(obj(
        id=STR, name=STR, actor_id=STR, task_type=enum(*TASKS), stage=enum(*STAGES),
        scope=enum("core", "conditional", "standing", "out_of_scope"),
        condition=TEXT, existence=enum("explicit", "inferred", "ambiguous"),
        evidence=arr(REF), notes=STR)),
    relations=arr(obj(
        source=STR, target=STR, kind=enum("precedes", "parallel", "rework"),
        support=enum("explicit", "inferred"), condition=TEXT, evidence=arr(REF))),
    measurements=arr(obj(
        id=STR, metric=enum("elapsed", "payer_work", "agency_work", "fee", "staffing_fte", "annual_volume"),
        scope=enum("step", "segment", "process", "standing"), activity_ids=arr(STR),
        start=enum("activity_start", "preparation_start", "submission", "complete_application", "unspecified"),
        end=enum("activity_end", "decision", "closeout", "unspecified"),
        statistic=enum("individual", "typical", "mean", "median", "p90", "statutory_cap", "target", "estimate"),
        value=NUM, lower=NUM, upper=NUM,
        unit=enum("calendar_days", "business_days", "hours", "weeks", "months", "USD", "fte", "cases_per_year"),
        qualitative={"type": "boolean"}, n={"type": ["integer", "null"]},
        case_id=TEXT, cohort=TEXT, source_family=STR,
        doc_id=STR, quote=STR, interpretation=STR)),
    ambiguities=arr(obj(subject=STR, alternatives=arr(STR), evidence=arr(REF))),
    excluded=arr(obj(doc_id=STR, quote=STR, reason=STR)),
)

# Backward-compatible extension: old canonical ledgers remain valid; a separate
# source-only audit adds explicit observation context without rewriting claims.
OBSERVATION_CONTEXT = obj(measurement_id=STR,
    temporal_scope=enum('current', 'historical', 'hypothetical', 'unspecified'),
    required_activity_ids=arr(STR), excluded_activity_ids=arr(STR),
    decision_activity_id=TEXT,
    segment_mode=enum('performed_operations', 'branch_union', 'not_segment'),
    evidence=arr(REF), notes=STR)
# Optional in existing v3 ledgers; a separate source-only clock audit can add it.
OBSERVATION_CONTEXT['properties']['clock_start_after_activity_ids'] = arr(STR)
SCHEMA_V3 = copy.deepcopy(SCHEMA)
SCHEMA_V3['properties']['schema_version'] = enum('process-evidence/3')
SCHEMA_V3['properties']['observation_contexts'] = arr(OBSERVATION_CONTEXT)
SCHEMA_V3['required'].append('observation_contexts')


def normalized_quote(value):
    # Whitespace/Markdown emphasis are presentation, not semantic corrections.
    value = value.replace("**", "").replace("\u00a0", " ")
    value = re.sub(r'(?<!\w)\*([^*\n]+)\*(?!\w)', r'\1', value)
    return re.sub(r"\s+", " ", value).strip()


def validate(evidence, documents=None):
    import jsonschema
    try:
        jsonschema.validate(evidence, SCHEMA_V3 if evidence.get('schema_version') == 'process-evidence/3' else SCHEMA)
    except jsonschema.ValidationError as error:
        raise ValueError(f'evidence schema: {error.message}') from error
    errors = []
    actors = {a["id"]: a for a in evidence["actors"]}
    acts = {a["id"]: a for a in evidence["activities"]}
    for key in ("actors", "activities", "measurements"):
        ids = [x["id"] for x in evidence[key]]
        if len(ids) != len(set(ids)):
            errors.append(f"duplicate {key} IDs")
    for a in acts.values():
        if a["actor_id"] not in actors:
            errors.append(f"{a['id']}: unknown actor")
        if not a["evidence"]:
            errors.append(f"{a['id']}: no supporting quote")
    for r in evidence["relations"]:
        if r["source"] not in acts or r["target"] not in acts or (r["source"] == r["target"] and r['kind'] != 'rework'):
            errors.append("invalid relation endpoints: " + json.dumps(r))
    for m in evidence["measurements"]:
        units = {'elapsed': {'calendar_days', 'business_days', 'hours', 'weeks', 'months'},
                 'payer_work': {'hours'}, 'agency_work': {'hours'}, 'fee': {'USD'},
                 'staffing_fte': {'fte'}, 'annual_volume': {'cases_per_year'}}
        if m['unit'] not in units[m['metric']]:
            errors.append(f"{m['id']}: incompatible metric/unit")
        if any(m[k] is not None and not math.isfinite(m[k]) for k in ('value', 'lower', 'upper')):
            errors.append(f"{m['id']}: non-finite number")
        if any(i not in acts for i in m["activity_ids"]):
            errors.append(f"{m['id']}: unknown activity")
        if m["scope"] == "step" and len(m["activity_ids"]) != 1:
            errors.append(f"{m['id']}: step measurement must identify exactly one activity")
        if m["lower"] is not None and m["upper"] is not None and m["lower"] > m["upper"]:
            errors.append(f"{m['id']}: reversed interval")
        if any(m[k] is not None and m[k] < 0 for k in ("value", "lower", "upper")):
            errors.append(f"{m['id']}: negative burden")
        if m["statistic"] == "individual" and m['metric'] in {'elapsed', 'payer_work', 'agency_work'} and not m["case_id"]:
            errors.append(f"{m['id']}: individual requires a stable case ID")
        if m["n"] is not None and m["n"] < 1:
            errors.append(f"{m['id']}: sample size must be positive")
    seen_context = set()
    measurements = {m['id']: m for m in evidence['measurements']}
    for context in evidence.get('observation_contexts', []):
        mid = context['measurement_id']
        if mid not in measurements or mid in seen_context:
            errors.append(f'{mid}: unknown/repeated observation context')
        seen_context.add(mid)
        required, excluded = set(context['required_activity_ids']), set(context['excluded_activity_ids'])
        if not (required | excluded) <= set(acts) or required & excluded:
            errors.append(f'{mid}: invalid or contradictory route constraints')
        decision = context['decision_activity_id']
        if decision is not None and (decision not in acts or acts[decision]['stage'] != 'decision'
                                      or acts[decision]['task_type'] != 'decision'):
            errors.append(f'{mid}: context selects a non-decision operation')
        if not context['evidence']:
            errors.append(f'{mid}: context requires quoted support')
        after = set(context.get('clock_start_after_activity_ids', []))
        if not after <= set(acts):
            errors.append(f'{mid}: unknown clock-start milestone')
    if documents is not None:
        texts = {d["id"]: normalized_quote(d["text"]) for d in documents}
        refs = [x for key in ("actors", "activities", "relations", "ambiguities")
                for item in evidence[key] for x in item["evidence"]]
        refs += evidence["measurements"] + evidence["excluded"]
        refs += [ref for context in evidence.get('observation_contexts', []) for ref in context['evidence']]
        for ref in refs:
            q = normalized_quote(ref["quote"])
            if not q or q not in texts.get(ref["doc_id"], ""):
                errors.append(f"quote not verbatim in {ref['doc_id']}: {ref['quote'][:100]}")
    if errors:
        raise ValueError("\n".join(errors))
    return evidence
