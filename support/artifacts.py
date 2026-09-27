"""Run and retention layout for benchmark artifacts."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path
import re
import time

from comparison_benchmark_suite.support.filesystem import remove_tree
from .retention import compact_success, prune_successful_runs
from .retention import remove_owned
import tempfile


def safe_component(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")
    if cleaned in {"", ".", ".."}:
        raise ValueError(f"invalid artifact name: {value!r}")
    return cleaned


def compact_component(value: str, maximum: int) -> str:
    cleaned = safe_component(value)
    if len(cleaned) <= maximum:
        return cleaned
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]
    return f"{cleaned[:maximum - 9]}-{digest}"


def create_run_dir(root: Path, source_name: str, fixture_name: str) -> Path:
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y.%m.%d")
    prefix = f"{stamp}-{compact_component(source_name, 16)}-{compact_component(fixture_name, 24)}"
    for sequence in range(1, 1000):
        candidate = root / f"{prefix}-{sequence:03d}"
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:
            continue
    raise RuntimeError(f"could not allocate run directory under {root}")


@dataclass
class LaneLayout:
    root: Path
    stats: Path
    traces: Path
    payload: Path
    _created_at: float = field(default_factory=time.perf_counter, repr=False)


@dataclass
class RunLayout:
    root: Path
    cleanup_actions: list = field(default_factory=list, repr=False)
    retain_evidence: bool = False

    def lane(self, label: str) -> LaneLayout:
        lane_root = self.root / "lanes" / compact_component(label, 32)
        stats = lane_root / "stats"
        traces = lane_root / "traces"
        payload = lane_root / "payload"
        for directory in (stats, traces, payload):
            directory.mkdir(parents=True, exist_ok=True)
        return LaneLayout(lane_root, stats, traces, payload)

    def write_manifest(self, status: str, **details) -> None:
        target = self.root / "run.json"
        previous = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}
        previous.update(details)
        previous.update(status=status, updated_at=datetime.now(timezone.utc).isoformat())
        self.write_json(target, previous)

    def write_json(self, target: Path, value) -> None:
        def portable(item):
            if isinstance(item, dict):
                return {key: portable(child) for key, child in item.items()}
            if isinstance(item, (list, tuple)):
                return [portable(child) for child in item]
            if isinstance(item, (str, Path)):
                path = Path(item)
                if path.is_absolute():
                    try:
                        return path.relative_to(self.root.resolve()).as_posix()
                    except ValueError:
                        pass
            return item
        value = portable(value)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
        temporary.replace(target)

    def write_results(self, results: list[dict]) -> None:
        target = self.root / "results.json"
        self.write_json(target, results)

    def remove_payloads(self) -> None:
        payload_root = self.root / "lanes"
        if not payload_root.exists():
            return
        for lane in payload_root.iterdir():
            if lane.is_dir():
                remove_owned(lane / "payload", self.root)
                for name in ("restic-cache", "kopia-cache", "borg-cache"):
                    remove_owned(lane / name, self.root)
                from comparison_benchmark_suite.tools.external import _plakar_cache_directory
                cache = _plakar_cache_directory(lane)
                for attempt in range(41):
                    try:
                        remove_owned(cache, Path(tempfile.gettempdir()))
                        break
                    except OSError as error:
                        # Plakar's cache helper can briefly outlive its CLI on
                        # Windows. Wait only for this run-owned cache to close.
                        if getattr(error, "winerror", None) not in {32, 33} or attempt == 40:
                            raise
                        if attempt == 0:
                            print("Waiting for the Plakar cache to close...", flush=True)
                        time.sleep(0.25)

    def finish(self, *, keep=False):
        if not keep:
            for action in self.cleanup_actions:
                action()
            self.remove_payloads()
        reports = ("run.json", "results.json", "summary.json", "summary.md", "trace.json")
        if not self.retain_evidence:
            compact_success(self.root, keep=keep, reports=reports)
        self.write_manifest("passed", cleanup_complete=True, keep_artifacts=keep,
                            detailed_evidence_retained=keep or self.retain_evidence)
        prune_successful_runs(self.root.parent)
