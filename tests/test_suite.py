"""Portable entry point, owned inputs, failure isolation, and capability checks."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from comparison_benchmark_suite.datasets import extract_archive, prepare_dataset
from comparison_benchmark_suite.support.command import CommandResult
from comparison_benchmark_suite.support.artifacts import RunLayout
from comparison_benchmark_suite.tools.buildpatchtool import run_buildpatchtool
from comparison_benchmark_suite.tools.models import LaneSpec


class SuiteTests(unittest.TestCase):
    def setUp(self):
        owner = ROOT / ".artifacts" / "tests"
        owner.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=owner)
        self.root = Path(self.temporary.name).resolve()
        assert self.root.is_relative_to(owner.resolve())
        self.addCleanup(self.temporary.cleanup)

    def inputs(self):
        builds = []
        for index in (1, 2):
            source = self.root / f"release-{index}"
            source.mkdir()
            (source / "empty").mkdir()
            (source / "file.txt").write_text(f"version {index}", encoding="utf-8")
            builds.append({"path": str(source)})
        return builds

    def test_copied_suite_runs_without_repository_and_preserves_inputs(self):
        standalone = self.root / "comparison_benchmark_suite"
        shutil.copytree(ROOT, standalone, ignore=shutil.ignore_patterns(".artifacts", "__pycache__", ".venv"))
        builds = self.inputs()
        fixture = standalone / "fixtures" / "custom" / "fixture.yaml"
        fixture.parent.mkdir()
        fixture.write_text(yaml.safe_dump({
            "name": "custom", "builds": builds, "warmups": 1, "repetitions": 2,
            "corrupt_repair": True, "lane_wait_seconds": 0, "step_wait_seconds": 0,
            "lanes": [{"label": "filesystem", "tool": "filesystem"},
                      {"label": "not-installed", "tool": "gutch"}],
            "executables": {"not-installed": str(self.root / "missing-tool")},
        }), encoding="utf-8")
        env = dict(os.environ, PYTHONPATH="")
        env.pop("GUTCH_EXECUTABLE", None)
        result = subprocess.run([sys.executable, standalone / "run.py", "--fixture", "custom"],
                                cwd=self.root, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("| Tool", result.stdout)
        self.assertIn("Stored MiB", result.stdout)
        self.assertIn("not-installed", result.stdout)
        self.assertIn("UNAVAILABLE", result.stdout)
        self.assertIn("'-' = not measured", result.stdout)
        run = next((standalone / ".artifacts/runs").iterdir())
        results = json.loads((run / "results.json").read_text())
        self.assertEqual(len(results), 4)
        self.assertEqual({r["metadata"]["status"] for r in results}, {"PASS", "UNAVAILABLE"})
        self.assertFalse(any((run / "lanes").glob("*/payload")))
        self.assertTrue((run / "summary.md").exists())
        events = json.loads((run / "trace.json").read_text())["traceEvents"]
        spans = [event for event in events if event["ph"] == "X"]
        self.assertEqual(len(spans), 12)  # Capture, restore, recovery x two builds x two measured runs.
        self.assertTrue(all(event["dur"] > 0 for event in spans))
        self.assertFalse(any("warmup" in event.get("args", {}).get("name", "") for event in events))
        for index, build in enumerate(builds, 1):
            self.assertEqual((Path(build["path"]) / "file.txt").read_text(), f"version {index}")

    def test_timeline_compacts_gaps_and_keeps_engine_threads(self):
        from comparison_benchmark_suite.support.traces import write_lane_timeline
        profile = self.root / "profile"
        profile.mkdir()
        trace = profile / "trace.json"
        trace.write_text(json.dumps({"traceEvents": [
            {"ph": "M", "name": "thread_name", "pid": 7, "tid": 8, "args": {"name": "Worker #1"}},
            {"ph": "X", "name": "hash", "pid": 7, "tid": 8, "ts": 100, "dur": 50},
        ]}))
        output = self.root / "timeline.json"
        write_lane_timeline("gutch", [
            {"operation": "capture", "boundary": "process_elapsed", "start_seconds": 2,
             "elapsed_seconds": 1, "returncode": 0, "command": ["tool", "--profile-dir", str(profile)]},
            {"operation": "verify", "boundary": "process_elapsed", "start_seconds": 4,
             "elapsed_seconds": 0.5, "returncode": 1},
        ], {"capture": [str(trace)]}, output)
        events = json.loads(output.read_text())["traceEvents"]
        spans = {event["name"]: event for event in events if event["ph"] == "X"}
        self.assertEqual(spans["capture"]["ts"], 0)
        self.assertEqual(spans["capture"]["dur"], 1_000_000)
        self.assertEqual(spans["hash"]["ts"], 100)
        self.assertNotEqual(spans["hash"]["tid"], spans["capture"]["tid"])
        self.assertEqual(spans["verify"]["ts"], 1_000_000)
        self.assertEqual(spans["verify"]["dur"], 500_000)
        self.assertEqual(spans["verify"]["args"]["returncode"], 1)

    def test_compacted_fractional_durations_do_not_overlap_after_combining(self):
        from comparison_benchmark_suite.support.traces import write_lane_timeline, combine_labeled_traces
        lane = self.root / "timeline.json"
        measurements = [{"operation": str(index), "boundary": "process_elapsed",
                         "elapsed_seconds": duration} for index, duration in enumerate(
                             [0.3980697, 2.1202831, 5.7358942, 0.0000007])]
        write_lane_timeline("tool", measurements, {}, lane)
        output = self.root / "combined.json"
        combine_labeled_traces([("tool", lane)], output)
        spans = [e for e in json.loads(output.read_text())["traceEvents"] if e["ph"] == "X"]
        for left, right in zip(spans, spans[1:]):
            self.assertEqual(left["ts"] + left["dur"], right["ts"])
        for span, measurement in zip(spans, measurements):
            self.assertLessEqual(abs(span["dur"] - measurement["elapsed_seconds"] * 1e6), 0.5)

    def test_failed_candidate_retains_evidence_and_does_not_stop_copy(self):
        from comparison_benchmark_suite import run
        from unittest.mock import patch
        fixture = self.root / "fixture.yaml"
        fixture.write_text(yaml.safe_dump({
            "name": "failure", "builds": self.inputs(), "warmups": 0,
            "lane_wait_seconds": 0, "step_wait_seconds": 0,
            "executables": {"broken": sys.executable},
            "lanes": [{"label": "broken", "tool": "gutch"}, {"label": "copy", "tool": "filesystem"}],
        }))
        with patch.object(run, "ROOT", self.root):
            self.assertEqual(run.main(["--fixture", str(fixture)]), 1)
        output = next((self.root / ".artifacts/runs").iterdir())
        results = json.loads((output / "results.json").read_text())
        self.assertEqual([r["metadata"]["status"] for r in results], ["ERROR", "PASS"])
        self.assertEqual(json.loads((output / "run.json").read_text())["status"], "failed")
        self.assertTrue(list(output.glob("lanes/*/commands/*")))

    def test_cached_local_fixture_is_repaired_from_original(self):
        builds = self.inputs()
        fixture = self.root / "fixture.yaml"
        fixture.write_text("name: test")
        values = {"builds": builds}
        product, _ = prepare_dataset(values, fixture, self.root / ".artifacts")
        (product / "v1/file.txt").write_text("tampered")
        prepare_dataset(values, fixture, self.root / ".artifacts")
        self.assertEqual((product / "v1/file.txt").read_text(), "version 1")

    def test_warmup_failure_is_not_hidden_by_passing_measurement(self):
        from comparison_benchmark_suite.scheduling.runner import execute_cases
        from comparison_benchmark_suite.support.command import CommandRunner
        from comparison_benchmark_suite.tools.models import FixtureSpec, LaneResult
        fixture = FixtureSpec(
            name="warmup-failure", runner="gutch-fixture", description="test",
            delete_artifacts=True, open_perfetto=False,
            lanes=(LaneSpec("copy", "filesystem", warmup=True), LaneSpec("copy", "filesystem")),
            source_path=self.root / "fixture.yaml", lane_wait_seconds=0,
        )
        layout = RunLayout(self.root / "run")
        layout.root.mkdir()
        results = execute_cases(
            fixture, layout, CommandRunner(),
            lambda case: LaneResult(case.label, case.kind,
                                   metadata={"status": "ERROR" if case.warmup else "PASS"}),
            executable=Path("missing"),
        )
        self.assertEqual(results[0].metadata["status"], "PASS")
        record = json.loads((layout.root / "run.json").read_text())
        self.assertEqual(record["status"], "failed")
        self.assertEqual(record["failed_cases"], ["copy-warmup"])

    def test_archive_traversal_is_rejected(self):
        archive = self.root / "bad.zip"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("../outside", "bad")
        with self.assertRaises(ValueError):
            extract_archive(archive, self.root / "extract")
        self.assertFalse((self.root / "outside").exists())

    def test_cleanup_does_not_chmod_socket_reparse_points(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from comparison_benchmark_suite.support.retention import remove_owned
        import stat
        directory = self.root / "cache"
        directory.mkdir()
        socket_path = directory / "cached.sock"
        socket_path.write_bytes(b"socket stand-in")
        original_lstat, original_chmod = Path.lstat, Path.chmod
        def metadata(path, *args, **kwargs):
            if path == socket_path:
                return SimpleNamespace(st_mode=stat.S_IFSOCK, st_reparse_tag=1)
            return original_lstat(path, *args, **kwargs)
        def chmod(path, *args, **kwargs):
            self.assertNotEqual(path, socket_path)
            return original_chmod(path, *args, **kwargs)
        with patch.object(Path, "lstat", metadata), patch.object(Path, "chmod", chmod):
            remove_owned(directory, self.root)
        self.assertFalse(directory.exists())

    def test_cleanup_waits_for_only_the_owned_plakar_cache(self):
        from unittest.mock import patch
        from comparison_benchmark_suite.support import artifacts
        original = artifacts.remove_owned
        attempts = []
        def remove(path, owner):
            if path.name.startswith("gutch-p-"):
                attempts.append(path)
                if len(attempts) == 1:
                    error = OSError("cache still closing")
                    error.winerror = 32
                    raise error
                return
            original(path, owner)
        layout = RunLayout(self.root / "run")
        layout.lane("plakar")
        with patch.object(artifacts, "remove_owned", remove), patch.object(artifacts.time, "sleep") as sleep:
            layout.remove_payloads()
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0], attempts[1])
        sleep.assert_called_once_with(0.25)

    def test_utilization_weights_cpu_and_preserves_unavailable_values(self):
        from comparison_benchmark_suite.support.memory import process_utilization
        values = process_utilization([
            {"memory": {"sampled_cpu_seconds": 2, "cpu_observed_seconds": 1, "sampled_peak_rss_bytes": 100}},
            {"memory": {"sampled_cpu_seconds": 1, "cpu_observed_seconds": 3, "sampled_peak_rss_bytes": 200}},
            {"memory": {"sampled_cpu_seconds": None, "cpu_observed_seconds": None}},
        ])
        self.assertEqual(values["cpu_percent"], 75)
        self.assertEqual(values["peak_rss_bytes"], 200)
        self.assertEqual(process_utilization([{}]), {})

    def test_extras_do_not_hide_missing_or_corrupt_expected_files(self):
        from comparison_benchmark_suite.scheduling.dataset import DatasetSelection
        source = self.root / "product/v1"
        source.mkdir(parents=True)
        (source / "expected").write_bytes(b"correct")
        dataset = DatasetSelection.resolve(source.parent)
        output = self.root / "output"
        output.mkdir()
        (output / "extra").write_bytes(b"extra")
        evidence = self.root / "validation.json"
        with self.assertRaises(RuntimeError):
            dataset.validate(source, output, evidence)
        (output / "expected").write_bytes(b"corrupt")
        with self.assertRaises(RuntimeError):
            dataset.validate(source, output, evidence)
        shutil.copy2(source / "expected", output / "expected")
        dataset.validate(source, output, evidence)
        self.assertEqual(json.loads(evidence.read_text())["extra_files"], ["extra"])

    def test_borg_preflight_reuses_version_for_repeated_lanes(self):
        from comparison_benchmark_suite.tools.external import ExternalTools
        calls = []
        class Commands:
            def run(self, command, **options):
                calls.append(command)
                return CommandResult(tuple(map(str, command)), 0.1, 0, "borg 2.0.0b23", "")
        binary = self.root / "borg.exe"
        binary.write_bytes(b"test")
        tools = ExternalTools(self.root, Commands(), borg=binary)
        tools.check_borg_version()
        tools.check_borg_version()
        self.assertEqual(len(calls), 1)
        self.assertEqual(tools.borg_version, "borg 2.0.0b23")

    def test_borg_one_is_rejected_before_repository_creation(self):
        from comparison_benchmark_suite.tools.external import ExternalTools, run_external
        calls = []
        class Commands:
            def run(self, command, **options):
                calls.append(command)
                return CommandResult(tuple(map(str, command)), 0.1, 0, "borg 1.4.5", "")
        source = self.root / "product/v1"
        source.mkdir(parents=True)
        (source / "file").write_bytes(b"data")
        binary = self.root / "borg.exe"
        binary.write_bytes(b"test")
        with self.assertRaisesRegex(ValueError, "Borg 2 is required"):
            ExternalTools(self.root, Commands(), borg=binary)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][-1], "--version")

    def test_pairwise_fixtures_leave_external_performance_defaults_untouched(self):
        from comparison_benchmark_suite.tools.config import load_fixture
        for name, tool in [("kopia", "kopia"), ("restic", "restic"), ("borg", "borg"),
                           ("plakar", "plakar"), ("bpt", "buildpatchtool")]:
            path = ROOT / "fixtures" / f"gutch_vs_{name}.yaml"
            fixture = load_fixture(path)
            self.assertEqual([lane.tool for lane in fixture.lanes], ["gutch", tool])
            self.assertEqual(fixture.lanes[1].arguments, ())
            self.assertEqual(fixture.profile_mode, "off")
            self.assertEqual(fixture.repetitions, 3)

    def test_shared_dataset_reuses_cache_and_resolves_paths_from_definition(self):
        builds = self.inputs()
        definition = self.root / "shared.yaml"
        definition.write_text(yaml.safe_dump({"builds": builds}))
        values = {"dataset": "shared.yaml"}
        first, _ = prepare_dataset(values, self.root / "first.yaml", self.root / ".artifacts")
        second, _ = prepare_dataset(values, self.root / "second.yaml", self.root / ".artifacts")
        self.assertEqual(first, second)
        with self.assertRaisesRegex(ValueError, "either dataset or builds"):
            prepare_dataset({**values, "builds": builds}, self.root / "third.yaml", self.root / ".artifacts")

    def test_corruption_plan_preserves_permissions(self):
        from comparison_benchmark_suite.support.recovery import build_corruption_plan, apply_corruption_plan
        destination = self.root / "installation"
        destination.mkdir()
        target = destination / "a.bin"
        target.write_bytes(b"original")
        (destination / "b.bin").write_bytes(b"delete me")
        mode = target.stat().st_mode
        plan = build_corruption_plan(destination, self.root / "corruption.json", 1)
        operations = json.loads(plan.read_text())["operations"]
        self.assertEqual({item["kind"] for item in operations}, {"flipByte", "delete", "addFile"})
        apply_corruption_plan(destination, plan)
        self.assertEqual(target.stat().st_mode, mode)
        self.assertNotEqual(target.read_bytes(), b"original")
        self.assertFalse((destination / "b.bin").exists())

    def test_buildpatch_store_uploader_is_not_used_as_local_generator(self):
        class Commands:
            def run(self, command, **options):
                return CommandResult(tuple(map(str, command)), 0, 0, "UploadBinary ClientSecret OrganizationID", "")
        binary = self.root / "tool"
        binary.write_bytes(b"example")
        result = run_buildpatchtool(binary, Commands(), None, None, LaneSpec("bpt", "buildpatchtool"))
        self.assertEqual(result.metadata["status"], "UNSUPPORTED")

    def test_buildpatch_recovery_preserves_target_and_allows_extra_files(self):
        class Commands:
            def run(self, command, **options):
                assert not options.get("expected_failure", False)
                if "-help" in command:
                    output = "BuildRoot CloudDir ArtifactId FeatureLevel ChunkWindowSize BuildVersion AppLaunch AppArgs"
                elif "-mode=InstallManifest" in command:
                    value = lambda flag: next(x.split("=", 1)[1] for x in command if str(x).startswith(flag + "="))
                    source = Path(value("-Manifest")).read_text()
                    destination = Path(value("-OutputDir"))
                    if any(str(arg).startswith("-PrevManifest=") for arg in command):
                        assert list(destination.glob(".gutch-benchmark-extra-*"))
                        (destination / "file").chmod(0o600)
                    shutil.copytree(source, destination, dirs_exist_ok=True)
                    output = ""
                else:
                    assert "-ChunkWindowSize=1048576" in command
                    cloud = Path(next(x.split("=", 1)[1] for x in command if str(x).startswith("-CloudDir=")))
                    value = lambda flag: next(x.split("=", 1)[1] for x in command if str(x).startswith(flag + "="))
                    (cloud / value("-OutputFilename")).write_text(value("-BuildRoot"))
                    output = ""
                return CommandResult(tuple(map(str, command)), 0.1, 0, output, "")
        product = self.root / "product"
        for version in ("v1", "v2"):
            source = product / version
            source.mkdir(parents=True)
            (source / "file").write_bytes(b"content")
        binary = self.root / "tool"
        binary.write_bytes(b"example")
        result = run_buildpatchtool(binary, Commands(), RunLayout(self.root / "run").lane("bpt"),
                                   product, LaneSpec("bpt", "buildpatchtool", arguments=("-ChunkWindowSize=1048576",)),
                                   recovery_enabled=True)
        self.assertEqual(result.metadata["status"], "PASS")
        self.assertAlmostEqual(result.metrics["restore"], 0.2)
        self.assertAlmostEqual(result.metrics["repair"], 0.2)
        self.assertNotIn("full_restore_recovery", result.metrics)
        self.assertEqual(result.metadata["operations"]["in_place_repair"], "PASS")
        evidence = json.loads((self.root / "run/lanes/bpt/stats/validate-final-v1.json").read_text())
        self.assertEqual(evidence["extra_files"], [".gutch-benchmark-extra-002.bin"])

    def test_buildpatch_success_exit_without_restored_files_fails_validation(self):
        class Commands:
            def run(self, command, **options):
                output = "BuildRoot CloudDir ArtifactId FeatureLevel ChunkWindowSize BuildVersion AppLaunch AppArgs"
                if "-mode=ChunkBuildDirectory" in command and "-help" not in command:
                    value = lambda flag: next(x.split("=", 1)[1] for x in command if str(x).startswith(flag + "="))
                    (Path(value("-CloudDir")) / value("-OutputFilename")).write_text("manifest")
                return CommandResult(tuple(map(str, command)), 0.1, 0, output, "")

        product = self.root / "product"
        source = product / "v1"
        source.mkdir(parents=True)
        (source / "file").write_bytes(b"expected")
        binary = self.root / "tool"
        binary.write_bytes(b"example")
        with self.assertRaises((RuntimeError, FileNotFoundError, ValueError)):
            run_buildpatchtool(binary, Commands(), RunLayout(self.root / "run").lane("bpt"),
                               product, LaneSpec("bpt", "buildpatchtool"))


if __name__ == "__main__":
    unittest.main()
