"""Translate reviewed solar episode clocks to existing marginal V6 inputs.

No text inference and no new model. Clocks stay separate, including clocks that
cannot be compared with SolarTRACE. Every decision is retained in consumption.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from ..prepare_conditional_frames import prepare
from ...recon.solar_review_packet import decision_case_id, load_sources, resolve_ref

ROOT = Path(__file__).resolve().parents[3]
DEFAULT = ROOT / "runs/solar_forum_20260922/parse/root_decisions001.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def load_clock_aliases(path):
    """Read opt-in, claim-scoped endpoint aliases; never infer them from names."""
    if path is None:
        return {}
    packet = json.loads(path.read_bytes())
    if (packet.get("schema_version") != "solar-clock-aliases/1"
            or packet.get("adoption_state") != "adopted"):
        raise ValueError("Clock aliases require an adopted solar-clock-aliases/1 packet")
    aliases = {}
    for row in packet["aliases"]:
        source, target = row.get("from"), row.get("to")
        if (not isinstance(source, str) or not source or not isinstance(target, str)
                or not target or source == target or source in aliases
                or not row.get("rationale")
                or not isinstance(row.get("eligible_source_claim_ids"), list)
                or not row["eligible_source_claim_ids"]
                or any(not isinstance(i, str) for i in row["eligible_source_claim_ids"])):
            raise ValueError("Each alias needs distinct endpoints and reviewed source claim IDs")
        aliases[source] = row
    if any(row["to"] in aliases for row in aliases.values()):
        raise ValueError("Clock aliases must resolve directly, not through a chain")
    return aliases


def resolve_clock_alias(clock, source_claim_id, aliases):
    row = aliases.get(clock)
    if row is not None and source_claim_id in row["eligible_source_claim_ids"]:
        return row["to"]
    return clock


def interval(row):
    """Declared rounding intervals, never exchange clock starts or censor types."""
    # Parser vocabulary aliases are normalized here, not dropped at the model
    # boundary. Bare "days" retains the existing calendar-day working convention.
    unit=row.get("unit", "calendar_days")
    if unit=="days":
        unit="calendar_days"
    factor = {"calendar_days": 1., "business_days": 7./5., "weeks": 7.,
              "months": 365.25/12., "years": 365.25}[unit]
    note = " Bare days are interpreted as calendar days, not a business-day claim." if row.get("unit")=="days" else ""
    if row.get("unit") == "business_days":
        note += " Business-to-calendar conversion 7/5 is an explicit weekend-only approximation."
    if row.get("unit") == "years":
        note += " Verbal years use 365.25 calendar days per year; precision is represented by the declared interval/approximate flag."
    value = row.get("value")
    if "start_date" in row and "end_date" in row:
        value = (dt.date.fromisoformat(row["end_date"]) - dt.date.fromisoformat(row["start_date"])).days
        factor = 1.
        note += " Date-only difference, rounded to plus/minus one calendar day."
    censor = row.get("censoring", "completed")
    approximate=bool(row.get("approximate"))
    if censor=="completed_approximate":
        censor="completed"
        approximate=True
        note += " completed_approximate is normalized to a completed interval with explicit approximate-report width."
    if "start_date" in row and "end_date" not in row:
        if censor not in {"right","right_bound_uncertain","completed_lower_bound","left","left_interval","interval"}:
            raise ValueError("A lone start date requires an explicit reported bound, not an invented end date")
        note += " Known start date retained as context; explicit duration bound used without inventing an end date."
    if censor == "left_interval":
        censor = "left"
        note += " Extraction label left_interval is normalized to the same completed upper-bound interval likelihood."
    if censor not in {"completed", "completed_lower_bound", "right", "right_bound_uncertain", "left", "interval"}:
        raise ValueError("Unrecognized timing censoring label: " + str(censor))
    if censor == "completed_lower_bound":
        return row["lower"]*factor, None, "completed_lower_bound", note + " Completion is known, but the reported duration is only bounded below."
    if censor == "right":
        return max(.01, (value if value is not None else row["lower"])*factor - 1.), None, "pending_right_censored", note
    if censor == "right_bound_uncertain":
        return row["lower"]*factor, None, "pending_right_censored", note + " Conservative lower endpoint of uncertain pending-duration bound."
    if censor == "left":
        return 0., row["upper"]*factor, "completed_interval", note + " Completed duration stated below upper bound."
    if censor == "interval":
        return row["lower"]*factor, row["upper"]*factor, "completed_interval", note
    width = max(1., .15*value*factor) if approximate else 1.
    return max(0., value*factor - width), value*factor + width, "completed_interval", note + " Point reports widened by one calendar day; approximate reports by max(one day,15 percent)."


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--decisions", type=Path, default=DEFAULT)
    ap.add_argument("--add-decisions", type=Path, action="append", default=[],
                    help="Additional reviewed packets in the same schema; duplicate case IDs fail rather than silently double counting")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--clock-aliases", type=Path,
                    help="Opt-in adopted, claim-scoped exact endpoint aliases; original labels stay in provenance")
    ap.add_argument("--fit-prepared", action="store_true", help="Run the existing marginal V6 implementation on the prepared finite queue")
    args = ap.parse_args()
    args.out = args.out.resolve()
    args.decisions = args.decisions.resolve()
    args.add_decisions = [p.resolve() for p in args.add_decisions]
    if args.clock_aliases:
        args.clock_aliases = args.clock_aliases.resolve()
    if args.fit_prepared:
        from ..bayes_trace_hierarchy import Config
        from ..marginal_conditional_frames import run_marginal_frame
        queue = json.loads((args.out / "fit_queue.json").read_bytes())
        summaries = []
        for item in queue:
            data_path, config_path, fit_path = (ROOT/item[k] for k in ("data", "config", "fit"))
            if (fit_path/"posterior.json").exists():
                result = json.loads((fit_path/"posterior.json").read_bytes())
            else:
                values = json.loads(config_path.read_bytes())
                values["modeled_channels"] = tuple(values["modeled_channels"])
                cfg = Config(**values)
                print("Fitting existing marginal V6", item["clock"], item["cases"], flush=True)
                result = run_marginal_frame(json.loads(data_path.read_bytes()), cfg, fit_path,
                    [data_path, config_path, args.decisions, *args.add_decisions, Path(__file__).resolve()],
                    quadrature_size=256, workers=2)
            summary = dict(item, numerically_usable=result["numerically_usable"],
                dimensions=result["dimensions"], diagnostics_flagged=result["diagnostics_flagged"],
                programs=result["programs"], qualification=result["qualification"])
            summaries.append(summary)
            write(args.out/"fit_summary.json", summaries)
            print(item["clock"], "numerically_usable", result["numerically_usable"], flush=True)
        return
    if args.out.exists():
        raise FileExistsError(args.out)
    args.out.mkdir(parents=True)
    decisions = json.loads(args.decisions.read_bytes())
    if decisions.get("adoption_state", "adopted") != "adopted":
        raise ValueError("Timing fits require an adopted successor, not a staged semantic packet")
    for path in args.add_decisions:
        extra = json.loads(path.read_bytes())
        if extra.get("adoption_state", "adopted") != "adopted":
            raise ValueError("Timing fits require adopted packets: " + str(path))
        decisions["episodes"].extend(extra["episodes"])
        decisions["threads"] = sorted(set(decisions["threads"]) | set(extra["threads"]))
        decisions["source_packets"] = sorted(set(decisions.get("source_packets", [])) |
                                            set(extra.get("source_packets", [])))
    ids = [decision_case_id(e) for e in decisions["episodes"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Repeated case IDs need an explicit reconciled successor packet, not independent rows")
    # A reviewed later thread can add a different clock for an existing case.
    # Aliases must explicitly name a canonical case in these same input packets;
    # merely sharing a username never authorizes a merge.
    def case_identity(episode):
        target = episode.get("same_installation_as")
        if target is not None and target not in ids:
            raise ValueError("Case alias has no canonical case in the supplied packets: " + target)
        return target or decision_case_id(episode)
    registry_cases = list(dict.fromkeys(case_identity(e) for e in decisions["episodes"]))
    if any(e.get("same_installation_as") and any(
            decision_case_id(other) == e["same_installation_as"] and other.get("same_installation_as")
            for other in decisions["episodes"]) for e in decisions["episodes"]):
        raise ValueError("Case aliases must resolve directly, not through an alias chain")
    comments, posts = load_sources()
    clock_aliases = load_clock_aliases(args.clock_aliases)
    groups, consumption = defaultdict(list), []
    seen_case_clocks = set()
    raw_bindings = {str(p.relative_to(ROOT)): sha(p) for p in [args.decisions, *args.add_decisions]}
    if args.clock_aliases:
        raw_bindings[str(args.clock_aliases.relative_to(ROOT))] = sha(args.clock_aliases)
    for relative in decisions.get("source_packets", []):
        path = ROOT / relative
        raw_bindings[relative] = sha(path)
    for episode in decisions["episodes"]:
        case = case_identity(episode)
        for number, timing in enumerate(episode.get("timing", [])):
            original_clock = timing["clock"]
            original_claim_id = "clock_" + hashlib.sha256((case+original_clock).encode()).hexdigest()[:16]
            clock = resolve_clock_alias(original_clock, original_claim_id, clock_aliases)
            if (case, clock) in seen_case_clocks:
                raise ValueError("Repeated same-case same-clock observation must be reconciled first")
            seen_case_clocks.add((case, clock))
            lower, upper, kind, assumption = interval(timing)
            source_records = []
            for ref in timing["refs"]:
                source = resolve_ref(episode["thread"], ref, comments, posts)
                # A byte-retained, literal decoded field is a stable text input
                # to the existing V6 preparer, which does not accept JSON paths.
                name = hashlib.sha256((str(source["path"])+source["json_path"]).encode()).hexdigest()[:24]
                text_path = args.out / "source_fields" / (name + ".txt")
                text_path.parent.mkdir(parents=True, exist_ok=True)
                if not text_path.exists():
                    text_path.write_text(source["text"], encoding="utf-8", newline="")
                raw_bindings[str(source["path"].relative_to(ROOT))] = sha(source["path"])
                if "underlying_artifact" in source:
                    raw = source["underlying_artifact"]
                    if sha(ROOT / raw["path"]) != raw["sha256"]:
                        raise ValueError("Underlying external capture hash mismatch")
                    raw_bindings[raw["path"]] = raw["sha256"]
                source_records.append({"path": str(text_path.relative_to(ROOT)),
                                       "sha256": sha(text_path), "quote_segments": [source["text"]]})
            ident = "clock_" + hashlib.sha256((case+clock).encode()).hexdigest()[:16]
            claim = dict(id=ident, registry_label_id=case, case_id=case,
                         observation_kind=kind, lower=lower, upper=upper,
                         interpretation=((timing.get("note") or "Reviewed named endpoints: " + clock) + assumption).strip(),
                         sources=source_records, logical_threads=[episode["thread"]])
            groups[clock].append(claim)
            consumption.append(dict(id=ident, case_id=case, clock=clock,
                original_clock=original_clock, original_claim_id=original_claim_id,
                clock_alias_applied=clock != original_clock, utility=episode.get("utility"),
                inherited_context=bool(episode.get("inherited_context")), original=timing,
                bounds_calendar_days=[lower, upper], observation_kind=kind,
                route="v6_conditional_report_frame"))
    queue = []
    for clock, claims in sorted(groups.items()):
        selected = {claim["case_id"] for claim in claims}
        registry = [dict(registry_label_id=case,
                         status="included" if case in selected else "excluded",
                         case_id=case if case in selected else None,
                         reason="Reviewed this clock" if case in selected else "No reviewed measurement of this distinct clock; not a zero duration")
                    for case in registry_cases]
        spec = dict(schema_version="reviewed-conditional-frame-input/1", id="solar_"+clock,
            target="Calendar-day " + clock + " within the reviewed solar forum report frame",
            source_family="solar_forum_"+args.decisions.stem,
            eligibility="One first-person report per reviewed author-installation and this clock, including pending/interval reports",
            generalization_limit="Interim selected " + str(len(decisions["threads"])) + "-thread report frame, pooled utilities and eras. Not all California applicants, intrinsic agency capability, calibrated source bias, or an administrative matching sample.",
            elapsed_time_unit="calendar_days",
            coarsening_assumption=dict(kind="assumed_ignorable_within_report_frame",
                rationale="Use reported bounds rather than treating unfinished cases as completed; reporting-time selection is unmeasured.",
                sensitivity_plan="Compare completed-only and explicitly located/contextual subsets after corpus expansion; no population transport claim.",
                informative_posting_unmodeled=True),
            registry_rows=registry, claims=claims,
            conditions=[dict(id="mixed", observation_ids=[c["id"] for c in claims],
                config_overrides=dict(chains=4, warmup=1000, draws=2000, population_size=32,
                    elapsed_prior_median=7., location_sd=2., case_log_sd_median=1., case_log_sd_prior=.5),
                subset_reason="All reviewed records with this clock; mixed completed and pending as applicable")],
            input_bindings=[dict(path=p, sha256=s) for p,s in sorted(raw_bindings.items())])
        spec_path = args.out / (clock + "_spec.json")
        write(spec_path, spec)
        prepared = args.out / clock
        prepare(spec_path, prepared, ROOT, workers=2)
        completed = sum(c["observation_kind"] == "completed_interval" for c in claims)
        queue.append(dict(clock=clock, cases=len(claims), completed_cases=completed,
                          data=str((prepared/"mixed_data.json").relative_to(ROOT)),
                          config=str((prepared/"mixed_config.json").relative_to(ROOT)),
                          fit=str((prepared/"fit_marginal").relative_to(ROOT)),
                          headline_eligible=completed>=3 and clock != "pto_wait_unspecified_start",
                          headline_qualification="Even eligible rows are conditional report-frame summaries, not applicant-population or agency-capability estimates."))
    write(args.out/"fit_queue.json", queue)
    write(args.out/"model_consumption.json", dict(claims=consumption, claim_count=len(consumption),
        cases=len(registry_cases),
        registered_case_identities=len(registry_cases),
        timing_contributing_case_identities=len({r["case_id"] for r in consumption}),
        cases_field_qualification="Legacy cases field counts the whole identity registry, including episodes without numeric timings; use timing_contributing_case_identities for fitted-case coverage.",
        episode_reports=len(decisions["episodes"]), clock_frames=len(groups),
        clock_aliases_binding=(dict(path=str(args.clock_aliases.relative_to(ROOT)), sha256=sha(args.clock_aliases))
                               if args.clock_aliases else None),
        clock_aliases_applied=sum(row["clock_alias_applied"] for row in consumption),
        explicit_same_installation_aliases={decision_case_id(e): e["same_installation_as"]
            for e in decisions["episodes"] if e.get("same_installation_as")},
        qualification="Separate conditional clock fits share cases; do not sum or multiply independent posterior draws as if joint."))
    print(json.dumps(queue, indent=2))


if __name__ == "__main__":
    main()
