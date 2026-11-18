"""Validated scientific settings, separate from computational execution choices."""
from dataclasses import asdict, dataclass, fields
import math


def _construct(cls, value):
    if isinstance(value, cls):
        return value
    value = {} if value is None else dict(value)
    unknown = set(value) - {f.name for f in fields(cls)}
    if unknown:
        raise ValueError(f"unknown {cls.__name__} fields: {sorted(unknown)}")
    return cls(**value)


@dataclass(frozen=True)
class ModelConfig:
    day_grid_size: int = 512
    hour_grid_size: int = 512
    max_loops: int = 4
    contamination_probability: float = .02
    contamination_max_days: int = 365
    # None preserves the evidence-declared range (legacy fallback 10..150).
    post_day_range: tuple | None = None
    process_family: str = "serial_completeness_loop"
    observation_family: str = "complete_partition_uniform_posting"
    # Opt-in (real records, 2026-10-01): mix the same numeric contamination into administrative
    # milestone GAP values that totals already get. Event-set mismatches stay impossible. Default
    # False keeps the exact-milestone target of all synthetic worlds unchanged.
    milestone_contamination: bool = False
    # Opt-in (real records, 2026-10-01): open/pending cases get the same contamination mixture,
    # P(T > N) = (1-c) S_model(N) + c S_contam(N). Stale "open" records (aged years) otherwise each
    # contribute log(1e-300). Ages beyond contamination_max_days get no contamination mass, so set
    # it above the oldest open age. Default False keeps the synthetic-world target unchanged.
    pending_contamination: bool = False
    # Real-corpus sensitivity: no synthetic timestamp-mask or posting process.
    score_timing_mask: bool = True
    completion_selection: bool = True

    def __post_init__(self):
        for name in ("milestone_contamination", "pending_contamination", "score_timing_mask", "completion_selection"):
            if not isinstance(getattr(self, name), bool):
                raise ValueError(f"{name} must be a boolean")
        for name in ("day_grid_size", "hour_grid_size", "max_loops", "contamination_max_days"):
            x = getattr(self, name)
            if isinstance(x, bool) or not isinstance(x, int) or x < (0 if name == "max_loops" else 2):
                raise ValueError(f"invalid {name}")
        if not math.isfinite(self.contamination_probability) or not 0 <= self.contamination_probability < 1:
            raise ValueError("contamination_probability must be in [0,1)")
        if self.post_day_range is not None:
            r = tuple(self.post_day_range)
            if len(r) != 2 or any(isinstance(v, bool) or not isinstance(v, int) for v in r) or not 0 <= r[0] <= r[1]:
                raise ValueError("post_day_range must be two ordered nonnegative integers")
            object.__setattr__(self, "post_day_range", r)
        if self.process_family != "serial_completeness_loop":
            raise ValueError("unsupported process_family; concurrent graphs need an explicit likelihood extension")
        if self.observation_family != "complete_partition_uniform_posting":
            raise ValueError("unsupported observation_family; partial reports/selection need an explicit likelihood extension")

    @classmethod
    def parse(cls, value=None):
        return _construct(cls, value)

    def to_dict(self):
        d = asdict(self)
        if d["post_day_range"] is not None:
            d["post_day_range"] = list(d["post_day_range"])
        return d


@dataclass(frozen=True)
class ExecutionConfig:
    backend: str = "cpu"
    kernel: str = "joint"
    batch_size: int = 256
    bucket_towns: bool = True
    hmc_steps: int = 8
    hmc_step_size: float = .1
    refresh_prior_only: bool = False

    def __post_init__(self):
        if self.backend not in ("cpu", "jax") or self.kernel not in ("joint", "blocked", "hmc"):
            raise ValueError("unsupported backend/kernel")
        if (self.backend == "cpu" and self.kernel == "hmc") or (self.backend == "jax" and self.kernel == "blocked"):
            raise ValueError("HMC requires JAX; cached blocked moves currently require CPU")
        for name in ("batch_size", "hmc_steps"):
            v = getattr(self, name)
            if isinstance(v, bool) or not isinstance(v, int) or v < 1:
                raise ValueError(f"{name} must be a positive integer")
        if not isinstance(self.bucket_towns, bool) or not isinstance(self.refresh_prior_only, bool):
            raise ValueError("bucket_towns and refresh_prior_only must be boolean")
        if not math.isfinite(self.hmc_step_size) or self.hmc_step_size <= 0:
            raise ValueError("hmc_step_size must be positive and finite")

    @classmethod
    def parse(cls, value=None):
        return _construct(cls, value)


class ParameterDict(dict):
    """Carry model-local support to every shared estimand/reading consumer."""
    def __init__(self, values, model_config):
        super().__init__(values)
        self.model_config = model_config

    def copy(self):
        return ParameterDict(self, self.model_config)


def config_for_params(p):
    return getattr(p, "model_config", ModelConfig())
