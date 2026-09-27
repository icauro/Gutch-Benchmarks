"""Core end-to-end execution, failure isolation, and filesystem validation."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from comparison_benchmark_suite.datasets import extract_archive

class SuiteTests(unittest.TestCase):
    def setUp(self):
        owner = ROOT / ".artifacts" / "tests"
        owner.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=owner)
        self.root = Path(self.temporary.name).resolve()
        assert self.root.is_relative_to(owner.resolve())
        self.addCleanup(self.temporary.cleanup)

    def test_platform_tools_and_explicit_paths(self):
        from comparison_benchmark_suite.benchmark import resolve_executable
        tools = self.root / "tools"
        fixture = self.root / "fixture.yaml"
        for system, platform_folder, relative in [
            ("Windows", "windows-x64", "restic/restic.exe"),
            ("Linux", "linux-x64", "restic/restic"),
        ]:
            binary = tools / platform_folder / relative
            binary.parent.mkdir(parents=True)
            binary.touch()
            with patch("platform.system", return_value=system), patch("platform.machine", return_value="AMD64"), patch("shutil.which", return_value=None):
                self.assertEqual(resolve_executable("restic", fixture, tools), binary)
                self.assertIsNone(resolve_executable("./missing", fixture, tools))
                self.assertEqual(resolve_executable(str(binary), fixture, tools), binary)
                target = "Win64/BuildPatchTool.exe" if system == "Windows" else "Linux/BuildPatchTool"
                bpt = tools / platform_folder / "buildpatchtool/Engine/Binaries" / target
                bpt.parent.mkdir(parents=True)
                bpt.touch()
                self.assertEqual(resolve_executable("BuildPatchTool", fixture, tools), bpt)

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
        standalone = self.root / "exported-suite"
        shutil.copytree(ROOT, standalone, ignore=shutil.ignore_patterns(".artifacts", "__pycache__", ".venv"))
        builds = self.inputs()
        fixture = standalone / "fixtures" / "custom" / "fixture.yaml"
        fixture.parent.mkdir()
        fixture.write_text(yaml.safe_dump({
            "name": "custom", "description": "Fixture settings and limitations.", "builds": builds, "warmups": 1, "repetitions": 2,
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
        self.assertIn("Fixture settings and limitations.", result.stdout)
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
        self.assertIn("Fixture settings and limitations.", (run / "summary.md").read_text())
        events = json.loads((run / "trace.json").read_text())["traceEvents"]
        spans = [event for event in events if event["ph"] == "X"]
        self.assertEqual(len(spans), 12)  # Capture, restore, recovery x two builds x two measured runs.
        self.assertTrue(all(event["dur"] > 0 for event in spans))
        self.assertFalse(any("warmup" in event.get("args", {}).get("name", "") for event in events))
        for index, build in enumerate(builds, 1):
            self.assertEqual((Path(build["path"]) / "file.txt").read_text(), f"version {index}")

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

    def test_archive_traversal_is_rejected(self):
        archive = self.root / "bad.zip"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("../outside", "bad")
        with self.assertRaises(ValueError):
            extract_archive(archive, self.root / "extract")
        self.assertFalse((self.root / "outside").exists())

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

if __name__ == "__main__":
    unittest.main()
