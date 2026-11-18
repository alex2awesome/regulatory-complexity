"""Strict semantic declarations for overlapping prior-preserving ESS blocks."""

from __future__ import annotations

import numpy as np


VERSION = "sampler-joint-blocks/1"
OVERLAP_POLICY = "sequential_invariant_kernels"


def compile_sampler_joint_blocks(declaration, model):
    """Resolve semantic selectors to existing iid-N(0,1) coordinates.

    This allocates no parameters and changes no density or transform. Blocks may
    overlap existing blocks: sequential composition of invariant ESS kernels is
    invariant, while each update still uses the full current likelihood.
    """
    if not isinstance(declaration, dict) or set(declaration) != {
            "schema_version", "overlap_policy", "blocks"}:
        raise ValueError("Sampler joint blocks require an exact v1 declaration")
    if declaration["schema_version"] != VERSION:
        raise ValueError("Unsupported sampler joint block schema")
    if declaration["overlap_policy"] != OVERLAP_POLICY:
        raise ValueError("Sampler joint blocks require sequential_invariant_kernels overlap policy")
    if not isinstance(declaration["blocks"], list) or not declaration["blocks"]:
        raise ValueError("Sampler joint blocks require a nonempty blocks list")
    result=[]; identifiers=set()
    programs={p["id"]:p for p in model.programs}
    for raw in declaration["blocks"]:
        if not isinstance(raw, dict) or set(raw) != {"id", "rationale", "selectors"}:
            raise ValueError("Each sampler joint block requires id, rationale, and selectors")
        ident,rationale=raw["id"],raw["rationale"]
        if (not isinstance(ident,str) or not ident.strip() or ident in identifiers
                or not isinstance(rationale,str) or not rationale.strip()
                or not isinstance(raw["selectors"],list) or not raw["selectors"]):
            raise ValueError("Sampler joint blocks need distinct IDs, rationale, and selectors")
        identifiers.add(ident); coordinates=[]
        for selector in raw["selectors"]:
            if not isinstance(selector,dict) or "kind" not in selector:
                raise ValueError("Sampler joint block selectors require a kind")
            kind=selector["kind"]
            if kind == "source_type_effect":
                if set(selector) != {"kind","source_type"} or model.source_offset_hierarchy is None:
                    raise ValueError("source_type_effect requires an active source hierarchy")
                try: coordinates.append(model.source_offset_hierarchy.type_coordinates[selector["source_type"]])
                except KeyError as error: raise ValueError("Unknown nonreference source type effect") from error
            elif kind == "operation_location_design_group":
                if set(selector) != {"kind","group"} or model.operation_location_design is None:
                    raise ValueError("operation_location_design_group requires an active design")
                positions=[i for i,t in enumerate(model.operation_location_design["terms"])
                           if t["group"] == selector["group"]]
                if not positions: raise ValueError("Unknown operation location design group")
                coordinates.extend(model.operation_location_design_coordinates[positions])
            elif kind == "operation_residuals":
                if set(selector) != {"kind","program_ids"} or not isinstance(selector["program_ids"],list):
                    raise ValueError("operation_residuals requires program_ids")
                if len(set(selector["program_ids"])) != len(selector["program_ids"]):
                    raise ValueError("operation_residuals program IDs must be distinct")
                for pid in selector["program_ids"]:
                    if pid not in programs: raise ValueError("Unknown joint-block program ID: "+str(pid))
                    coordinates.extend(model.operation[0,programs[pid]["global_indices"]])
            else:
                raise ValueError("Unknown sampler joint block selector kind: "+str(kind))
        coordinates=np.asarray(coordinates,dtype=int)
        if len(coordinates)<2 or len(set(map(int,coordinates)))!=len(coordinates):
            raise ValueError("A sampler joint block needs at least two distinct coordinates")
        result.append(dict(id=ident,rationale=rationale,coordinates=coordinates,
                           selectors=raw["selectors"]))
    return tuple(result)
