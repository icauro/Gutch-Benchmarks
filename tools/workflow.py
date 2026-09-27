"""Local Gutch fixture execution.

The workflow deliberately treats reconstruct verification as part of the
reconstruct command.  It reads the embedded verification timing from the
reconstruct stats and never starts a second snapshot-verify command.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
import shutil
import time
from collections.abc import Callable

from comparison_benchmark_suite.support.artifacts import LaneLayout, RunLayout, create_run_dir
from comparison_benchmark_suite.support.command import CommandRunner
from comparison_benchmark_suite.support.filesystem import remove_tree, scan_tree
from comparison_benchmark_suite.support.recovery import apply_corruption_plan, build_corruption_plan
from comparison_benchmark_suite.support.commands import GutchCli
from comparison_benchmark_suite.tools.external import ExternalTools, run_external
from comparison_benchmark_suite.tools.models import FixtureSpec, LaneResult, LaneSpec


from comparison_benchmark_suite.support.gutch import GutchOperations, snapshot_id as _snapshot_id, verification_seconds as _verify_seconds
from comparison_benchmark_suite.scheduling.dataset import select_sources as _selected_product_sources, DatasetSelection
from comparison_benchmark_suite.scheduling.runner import execute_cases


@dataclass
class LocalFixtureRunner:
    cli: GutchCli
    commands: CommandRunner
    run: RunLayout
    external: ExternalTools | None = None

    def __post_init__(self):
        self.gutch = GutchOperations(self.cli, self.commands)
        self.selections = {}

    def _run_individual(
        self,
        lane: LaneLayout,
        dataset: DatasetSelection,
        lane_spec: LaneSpec,
        recovery_enabled: bool,
    ) -> LaneResult:
        product = dataset.product
        repo = lane.payload / "repo"
        output = lane.payload / "installation"
        remove_tree(repo)
        remove_tree(output)
        self.gutch.init_repo(repo, lane_spec.label)
        sources = list(dataset.sources)
        if not sources:
            raise ValueError(f"product has no target directories: {product}")
        snapshot_metrics = dataset.snapshot_metrics()
        backup_times: list[float] = []
        snapshots: list[tuple[str, str, Path]] = []
        capture_traces: list[str] = []
        for index, source in enumerate(sources, start=1):
            capture_stats = lane.stats / f"capture-{index:03d}.json"
            capture_trace = lane.traces / f"capture-{index:03d}" / "trace.json"
            elapsed, stats = self.gutch.capture(repo, source, lane_spec.profile, capture_stats, capture_trace, lane_spec.label)
            backup_times.append(elapsed)
            snapshot_metrics[source.name]["backup"] = elapsed
            capture_traces.append(str(capture_trace))
            destination = output / source.name
            snapshots.append((source.name, _snapshot_id(stats), destination))
        return self._restore_gutch_snapshots(
            lane, dataset, lane_spec, snapshots, sum(backup_times),
            capture_traces, snapshot_metrics, recovery_enabled,
        )

    def _restore_gutch_snapshots(
        self,
        lane: LaneLayout,
        dataset: DatasetSelection,
        lane_spec: LaneSpec,
        snapshots: list[tuple[str, str, Path]],
        capture_seconds: float,
        capture_traces: list[str],
        snapshot_metrics: dict,
        recovery_enabled: bool,
    ) -> LaneResult:
        """Restore newest first, validate, then optionally corrupt and repair."""
        repo = lane.payload / "repo"
        output = lane.payload / "installation"
        sources = dataset.sources
        restore_seconds = 0.0
        verify_seconds = 0.0
        traces = {"capture": capture_traces, "reconstruct": [], "corrupt": [], "repair": []}
        repo_stats = scan_tree(repo)
        reconstructed: list[tuple[str, str, Path]] = []
        for index, (name, snapshot_id, destination) in enumerate(reversed(snapshots), start=1):
            reconstruct_stats = lane.stats / f"reconstruct-{index:03d}.json"
            reconstruct_trace = lane.traces / f"reconstruct-{index:03d}" / "trace.json"
            elapsed, stats = self.gutch.reconstruct(
                repo,
                snapshot_id,
                destination,
                lane_spec.profile,
                reconstruct_stats,
                reconstruct_trace,
                f"{lane_spec.label} {name}",
            )
            restore_seconds += elapsed
            snapshot_metrics[name]["restore"] = elapsed
            verify_seconds = _add_optional(verify_seconds, _verify_seconds(stats))
            traces["reconstruct"].append(str(reconstruct_trace))
            reconstructed.append((name, snapshot_id, destination))
        for source in sources:
            dataset.validate(source, output / source.name, lane.stats / f"validate-restored-{source.name}.json")
        recovery: dict[str, float | list[str]] = {}
        if recovery_enabled:
            recovery = self.gutch.corrupt_and_repair(lane, repo, reconstructed, lane_spec.profile, lane_spec.label)
            traces["corrupt"].extend(recovery["corrupt_traces"])  # type: ignore[arg-type]
            traces["repair"].extend(recovery["repair_traces"])  # type: ignore[arg-type]
        for source in sources:
            dataset.validate(source, output / source.name, lane.stats / f"validate-final-{source.name}.json")
        return LaneResult(
            lane_spec.label,
            lane_spec.kind,
            {
                "backup": capture_seconds,
                "restore": restore_seconds,
                "verify": verify_seconds,
                "compare": 0.0,
                "corrupt": float(recovery.get("corrupt", 0.0)),
                "repair": float(recovery.get("repair", 0.0)),
                "repo_size": repo_stats.total_bytes,
                "repo_files": repo_stats.file_count,
            },
            traces,
            {
                "snapshot_metrics": snapshot_metrics,
                "verify_source": "reconstruct_stats.verify_timings.total_seconds",
                "verify_invocations": len(sources),
                "corrupt_repair_after_reconstruct": recovery_enabled,
                "differences": [],
            },
        )

    def _run_product_bulk(
        self,
        lane: LaneLayout,
        dataset: DatasetSelection,
        lane_spec: LaneSpec,
        recovery_enabled: bool,
    ) -> LaneResult:
        product = dataset.product
        repo = lane.payload / "repo"
        output = lane.payload / "installation"
        remove_tree(repo)
        remove_tree(output)
        self.gutch.init_repo(repo, lane_spec.label)
        capture_stats = lane.stats / "capture.json"
        capture_trace = lane.traces / "capture" / "trace.json"
        sources = _selected_product_sources(product)
        if not sources:
            raise ValueError(f"product has no target directories: {product}")
        backup, capture = self.gutch.capture(
            repo,
            product,
            lane_spec.profile,
            capture_stats,
            capture_trace,
            lane_spec.label,
            version_name=sources[-1].name,
        )
        repo_stats = scan_tree(repo)
        reconstruct_stats = lane.stats / "reconstruct.json"
        reconstruct_trace = lane.traces / "reconstruct" / "trace.json"
        restore, reconstruction = self.gutch.reconstruct(repo, _snapshot_id(capture), output, lane_spec.profile, reconstruct_stats, reconstruct_trace, lane_spec.label)
        dataset.validate(product, output, lane.stats / "validate-restored.json")
        snapshot_metrics = dataset.snapshot_metrics()
        snapshot_metrics[product.name].update(backup=backup, restore=restore)
        snapshots = [(product.name, _snapshot_id(capture), output)]
        recovery = self.gutch.corrupt_and_repair(lane, repo, snapshots, lane_spec.profile, lane_spec.label) if recovery_enabled else {}
        dataset.validate(product, output, lane.stats / "validate-final.json")
        return LaneResult(
            lane_spec.label,
            lane_spec.kind,
            {
                "backup": backup,
                "restore": restore,
                "verify": _verify_seconds(reconstruction),
                "compare": 0.0,
                "corrupt": float(recovery.get("corrupt", 0.0)),
                "repair": float(recovery.get("repair", 0.0)),
                "repo_size": repo_stats.total_bytes,
                "repo_files": repo_stats.file_count,
            },
            {
                "capture": [str(capture_trace)],
                "reconstruct": [str(reconstruct_trace)],
                "corrupt": recovery.get("corrupt_traces", []),
                "repair": recovery.get("repair_traces", []),
            },
            {
                "snapshot_metrics": snapshot_metrics,
                "verify_source": "reconstruct_stats.verify_timings.total_seconds",
                "verify_invocations": 1,
                "corrupt_repair_after_reconstruct": recovery_enabled,
                "differences": [],
            },
        )

    def _run_batch(
        self,
        lane: LaneLayout,
        dataset: DatasetSelection,
        lane_spec: LaneSpec,
        recovery_enabled: bool,
    ) -> LaneResult:
        product = dataset.product
        repo = lane.payload / "repo"
        output = lane.payload / "installation"
        remove_tree(repo)
        remove_tree(output)
        self.gutch.init_repo(repo, lane_spec.label)
        sources = list(dataset.sources)
        if not sources:
            raise ValueError(f"product has no target directories: {product}")
        capture_stats = lane.stats / "capture-many.json"
        capture_trace = lane.traces / "capture-many" / "trace.json"
        backup, capture = self.gutch.capture_many(repo, product, lane_spec.profile, capture_stats, capture_trace, lane_spec.label, lane_spec.label)
        snapshots = capture.get("snapshots", [])
        by_name = {
            Path(item["input_path"]).name: str(item["snapshot_id"])
            for item in snapshots
            if isinstance(item, dict) and item.get("input_path") and item.get("snapshot_id")
        }
        missing = [source.name for source in sources if source.name not in by_name]
        if missing:
            raise ValueError(f"capture-many stats omitted snapshots: {missing}")
        snapshots = [(source.name, by_name[source.name], output / source.name) for source in sources]
        return self._restore_gutch_snapshots(
            lane, dataset, lane_spec, snapshots, backup, [str(capture_trace)],
            dataset.snapshot_metrics(), recovery_enabled,
        )

    def _run_copy(
        self,
        lane: LaneLayout,
        dataset: DatasetSelection,
        lane_spec: LaneSpec,
        recovery_enabled: bool,
    ) -> LaneResult:
        repo = lane.payload / "repo"
        output = lane.payload / "installation"
        remove_tree(repo)
        remove_tree(output)
        snapshot_metrics = dataset.snapshot_metrics()
        for source in dataset.sources:
            started = time.perf_counter()
            shutil.copytree(source, repo / source.name, symlinks=True)
            snapshot_metrics[source.name]["backup"] = time.perf_counter() - started
            self.commands.record_operation(f"capture {source.name}", started, snapshot_metrics[source.name]["backup"])
        repo_stats = scan_tree(repo)

        def restore_output(record_snapshots: bool) -> float:
            total = 0.0
            for source in reversed(dataset.sources):
                started = time.perf_counter()
                shutil.copytree(repo / source.name, output / source.name, symlinks=True)
                elapsed = time.perf_counter() - started
                operation = "restore" if record_snapshots else "full recovery"
                self.commands.record_operation(f"{operation} {source.name}", started, elapsed)
                total += elapsed
                if record_snapshots:
                    snapshot_metrics[source.name]["restore"] = elapsed
            return total

        restore = restore_output(True)
        for source in dataset.sources:
            dataset.validate(source, output / source.name, lane.stats / f"validate-restored-{source.name}.json")
        recovery = {}
        if recovery_enabled:
            destinations = [output / source.name for source in reversed(dataset.sources)]
            plans = [build_corruption_plan(destination, lane.stats / f"corruption-{index:03d}.json", index)
                     for index, destination in enumerate(destinations, start=1)]
            started = time.perf_counter()
            for destination, plan in zip(destinations, plans, strict=True):
                apply_corruption_plan(destination, plan)
            recovery["corrupt"] = time.perf_counter() - started
            remove_tree(output)
            recovery["full_restore_recovery"] = restore_output(False)
        for source in dataset.sources:
            dataset.validate(source, output / source.name, lane.stats / f"validate-final-{source.name}.json")
        return LaneResult(
            lane_spec.label,
            lane_spec.kind,
            {
                "backup": sum(values["backup"] for values in snapshot_metrics.values()),
                "restore": restore,
                "repo_size": repo_stats.total_bytes,
                "repo_files": repo_stats.file_count,
                "compare": 0.0,
                **recovery,
            },
            {},
            {
                "snapshot_metrics": snapshot_metrics,
                "verify_source": "not_applicable",
                "verify_invocations": 0,
                "corrupt_repair_after_reconstruct": recovery_enabled,
                "differences": [],
            },
        )

    def run_lane(self, product, lane_spec, recovery_enabled=False, snapshot_limit=None):
        whole_product = lane_spec.workload in {"product-bulk", "exact-bulk"}
        key = (product, snapshot_limit, whole_product)
        if key not in self.selections:
            self.selections[key] = DatasetSelection.resolve(product, snapshot_limit, whole_product=whole_product)
        selection = self.selections[key]
        result = self._execute_lane(selection, lane_spec, recovery_enabled, snapshot_limit)
        result.metadata.update(selection.metadata(), configuration=asdict(lane_spec))
        result.metrics.update(input_bytes=selection.input_bytes, input_files=selection.input_files)
        return result

    def _execute_lane(
        self,
        dataset: DatasetSelection,
        lane_spec: LaneSpec,
        recovery_enabled: bool = False,
        snapshot_limit: int | None = None,
    ) -> LaneResult:
        if lane_spec.kind.startswith(("restic-", "kopia-", "borg-", "plakar-")):
            if self.external is None:
                raise RuntimeError("external benchmark tools are not configured")
            return run_external(
                self.external,
                self.run.lane(lane_spec.label),
                dataset.product,
                lane_spec,
                recovery_enabled=recovery_enabled,
                snapshot_limit=snapshot_limit,
                dataset=dataset,
            )
        lane = self.run.lane(lane_spec.label)
        if lane_spec.kind == "gutch-individual":
            return self._run_individual(
                lane,
                dataset,
                lane_spec,
                recovery_enabled,
            )
        if lane_spec.kind == "gutch-product-bulk":
            return self._run_product_bulk(lane, dataset, lane_spec, recovery_enabled)
        if lane_spec.kind == "gutch-batch":
            return self._run_batch(lane, dataset, lane_spec, recovery_enabled)
        if lane_spec.kind == "filesystem-copy":
            return self._run_copy(lane, dataset, lane_spec, recovery_enabled)
        raise ValueError(f"unsupported benchmark lane kind: {lane_spec.kind}")


def run_fixture(
    fixture: FixtureSpec,
    product: Path,
    cli: GutchCli,
    artifacts_root: Path,
    *,
    keep_artifacts: bool,
    repo_root: Path | None = None,
    on_lane_complete: Callable[[LaneResult], None] | None = None,
    on_run_complete: Callable[[list[LaneResult]], None] | None = None,
    on_step: Callable[[str], None] | None = None,
    external_binary_root: Path | None = None,
) -> list[LaneResult]:
    if fixture.snapshot_limit is not None:
        supported_kinds = {
            "gutch-individual",
            "filesystem-copy",
            "restic-individual",
            "kopia-individual",
            "borg-individual",
            "plakar-individual",
        }
        unsupported = sorted(
            {lane.kind for lane in fixture.lanes if lane.kind not in supported_kinds}
        )
        if unsupported:
            raise ValueError(
                "snapshot_limit is only supported for individual snapshot lanes: "
                + ", ".join(unsupported)
            )
    run_root = create_run_dir(artifacts_root, product.name, fixture.name)
    layout = RunLayout(run_root)
    commands = CommandRunner(step_wait_seconds=fixture.step_wait_seconds, on_step=on_step, memory_profile=fixture.profile_mode == "detailed")
    external = ExternalTools(repo_root or Path(__file__).resolve().parents[1], commands)
    if external_binary_root is not None:
        external = ExternalTools(
            external.repo_root,
            commands,
            restic=external_binary_root / "restic",
            kopia=external_binary_root / "kopia",
            borg=external_binary_root / "borg" if any(lane.tool == "borg" for lane in fixture.lanes) else None,
            plakar=external_binary_root / "plakar",
        )
    if any(lane.tool == "borg" for lane in fixture.lanes):
        external.check_borg_version()
    cli = GutchCli(cli.executable, profile_mode=fixture.profile_mode)
    runner = LocalFixtureRunner(
        cli,
        commands,
        layout,
        external,
    )
    return execute_cases(fixture, layout, commands,
        lambda case: runner.run_lane(product, case, fixture.corrupt_repair, snapshot_limit=fixture.snapshot_limit),
        executable=cli.executable, keep_artifacts=keep_artifacts,
        on_lane_complete=on_lane_complete, on_run_complete=on_run_complete)


def _add_optional(left, right):
    return None if left is None or right is None else left + right
