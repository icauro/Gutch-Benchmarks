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

    def test_buildpatch_store_uploader_is_not_used_as_local_generator(self):
        class Commands:
            def run(self, command, **options):
                return CommandResult(tuple(map(str, command)), 0, 0, "UploadBinary ClientSecret OrganizationID", "")
        binary = self.root / "tool"
        binary.write_bytes(b"example")
        result = run_buildpatchtool(binary, Commands(), None, None, LaneSpec("bpt", "buildpatchtool"))
        self.assertEqual(result.metadata["status"], "UNSUPPORTED")

    def test_buildpatch_local_capture_does_not_claim_restore_validation(self):
        class Commands:
            def run(self, command, **options):
                assert not options.get("expected_failure", False)
                assert "-mode=ChunkBuildDirectory" in command
                if "-help" in command:
                    output = "BuildRoot CloudDir ArtifactId FeatureLevel ChunkWindowSize BuildVersion AppLaunch AppArgs"
                else:
                    assert "-ChunkWindowSize=1048576" in command
                    cloud = Path(next(x.split("=", 1)[1] for x in command if str(x).startswith("-CloudDir=")))
                    (cloud / "data").write_bytes(b"generated")
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
                                   product, LaneSpec("bpt", "buildpatchtool", arguments=("-ChunkWindowSize=1048576",)))
        self.assertEqual(result.metadata["status"], "CAPTURE_ONLY")
        self.assertNotIn("restore", result.metrics)


if __name__ == "__main__":
    unittest.main()
