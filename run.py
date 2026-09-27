"""Run a portable comparison: python run.py [--fixture NAME_OR_PATH]."""

import argparse
from dataclasses import replace
import json
import hashlib
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
if __package__ in {None, ""}:
    sys.path.insert(0, str(ROOT.parent))
    __package__ = "comparison_benchmark_suite"


def resolve_executable(value: str, fixture: Path) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Executable names must be nonempty strings.")
    candidate = Path(value).expanduser()
    if candidate.is_absolute() or candidate.parent != Path("."):
        candidate = (fixture.parent / candidate).resolve()
        return candidate if candidate.is_file() else None
    found = shutil.which(value)
    return Path(found).resolve() if found else None


def main(arguments=None) -> int:
    parser = argparse.ArgumentParser(description="Compare build storage tools. Results go to .artifacts/runs/.")
    parser.add_argument("--fixture", default="blender", help="Fixture name, directory, or YAML file")
    args = parser.parse_args(arguments)
    try:
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
        from .tools.report import ascii_comparison_table
        from .tools.workflow import LocalFixtureRunner
    except ImportError as error:
        print(f"Missing dependency: {error}. Run: python -m pip install -r requirements.txt", file=sys.stderr)
        return 2
    try:
        fixture_path = Path(args.fixture).expanduser()
        if not fixture_path.exists():
            fixture_path = ROOT / "fixtures" / args.fixture
        if fixture_path.is_dir():
            fixture_path /= "fixture.yaml"
        fixture_path = fixture_path.resolve()
        fixture = load_fixture(fixture_path)
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
            executable = resolve_executable(configured, fixture_path)
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
        artifacts = ROOT / ".artifacts"
        product, dataset_metadata = prepare_dataset(values, fixture_path, artifacts)
        selections = {
            (product, fixture.snapshot_limit, whole): DatasetSelection.resolve(
                product, fixture.snapshot_limit, whole_product=whole,
            )
            for whole in {lane.workload in {"product-bulk", "exact-bulk"} for lane in fixture.lanes}
        }
        if warmups:
            fixture = replace(fixture, lanes=tuple(replace(lane, warmup=True) for lane in fixture.lanes) + fixture.lanes)
        layout = RunLayout(create_run_dir(artifacts / "runs", fixture.name, "comparison"), retain_evidence=True)
        source_hash = hashlib.sha256()
        runtime_files = list(ROOT.glob("*.py"))
        for directory in ("support", "scheduling", "tools"):
            runtime_files.extend((ROOT / directory).glob("*.py"))
        for path in sorted(runtime_files):
            source_hash.update(path.relative_to(ROOT).as_posix().encode())
            source_hash.update(b"\0" + hashlib.sha256(path.read_bytes()).digest())
        layout.write_manifest("preparing", suite_source_sha256=source_hash.hexdigest(), dataset=dataset_metadata,
                              executables={label: {"path": str(path), "sha256": file_sha256(path)} for label, path in resolved.items()})
        commands = CommandRunner(memory_profile=fixture.profile_mode == "detailed")
        runners = {}
        for lane in fixture.lanes:
            binary = resolved.get(lane.label, Path("unavailable"))
            external = ExternalTools(ROOT, commands, **({lane.tool: binary} if lane.tool in {"restic", "kopia", "borg", "plakar"} else {}))
            runners[lane.label] = LocalFixtureRunner(GutchCli(binary, profile_mode=fixture.profile_mode), commands, layout, external)
            runners[lane.label].selections = selections

        def execute(lane):
            # Scheduled labels include repetition suffixes; configuration labels do not.
            label = lane.configuration_label or lane.label
            if label in unavailable:
                return LaneResult(lane.label, lane.kind, metadata={"status": "UNAVAILABLE", "reason": unavailable[label]})
            try:
                if lane.tool == "buildpatchtool":
                    from .tools.buildpatchtool import run_buildpatchtool
                    return run_buildpatchtool(resolved[label], commands, layout.lane(lane.label), product, lane,
                                              dataset=selections[(product, fixture.snapshot_limit, False)],
                                              recovery_enabled=fixture.corrupt_repair)
                result = runners[label].run_lane(product, lane, fixture.corrupt_repair, snapshot_limit=fixture.snapshot_limit)
                result.metadata.setdefault("status", "PASS")
                result.metadata["operations"] = {
                    "capture": "PASS", "clean_restore": "PASS",
                    "in_place_repair": ("FAIL" if result.metadata.get("recovery_error") else "PASS")
                        if fixture.corrupt_repair and lane.tool != "filesystem" else "NOT_RUN",
                    "full_restore_recovery": "PASS" if fixture.corrupt_repair and lane.tool == "filesystem" else "NOT_RUN",
                    "update": "NOT_RUN", "rollback": "NOT_RUN", "no_op_restore": "NOT_RUN",
                }
                return result
            except Exception as error:
                return LaneResult(lane.label, lane.kind, metadata={"status": "ERROR", "reason": redact_output(str(error))})

        def report(results):
            summary = json.loads((layout.root / "summary.json").read_text(encoding="utf-8"))
            lines = ["# Comparison benchmark", "", "OS cache state: uncontrolled. Times are median seconds.", "",
                     "| Candidate | Status | Capture | Restore | In-place repair | Full recovery | Stored MiB |",
                     "|---|---|---:|---:|---:|---:|---:|"]
            rows = []
            for label, metrics in summary.items():
                samples = [result for result in results if result.metadata["case"] == label]
                statuses = ", ".join(sorted({result.metadata["status"] for result in samples}))
                def value(key, divisor=1):
                    median = metrics.get(key, {}).get("median") if isinstance(metrics.get(key), dict) else None
                    return "-" if median is None else f"{median / divisor:.3f}"
                row = [label, statuses, value('backup'), value('restore'), value('repair'),
                       value('full_restore_recovery'), value('repo_size', 1048576)]
                rows.append(row)
                lines.append("| " + " | ".join(row) + " |")
            reasons = dict.fromkeys(result.metadata["reason"] for result in results if result.metadata.get("reason"))
            lines.extend(["", *reasons, "", "Restore includes the tool's own verification. Independent SHA-256 validation is outside command timing.",
                          "", "Raw samples and operation semantics: results.json. Aggregate medians and ranges: summary.json. Perfetto overview: trace.json (compacted tool time; harness gaps omitted, not concurrent execution)."])
            (layout.root / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
            print("\nComparison: median seconds across measured runs; warm-ups excluded.")
            print(ascii_comparison_table(rows))
            print("Repair = in-place; recovery = full restore. '-' = not measured.")
            print("Independent validation is outside timings. OS cache is uncontrolled.")
            for reason in reasons:
                print(reason)


        print(f"Running {fixture.name}. Results: {layout.root}", flush=True)
        results = execute_cases(fixture, layout, commands, execute, executable=resolved.get("gutch", Path("unavailable")),
                                on_lane_complete=lambda result: print(f"{result.label}: {result.metadata['status']}", flush=True),
                                on_run_complete=report)
        print(f"Report: {layout.root / 'summary.md'}", flush=True)
        return 1 if json.loads((layout.root / "run.json").read_text(encoding="utf-8"))["status"] == "failed" else 0
    except (OSError, ValueError, RuntimeError, yaml.YAMLError) as error:
        print(f"Comparison benchmark: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
