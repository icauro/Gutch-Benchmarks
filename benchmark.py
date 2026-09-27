"""Prepare and execute a standalone comparison, independent of the CLI and UI."""

from dataclasses import replace
from functools import partial
import hashlib
import json
import os
import platform
from pathlib import Path
import shutil

import yaml

from .datasets import prepare_dataset
from .scheduling.runner import execute_cases
from .scheduling.dataset import DatasetSelection
from .support.artifacts import RunLayout, create_run_dir
from .support.command import CommandRunner, redact_output
from .support.commands import GutchCli
from .support.filesystem import file_sha256
from .tools.config import load_fixture
from .tools.external import ExternalTools
from .tools.models import LaneResult
from .tools.report import write_comparison_report
from .tools.workflow import LocalFixtureRunner


def resolve_executable(value: str, fixture: Path, tools_root: Path) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Executable names must be nonempty strings.")
    candidate = Path(value).expanduser()
    if candidate.is_absolute() or candidate.parent != Path("."):
        candidate = (fixture.parent / candidate).resolve()
        return candidate if candidate.is_file() else None
    host = {"Windows": "windows-x64", "Linux": "linux-x64"}.get(platform.system())
    if host and platform.machine().lower() in {"amd64", "x86_64"}:
        tool = "gutch" if value in {"gutch", "gutch-cli"} else value.lower()
        executable = "gutch-cli" if tool == "gutch" else value
        folder = tools_root / host / tool
        if tool == "buildpatchtool":
            target = "Win64/BuildPatchTool.exe" if host == "windows-x64" else "Linux/BuildPatchTool"
            bundled = folder / "Engine/Binaries" / target
        else:
            bundled = folder / (executable + (".exe" if host == "windows-x64" else ""))
        if bundled.is_file():
            return bundled.resolve()
    found = shutil.which(value)
    return Path(found).resolve() if found else None


def suite_source_hash(root: Path) -> str:
    source_hash = hashlib.sha256()
    runtime_files = list(root.glob("*.py"))
    for directory in ("support", "scheduling", "tools"):
        runtime_files.extend((root / directory).glob("*.py"))
    for path in sorted(runtime_files):
        source_hash.update(path.relative_to(root).as_posix().encode())
        source_hash.update(b"\0" + hashlib.sha256(path.read_bytes()).digest())
    return source_hash.hexdigest()


def operation_statuses(tool: str, recovery_enabled: bool, recovery_failed: bool) -> dict[str, str]:
    statuses = dict.fromkeys(
        ("in_place_repair", "full_restore_recovery", "update", "rollback", "no_op_restore"), "NOT_RUN",
    )
    statuses.update(capture="PASS", clean_restore="PASS")
    if recovery_enabled:
        operation = "full_restore_recovery" if tool == "filesystem" else "in_place_repair"
        statuses[operation] = "FAIL" if recovery_failed else "PASS"
    return statuses


