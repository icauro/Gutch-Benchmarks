"""Local BuildPatchTool capture, installation, and independently verified recovery."""

from ..scheduling.dataset import DatasetSelection
from ..support.command import CommandError
from ..support.filesystem import file_sha256, scan_tree
from ..support.recovery import capture_metrics, recovery_checks, validate_installation
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
        before = scan_tree(cloud).total_bytes
        result = commands.run([
            executable, "-mode=ChunkBuildDirectory", f"-BuildRoot={source.as_posix()}",
            f"-CloudDir={cloud.as_posix()}", "-ArtifactId=ComparisonBenchmark", "-FeatureLevel=Latest",
            # These are data-only comparisons. BPT automatically marks AppLaunch
            # executable, which would change metadata on Windows ZIP inputs.
            f"-BuildVersion={source.name}", "-AppLaunch=", "-AppArgs=",
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

    def restore(record_snapshots, *, clean=False):
        total = 0.0
        operation = "restore" if record_snapshots else "in-place recovery"
        for source in reversed(dataset.sources):
            destination = output / source.name
            result = commands.run([
                executable, "-mode=InstallManifest",
                f"-Manifest={manifests[source.name].as_posix()}",
                f"-CloudDirs={cloud.as_posix()}", f"-OutputDir={destination.as_posix()}",
                *([] if record_snapshots or clean else [f"-PrevManifest={manifests[source.name].as_posix()}"]),
            ], description=f"BuildPatchTool {operation} {source.name}", cwd=lane.root)
            total += result.elapsed_seconds
            if record_snapshots:
                snapshots[source.name]["restore"] = result.elapsed_seconds
        return total

    restored = restore(True)
    validation_seconds = validate_installation(dataset, output, lane.stats, "restored")
    recovery, operations = {}, {}
    if recovery_enabled:
        recovery, operations = recovery_checks(dataset, lane, output, lambda operation: restore(False),
                                               lambda: restore(False, clean=True), delete_extra=False)
    return LaneResult(specification.label, specification.kind,
                      metrics={"backup": elapsed, "restore": restored, "repo_size": stored.total_bytes,
                               "repo_files": stored.file_count, "restore_validated": restored + validation_seconds,
                               **capture_metrics(snapshots), **recovery},
                      metadata={**dataset.metadata(), "status": "PASS", "measurement_contract": 2,
                                "recovery_mode": "restore_existing",
                                "extra_file_policy": "no_native_delete_option",
                                "snapshot_metrics": snapshots, "binary_sha256": file_sha256(executable),
                                "operations": {"capture": "PASS", "clean_restore": "PASS", **operations}})
