"""Local BuildPatchTool capture, installation, and independently verified recovery."""

from pathlib import Path
import time

from ..scheduling.dataset import DatasetSelection
from ..support.command import CommandError
from ..support.filesystem import file_sha256, scan_tree
from ..support.recovery import build_corruption_plan, apply_corruption_plan
from .models import LaneResult


def run_buildpatchtool(executable, commands, lane, product, specification, *, dataset=None, recovery_enabled=False):
    try:
        probe = commands.run(
            [executable, "-mode=ChunkBuildDirectory", "-help"],
            description="BuildPatchTool local generation capabilities",
        )
    except CommandError as error:
        probe = error.result
    help_text = probe.stdout + probe.stderr
    required = ("BuildRoot", "CloudDir", "ArtifactId", "FeatureLevel", "ChunkWindowSize", "BuildVersion", "AppLaunch", "AppArgs")
    # The Epic Store uploader is not the same interface as the local engine tool.
    # Do not guess credentials or substitute a publishing operation.
    if probe.returncode != 0 or not all(name.lower() in help_text.lower() for name in required) or any(
        name.lower() in help_text.lower() for name in ("ClientSecret", "OrganizationID")
    ):
        return LaneResult(specification.label, specification.kind, metadata={
            "status": "UNSUPPORTED",
            "reason": "This executable does not advertise the supported local ChunkBuildDirectory interface. Upload modes are not benchmarked.",
            "binary_sha256": file_sha256(executable),
        })
    dataset = dataset or DatasetSelection.resolve(product)
    cloud = lane.payload / "cloud"
    cloud.mkdir(parents=True, exist_ok=True)
    snapshots = dataset.snapshot_metrics()
    manifests = {}
    elapsed = 0.0
    for source in dataset.sources:
        files = [name for name, item in dataset.inventories[source.name].items() if item["kind"] == "file"]
        if not files:
            raise ValueError("BuildPatchTool generation requires a nonempty build.")
        launch = next((name for name in files if Path(name).name in {"blender", "blender.exe"}), files[0])
        before = scan_tree(cloud).total_bytes
        result = commands.run([
            executable, "-mode=ChunkBuildDirectory", f"-BuildRoot={source.as_posix()}",
            f"-CloudDir={cloud.as_posix()}", "-ArtifactId=ComparisonBenchmark", "-FeatureLevel=Latest",
            f"-BuildVersion={source.name}", f"-AppLaunch={launch}", "-AppArgs=",
            *specification.arguments, f"-OutputFilename={source.name}.manifest",
        ], description=f"BuildPatchTool generate {source.name}", cwd=lane.root)
        elapsed += result.elapsed_seconds
        after = scan_tree(cloud).total_bytes
        manifest = cloud / f"{source.name}.manifest"
        if not manifest.is_file():
            raise RuntimeError(f"BuildPatchTool returned success without generating {manifest.name}.")
        manifests[source.name] = manifest
        snapshots[source.name].update(backup=result.elapsed_seconds, repo_growth_bytes=after - before)
    stored = scan_tree(cloud)
    output = lane.payload / "installation"

    def restore(record_snapshots):
        total = 0.0
        operation = "restore" if record_snapshots else "in-place recovery"
        for source in reversed(dataset.sources):
            destination = output / source.name
            result = commands.run([
                executable, "-mode=InstallManifest",
                f"-Manifest={manifests[source.name].as_posix()}",
                f"-CloudDirs={cloud.as_posix()}", f"-OutputDir={destination.as_posix()}",
                *([] if record_snapshots else [f"-PrevManifest={manifests[source.name].as_posix()}"]),
            ], description=f"BuildPatchTool {operation} {source.name}", cwd=lane.root)
            total += result.elapsed_seconds
            if record_snapshots:
                snapshots[source.name]["restore"] = result.elapsed_seconds
        return total

    restored = restore(True)
    for source in dataset.sources:
        dataset.validate(source, output / source.name, lane.stats / f"validate-restored-{source.name}.json")
    recovery = {}
    recovery_error = None
    if recovery_enabled:
        plans = [(output / source.name, build_corruption_plan(
            output / source.name, lane.stats / f"corruption-{index:03d}.json", index,
        )) for index, source in enumerate(reversed(dataset.sources), 1)]
        started = time.perf_counter()
        for destination, plan in plans:
            apply_corruption_plan(destination, plan)
        recovery["corrupt"] = time.perf_counter() - started
        try:
            repair_seconds = restore(False)
            for source in dataset.sources:
                dataset.validate(source, output / source.name, lane.stats / f"validate-final-{source.name}.json")
            recovery["repair"] = repair_seconds
        except (CommandError, RuntimeError) as error:
            recovery_error = str(error)
    return LaneResult(specification.label, specification.kind,
                      metrics={"backup": elapsed, "restore": restored, "repo_size": stored.total_bytes,
                               "repo_files": stored.file_count, **recovery},
                      metadata={**dataset.metadata(), "status": "ERROR" if recovery_error else "PASS",
                                "reason": recovery_error, "recovery_error": recovery_error,
                                "recovery_mode": "restore_existing",
                                "extra_file_policy": "no_native_delete_option",
                                "snapshot_metrics": snapshots, "binary_sha256": file_sha256(executable),
                                "operations": {"capture": "PASS", "clean_restore": "PASS",
                                               "full_restore_recovery": "NOT_RUN",
                                               "in_place_repair": ("FAIL" if recovery_error else "PASS") if recovery_enabled else "NOT_RUN", "update": "NOT_RUN",
                                               "rollback": "NOT_RUN", "no_op_restore": "NOT_RUN"}})
