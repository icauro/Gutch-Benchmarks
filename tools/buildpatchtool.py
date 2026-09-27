"""Local BuildPatchTool generation; never upload or emulate installation."""

from pathlib import Path

from ..scheduling.dataset import DatasetSelection
from ..support.command import CommandError
from ..support.filesystem import file_sha256, scan_tree
from .models import LaneResult


def run_buildpatchtool(executable, commands, lane, product, specification, *, dataset=None):
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
    snapshots = {}
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
            *specification.arguments,
        ], description=f"BuildPatchTool generate {source.name}", cwd=lane.root)
        elapsed += result.elapsed_seconds
        after = scan_tree(cloud).total_bytes
        if not scan_tree(cloud).file_count:
            raise RuntimeError("BuildPatchTool returned success without generating any files.")
        snapshots[source.name] = {"backup": result.elapsed_seconds, "repo_growth_bytes": after - before}
    return LaneResult(specification.label, specification.kind,
                      metrics={"backup": elapsed, "repo_size": scan_tree(cloud).total_bytes},
                      metadata={**dataset.metadata(), "status": "CAPTURE_ONLY",
                                "snapshot_metrics": snapshots, "binary_sha256": file_sha256(executable),
                                "reason": "Local generation completed. Restore, update, repair, and restored-content validation are UNSUPPORTED by this adapter; capture correctness is not established by an exit code."})
