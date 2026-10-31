"""Domain objects for Gutch fixture workflows."""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


from comparison_benchmark_suite.support.models import GutchProfile


@dataclass(frozen=True)
class LaneSpec:
    label: str
    tool: str
    profile: GutchProfile | None = None
    warmup: bool = False
    arguments: tuple[str, ...] = ()
    workload: str = "individual"
    configuration_label: str = ""
    resource_sample: bool = False

    @property
    def kind(self) -> str:
        return "filesystem-copy" if self.tool == "filesystem" else f"{self.tool}-{self.workload}"


@dataclass(frozen=True)
class FixtureSpec:
    name: str
    runner: str
    description: str
    delete_artifacts: bool
    open_perfetto: bool
    lanes: tuple[LaneSpec, ...]
    source_path: Path
    corrupt_repair: bool = False
    lane_wait_seconds: float = 4.0
    step_wait_seconds: float = 4.0
    snapshot_limit: int | None = None
    repetitions: int = 1
    profile_mode: str = "off"
    resource_sampling: bool = False


@dataclass
class LaneResult:
    label: str
    kind: str
    metrics: dict[str, float | int] = field(default_factory=dict)
    traces: dict[str, list[str]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_json(self) -> dict[str, Any]:
        return asdict(self)
