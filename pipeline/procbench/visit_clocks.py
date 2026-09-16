"""Deterministic observation operators for a *realized* process trace.

This module has no truth-reader, LLM, priors or inference. A future visit-based
hierarchy can call the same operators for every latent trace draw. It must not
replace that posterior with a single guessed trace. All timestamps are elapsed
calendar days on one case clock; labor is separately supplied person-hours.
"""
from dataclasses import dataclass
import math


MARKERS={'submission','complete_submission','decision','legal_closeout'}
ROLES={'payer','agency','third_party','unknown'}


@dataclass(frozen=True)
class Visit:
    visit_id: str
    activity_id: str
    start: float
    end: float
    actor_id: str | None = None
    actor_role: str = 'unknown'
    markers: tuple[str,...] = ()
    service_start: float | None = None
    payer_hours: float | None = None
    agency_hours: float | None = None
    fee_dollars: float | None = None

    def __post_init__(self):
        object.__setattr__(self,'markers',tuple(self.markers))
        if not all(isinstance(x,str) and x.strip() for x in (self.visit_id,self.activity_id)) or self.actor_role not in ROLES:
            raise ValueError('Visits require stable visit/activity IDs and a typed actor role')
        if self.actor_id is not None and (not isinstance(self.actor_id,str) or not self.actor_id.strip()):
            raise ValueError('Unknown actor identity must be None, not a fabricated empty identifier')
        if not all(math.isfinite(x) for x in (self.start,self.end)) or self.end<self.start:
            raise ValueError('Visit calendar endpoints must be finite and ordered')
        if len(set(self.markers))!=len(self.markers) or not set(self.markers)<=MARKERS:
            raise ValueError('Unknown or duplicated event marker')
        if self.service_start is not None and not self.start<=self.service_start<=self.end:
            raise ValueError('Service start must lie inside the visit cycle')
        for x in (self.payer_hours,self.agency_hours,self.fee_dollars):
            if x is not None and (not math.isfinite(x) or x<0):
                raise ValueError('Separate resource amounts must be finite and nonnegative')


@dataclass(frozen=True)
class Trace:
    visits: tuple[Visit,...]
    process_start: float = 0.

    def __post_init__(self):
        object.__setattr__(self,'visits',tuple(self.visits))
        if not all(isinstance(v,Visit) for v in self.visits):
            raise ValueError('Trace must contain typed visits')
        if not math.isfinite(self.process_start):
            raise ValueError('Nonfinite process start')
        if len({v.visit_id for v in self.visits})!=len(self.visits):
            raise ValueError('A repeated operation needs a distinct visit ID')
        if any(v.start<self.process_start for v in self.visits):
            raise ValueError('A visit cannot precede the declared process start')

    def event(self,name):
        if name=='process_start':
            return self.process_start
        if name=='modeled_work_end':
            return max((v.end for v in self.visits),default=None)
        marker,which={
            'first_submission':('submission',min),
            'first_complete_submission':('complete_submission',min),
            'initial_decision':('decision',min),
            'last_decision':('decision',max),
            'legal_closeout':('legal_closeout',max),
        }.get(name,(None,None))
        if marker is None:
            raise ValueError('Unsupported event clock: '+name)
        return which((v.end for v in self.visits if marker in v.markers),default=None)

    def interval(self,start,end):
        """Missing events return None, not a zero-day completion."""
        a,b=self.event(start),self.event(end)
        if a is None or b is None:
            return None
        if b<a:
            raise ValueError('Clock endpoint precedes its start')
        return b-a

    def activity_time(self,activity_id,basis,visit='all'):
        """Cycle sums, stage spans, waiting and service have different operators.

        A service interval is elapsed service time, *not* person-hours. Multiple
        staff, interrupted work and simultaneous cases require separate labor data.
        """
        rows=sorted((v for v in self.visits if v.activity_id==activity_id),key=lambda v:(v.start,v.end,v.visit_id))
        if visit=='first':
            rows=rows[:1]
        elif visit=='last':
            rows=rows[-1:]
        elif visit!='all':
            rows=[v for v in rows if v.visit_id==visit]
        if basis not in {'cycle','stage_span','waiting','service'}:
            raise ValueError('Unsupported activity-duration basis')
        if not rows:
            return None
        if basis=='stage_span':
            return max(v.end for v in rows)-min(v.start for v in rows)
        if basis=='cycle':
            return sum(v.end-v.start for v in rows)
        if any(v.service_start is None for v in rows):
            return None
        if basis=='waiting':
            return sum(v.service_start-v.start for v in rows)
        return sum(v.end-v.service_start for v in rows)

    def through(self,event,touch_rule):
        """Explicitly choose started versus completed work at a decision boundary.

        This filters a realized trace, not an observation-date censoring model.
        A last decision in a latent completed trace is not necessarily the latest
        recorded decision in an incomplete administrative extract.
        """
        end=self.event(event)
        if touch_rule not in {'started','completed'}:
            raise ValueError('Count boundary must explicitly say started or completed')
        if end is None:
            return None
        # Decisions at the boundary are included, while work starting precisely
        # afterward cannot be distinguished by coarse timestamps. The caller's
        # trace must retain order if that distinction matters; do not invent it.
        field='start' if touch_rule=='started' else 'end'
        return Trace(tuple(v for v in self.visits if getattr(v,field)<=end),self.process_start)

    def burden(self,operation_identity=None):
        """Burden conditional on this trace and one operation-identity hypothesis.

        Missing agencies/hours never become tight zeroes. Resource sums of known
        amounts are lower bounds for these represented visits, not estimates of
        unobserved visits or unidentified standing obligations.
        """
        identity=({v.activity_id:v.activity_id for v in self.visits}
                  if operation_identity is None else operation_identity)
        if any(v.activity_id not in identity or not identity[v.activity_id] for v in self.visits):
            raise ValueError('Operation-identity map must cover every represented activity')
        known_agencies={v.actor_id for v in self.visits if v.actor_role=='agency' and v.actor_id is not None}
        unresolved=[v.visit_id for v in self.visits if v.actor_role=='unknown' or
                    (v.actor_role=='agency' and v.actor_id is None)]
        result=dict(visits=len(self.visits),distinct_operations=len({identity[v.activity_id] for v in self.visits}),
            known_agencies=sorted(known_agencies),
            agency_count=len(known_agencies) if not unresolved else None,
            known_agency_count_lower_bound=len(known_agencies),unattributed_visit_ids=unresolved)
        for field in ('payer_hours','agency_hours','fee_dollars'):
            amounts=[getattr(v,field) for v in self.visits]
            missing=[v.visit_id for v,x in zip(self.visits,amounts) if x is None]
            lower=sum(x for x in amounts if x is not None)
            result[field]=dict(total=None if missing else lower,known_sum_lower_bound=lower,
                               missing_visit_ids=missing)
        return result