def run_benchmark(root: Path, fixture_name: str, *, open_perfetto: bool | None = None) -> int:
    fixture_path = Path(fixture_name).expanduser()
    if not fixture_path.exists():
        fixture_path = root / "fixtures" / fixture_name
        if not fixture_path.exists() and fixture_path.suffix == "":
            fixture_path = fixture_path.with_suffix(".yaml")
    if fixture_path.is_dir():
        fixture_path /= "fixture.yaml"
    fixture_path = fixture_path.resolve()
    fixture = load_fixture(fixture_path)
    if open_perfetto is not None:
        fixture = replace(fixture, open_perfetto=open_perfetto)
    values = yaml.safe_load(fixture_path.read_text(encoding="utf-8"))
    executables = values.get("executables", {})
    if not isinstance(executables, dict):
        raise ValueError("executables must map candidate names to executable paths.")
    resolved = {}
    unavailable = {}
    for lane in fixture.lanes:
        if lane.tool == "filesystem":
            continue
        configured = executables.get(lane.label, executables.get(lane.tool, lane.tool))
        if lane.tool == "gutch" and configured in {"gutch", "gutch-cli"}:
            configured = os.environ.get("GUTCH_EXECUTABLE", configured)
        executable = resolve_executable(configured, fixture_path, root / ".artifacts/tools")
        if executable is None:
            unavailable[lane.label] = f"Cannot find {configured!r}; set executables.{lane.label} in {fixture_path} or add it to PATH."
            print(f"UNAVAILABLE {lane.label}: {unavailable[lane.label]}", flush=True)
        else:
            resolved[lane.label] = executable
    if all(lane.label in unavailable for lane in fixture.lanes):
        raise ValueError("None of the configured tools are available.")
    warmups = values.get("warmups", 1)
    if isinstance(warmups, bool) or warmups not in (0, 1):
        raise ValueError("warmups must be 0 or 1")
    artifacts = root / ".artifacts"
    print("Preparing and validating input builds...", flush=True)
    product, dataset_metadata = prepare_dataset(values, fixture_path, artifacts)
    dataset = DatasetSelection.resolve(product, fixture.snapshot_limit)
    if warmups:
        fixture = replace(fixture, lanes=tuple(replace(lane, warmup=True) for lane in fixture.lanes) + fixture.lanes)
    layout = RunLayout(create_run_dir(artifacts / "runs", fixture.name, "comparison"), retain_evidence=True)
    print(f"Running {fixture.name}. Results: {layout.root}", flush=True)
    if fixture.description:
        print(fixture.description, flush=True)
    layout.write_manifest("preparing", suite_source_sha256=suite_source_hash(root), dataset=dataset_metadata,
                          executables={label: {"path": str(path), "sha256": file_sha256(path)} for label, path in resolved.items()})
    commands = CommandRunner(memory_profile=fixture.profile_mode == "detailed",
                             on_step=lambda description: print(f"Step: {description}", flush=True))
    runners = {}
    for lane in fixture.lanes:
        if lane.label in runners or lane.label in unavailable or lane.tool == "buildpatchtool":
            continue
        binary = resolved.get(lane.label, Path("unavailable"))
        external_paths = {lane.tool: binary} if lane.tool in {"restic", "kopia", "borg", "plakar"} else {}
        external = ExternalTools(commands, **external_paths)
        runners[lane.label] = LocalFixtureRunner(GutchCli(binary, profile_mode=fixture.profile_mode), commands, layout, external)

    def execute(lane):
        # Scheduled labels include repetition suffixes; configuration labels do not.
        label = lane.configuration_label or lane.label
        if label in unavailable:
            return LaneResult(lane.label, lane.kind, metadata={"status": "UNAVAILABLE", "reason": unavailable[label]})
        try:
            if lane.tool == "buildpatchtool":
                from .tools.buildpatchtool import run_buildpatchtool
                return run_buildpatchtool(resolved[label], commands, layout.lane(lane.label), product, lane,
                                          dataset=dataset,
                                          recovery_enabled=fixture.corrupt_repair)
            result = runners[label].run_lane(product, lane, fixture.corrupt_repair, snapshot_limit=fixture.snapshot_limit, dataset=dataset)
            result.metadata.setdefault("status", "PASS")
            result.metadata["operations"] = operation_statuses(
                lane.tool, fixture.corrupt_repair, bool(result.metadata.get("recovery_error")),
            )
            return result
        except Exception as error:
            return LaneResult(lane.label, lane.kind, metadata={"status": "ERROR", "reason": redact_output(str(error))})

    completed = 0
    total = sum(not lane.warmup for lane in fixture.lanes) * fixture.repetitions
    def completed_case(result):
        nonlocal completed
        completed += 1
        print(f"{result.label}: {result.metadata['status']}", flush=True)
        print(f"Progress: {completed}/{total} measured cases", flush=True)
        if completed == total:
            print("Step: Building reports and finalizing the run", flush=True)
    execute_cases(fixture, layout, commands, execute, executable=resolved.get("gutch", Path("unavailable")),
                            on_lane_complete=completed_case,
                            on_run_complete=partial(write_comparison_report, layout.root, fixture.description))
    print(f"Report: {layout.root / 'summary.md'}", flush=True)
    return 1 if json.loads((layout.root / "run.json").read_text(encoding="utf-8"))["status"] == "failed" else 0
