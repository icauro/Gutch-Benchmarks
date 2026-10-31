"""CI preparation, report publication and disposal with tools/processes blocked."""

import bz2
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import zipfile

import yaml

from comparison_benchmark_suite.datasets import prepare_dataset
from comparison_benchmark_suite.scheduling.runner import execute_cases
from comparison_benchmark_suite.support.artifacts import RunLayout
from comparison_benchmark_suite.tools.models import FixtureSpec, LaneResult, LaneSpec


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ci_benchmarks", ROOT / ".github/scripts/benchmarks.py")
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)


class CiTests(unittest.TestCase):
    def setUp(self):
        owner = ROOT / ".artifacts/tests"
        owner.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=owner)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.package = self.root / ci.SOURCE
        blocked = patch("subprocess.Popen", side_effect=AssertionError("tools must not run"))
        blocked.start()
        self.addCleanup(blocked.stop)
        # platform.platform() may invoke uname on Linux; it is not a tool run.
        platform_probe = patch("platform.platform", return_value="mock-platform")
        platform_probe.start()
        self.addCleanup(platform_probe.stop)
        summary = patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": ""})
        summary.start()
        self.addCleanup(summary.stop)

    def test_every_pair_and_relocated_checkout_reuse_downloaded_inputs(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("blender/file.txt", "immutable Blender stand-in")
        archive_bytes = buffer.getvalue()
        asset = {"url": "https://example.test/blender.zip", "sha256": hashlib.sha256(archive_bytes).hexdigest()}
        shared = self.root / "fixtures/blender/dataset.yaml"
        shared.parent.mkdir(parents=True)
        shared.write_text(yaml.safe_dump({"builds": [{"version": version, "downloads": {"linux-x64": asset}}
                                                   for version in ("1.0", "2.0")]}))
        artifacts = self.root / ".artifacts"
        with patch("comparison_benchmark_suite.datasets.platform.system", return_value="Linux"), patch(
            "comparison_benchmark_suite.datasets.platform.machine", return_value="x86_64"
        ), patch("comparison_benchmark_suite.datasets.urlopen", side_effect=lambda *a, **k: io.BytesIO(archive_bytes)) as download:
            products = [prepare_dataset({"dataset": "blender/dataset.yaml"},
                        self.root / f"fixtures/gutch_vs_{pair}.yaml", artifacts)[0] for pair in ci.PAIRS]
            self.assertEqual(len(set(products)), 1)
            self.assertEqual(download.call_count, 1)  # Same archive bytes used by both versions.
            relocated = self.root / "elsewhere"
            relocated.mkdir()
            copy = relocated / "dataset.yaml"
            shutil.copyfile(shared, copy)
            other = prepare_dataset(yaml.safe_load(copy.read_text()), copy, artifacts)[0]
            self.assertEqual(other, products[0])
            self.assertEqual(download.call_count, 1)
            # A modified cached input is rebuilt from the verified archive.
            (other / "v1/file.txt").write_text("corrupt")
            prepare_dataset(yaml.safe_load(copy.read_text()), copy, artifacts)
            self.assertEqual((other / "v1/file.txt").read_text(), "immutable Blender stand-in")

    def test_tool_install_verifies_archive_and_executable_without_launching(self):
        binary = b"synthetic executable"
        archive = bz2.compress(binary)
        (self.package / "resources").mkdir(parents=True)
        manifest = {"executables": [{"platform": "linux-x64", "tool": "restic",
                    "path": "linux-x64/restic/restic", "source_url": "https://example.test/restic.bz2",
                    "archive_sha256": hashlib.sha256(archive).hexdigest(), "sha256": hashlib.sha256(binary).hexdigest()}]}
        (self.package / "resources/tools.json").write_text(json.dumps(manifest))
        with patch.object(ci, "urlopen", return_value=io.BytesIO(b"bad checksum")):
            with self.assertRaisesRegex(ValueError, "Archive checksum"):
                ci.install_tool("restic", self.root)
        target = self.root / ".artifacts/tools/linux-x64/restic/restic"
        self.assertFalse(target.exists())
        with patch.object(ci, "urlopen", return_value=io.BytesIO(archive)) as download:
            ci.install_tool("restic", self.root)
            ci.install_tool("restic", self.root)
            self.assertEqual(download.call_count, 1)
        self.assertEqual(target.read_bytes(), binary)

    def test_discard_cleans_failed_samples_before_next_case_and_keeps_evidence(self):
        layout = RunLayout(self.root / "runs/test", retain_evidence=True)
        fixture = FixtureSpec("test", "local", "mocked", True, False,
                              (LaneSpec("gutch", "gutch"),), self.root / "fixture.yaml",
                              repetitions=2, lane_wait_seconds=0)
        commands = Mock(measurements=[])
        calls = []

        def execute(case):
            if calls:
                self.assertFalse(calls[-1].exists())
            lane = layout.lane(case.label)
            payload = lane.payload / "discard.bin"
            payload.write_bytes(b"mocked output")
            calls.append(payload)
            (lane.stats / "validation.json").write_text("{}")
            return LaneResult(case.label, case.kind, {"backup": 1}, metadata={"status": "ERROR"})

        module = "comparison_benchmark_suite.scheduling.runner."
        with patch(module + "subprocess.run", return_value=SimpleNamespace(stdout="mock-sha")), patch(
            module + "process_utilization", return_value={}
        ), patch(module + "write_lane_timeline"), patch(module + "combine_labeled_traces"):
            execute_cases(fixture, layout, commands, execute, executable=self.root / "unused",
                          discard_outputs=True)
        self.assertEqual(len(calls), 2)
        self.assertFalse(any(path.exists() for path in calls))
        self.assertEqual(json.loads((layout.root / "run.json").read_text())["status"], "failed")
        self.assertEqual(len(list(layout.root.glob("lanes/*/stats/validation.json"))), 2)

    def test_discard_also_cleans_a_case_that_raises_before_returning_results(self):
        layout = RunLayout(self.root / "runs/interrupted", retain_evidence=True)
        fixture = FixtureSpec("test", "local", "mocked", True, False,
                              (LaneSpec("gutch", "gutch"),), self.root / "fixture.yaml")

        def execute(case):
            (layout.lane(case.label).payload / "partial.bin").write_bytes(b"partial output")
            raise RuntimeError("interrupted mock")

        with patch("comparison_benchmark_suite.scheduling.runner.subprocess.run",
                   return_value=SimpleNamespace(stdout="mock-sha")), self.assertRaisesRegex(RuntimeError, "interrupted mock"):
            execute_cases(fixture, layout, Mock(measurements=[]), execute,
                          executable=self.root / "unused", discard_outputs=True)
        self.assertFalse((layout.root / "lanes/gutch/payload").exists())
        self.assertEqual(json.loads((layout.root / "run.json").read_text())["status"], "failed")

    def test_bpt_install_preserves_engine_support_files(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("Engine/Binaries/Linux/BuildPatchTool", b"mock bpt")
            archive.writestr("Engine/Binaries/Linux/support.so", b"mock support")
            archive.writestr("Engine/Config/settings.ini", b"mock settings")
        data = buffer.getvalue()
        (self.package / "resources").mkdir(parents=True)
        record = {"platform": "linux-x64", "tool": "buildpatchtool",
                  "path": "linux-x64/buildpatchtool/Engine/Binaries/Linux/BuildPatchTool",
                  "source_url": "https://example.test/bpt.zip", "sha256": hashlib.sha256(b"mock bpt").hexdigest(),
                  "archive_sha256": hashlib.sha256(data).hexdigest()}
        (self.package / "resources/tools.json").write_text(json.dumps({"executables": [record]}))
        with patch.object(ci, "urlopen", return_value=io.BytesIO(data)):
            ci.install_tool("bpt", self.root)
        engine = self.root / ".artifacts/tools/linux-x64/buildpatchtool/Engine"
        self.assertEqual((engine / "Config/settings.ini").read_bytes(), b"mock settings")
        self.assertEqual((engine / "Binaries/Linux/support.so").read_bytes(), b"mock support")

    def test_bpt_data_capture_does_not_mark_a_payload_file_as_launch_executable(self):
        from comparison_benchmark_suite.scheduling.dataset import DatasetSelection
        from comparison_benchmark_suite.support.command import CommandResult
        from comparison_benchmark_suite.tools.buildpatchtool import run_buildpatchtool

        product = self.root / "product"
        for name in ("v1", "v2"):
            source = product / name
            source.mkdir(parents=True)
            (source / "blender.exe").write_bytes(b"Windows executable used only as data")
        dataset = DatasetSelection.resolve(product)
        executable = self.root / "mock-bpt"
        executable.touch()
        lane = RunLayout(self.root / "run").lane("bpt")
        calls = []

        def command(args, **kwargs):
            calls.append(args)
            if "-help" in args:
                help_text = "BuildRoot CloudDir ArtifactId FeatureLevel ChunkWindowSize BuildVersion AppLaunch AppArgs"
                return CommandResult((), 0, 0, help_text, "")
            options = dict(str(arg).split("=", 1) for arg in args[1:] if "=" in str(arg))
            if options["-mode"] == "ChunkBuildDirectory":
                self.assertEqual(options["-AppLaunch"], "")
                (Path(options["-CloudDir"]) / options["-OutputFilename"]).touch()
            else:
                version = Path(options["-Manifest"]).stem
                shutil.copytree(product / version, options["-OutputDir"])
            return CommandResult((), 0.1, 0, "", "")

        result = run_buildpatchtool(executable, SimpleNamespace(run=command), lane, product,
                                   LaneSpec("bpt", "buildpatchtool"), dataset=dataset)
        self.assertEqual(result.metadata["status"], "PASS")
        self.assertEqual(len(calls), 5)
        self.assertEqual(dataset.inventories, DatasetSelection.resolve(product).inventories)

    def test_collection_excludes_payload_and_publication_marks_missing_pair(self):
        run = self.root / ".artifacts/runs/test"
        run.mkdir(parents=True)
        (self.package / "resources").mkdir(parents=True)
        (self.package / "resources/tools.json").write_text('{"executables": []}')
        row = {"metadata": {"case": "gutch", "status": "PASS"}}
        for name, value in {"run.json": {"status": "passed", "fixture": {"description": "Test settings"}},
                            "results.json": [row], "summary.json": {"gutch": {"backup": {"median": 1.25}}}}.items():
            (run / name).write_text(json.dumps(value))
        for relative in ("lanes/gutch/payload/repo/private.bin", "lanes/gutch/commands/command.log"):
            path = run / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("evidence")
        compact = ci.collect("restic", "success", self.root)
        self.assertEqual(compact["status"], "PASS")
        export = self.root / ".artifacts/export/restic"
        self.assertFalse(any(path.name == "private.bin" for path in export.rglob("*")))
        self.assertTrue((export / "lanes/gutch/commands/command.log").exists())
        self.assertFalse(run.exists())
        incoming = self.root / "incoming/benchmark-restic/restic"
        incoming.mkdir(parents=True)
        shutil.copyfile(export / "compact.json", incoming / "compact.json")
        (self.root / "README.md").write_text(f"Original intro\n![Latest per-pair benchmark comparisons](reports/comparison.svg)\n![Peak resources by operation](reports/resources.svg)\n{ci.START}\nold\n{ci.END}\nOriginal footer")
        ci.publish("all", self.root / "incoming", "123", "2", self.root)
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("Original intro", readme)
        self.assertIn("Original footer", readme)
        self.assertIn("1.250", readme)
        self.assertIn("<summary>Detailed results and source reports</summary>", readme)
        self.assertNotIn("Suite commit:", readme)
        self.assertIn("### Gutch vs Borg (ERROR)", readme)
        self.assertIn("![Latest per-pair benchmark comparisons]", readme)
        charts = list((self.root / "reports").rglob("comparison.svg"))
        self.assertEqual(len(charts), 2)
        self.assertEqual(charts[0].read_bytes(), charts[1].read_bytes())
        resources = list((self.root / "reports").rglob("resources.svg"))
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0].read_bytes(), resources[1].read_bytes())
        self.assertLess(readme.index("reports/comparison.svg"), readme.index("reports/resources.svg"))
        self.assertLess(readme.index("reports/resources.svg"), readme.index(ci.START))
        self.assertLess(readme.index("![Latest per-pair"), readme.index(ci.START))
        ci.publish("restic", self.root / "incoming", "124", "1", self.root)
        updated = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertEqual(updated.count("![Latest per-pair"), 1)
        self.assertIn("/123-2/borg.json", updated)
        self.assertIn("/124-1/restic.json", updated)
        self.assertIn("### Gutch vs Borg (ERROR)", updated)
        self.assertEqual((self.root / "reports/comparison.svg").read_bytes(),
                         next((self.root / "reports").glob("*/124-1/comparison.svg")).read_bytes())
        self.assertEqual(len(list((self.root / "reports").rglob("*.json"))), 7)
        self.assertFalse(list((self.root / "reports").rglob("command.log")))
        with self.assertRaises(ValueError):
            ci.publish("all", self.root / "incoming", "../escape", "1", self.root)

    def test_single_downloaded_artifact_without_artifact_name_directory_publishes(self):
        incoming = self.root / "incoming/rustic"
        incoming.mkdir(parents=True)
        record = {"pair": "rustic", "status": "PASS", "rows": [
            [label, "PASS", *("1.000" for _ in range(8))] for label in ("gutch", "rustic")],
            "summary": {label: {metric: {"median": value, "minimum": value, "maximum": value, "samples": 1}
                        for metric in ("peak_rss_bytes", "peak_disk_bytes")}
                        for label, value in (("gutch", 2097152), ("rustic", 4194304))}}
        record["operation_resources"] = {label: {"initial_capture": {"peak_rss_bytes": value}}
            for label, value in (("gutch", 2097152), ("rustic", 4194304))}
        (incoming / "compact.json").write_text(json.dumps(record))
        (self.root / "README.md").write_text(f"{ci.START}\nold\n{ci.END}")
        ci.publish("rustic", self.root / "incoming", "123", "1", self.root)
        report = next((self.root / "reports").glob("*/123-1/rustic.json"))
        self.assertEqual(json.loads(report.read_text())["status"], "PASS")
        self.assertNotIn(b"\r", report.read_bytes())
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("First capture RAM | First capture disk | Second capture RAM | Second capture disk", readme)
        self.assertIn("gutch | 2.0 | —", readme)
        self.assertIn("rustic | 4.0 | —", readme)

    def test_workflow_is_manual_only_and_pairs_share_one_cache_action(self):
        workflow = yaml.load((ROOT / ".github/workflows/benchmarks.yml").read_text(), Loader=yaml.BaseLoader)
        self.assertEqual(set(workflow["on"]), {"workflow_dispatch"})
        self.assertEqual(workflow["on"]["workflow_dispatch"]["inputs"]["pair"]["default"], "all")
        jobs = workflow["jobs"]
        self.assertEqual(jobs["compare"]["strategy"]["fail-fast"], "false")
        for job in ("inputs", "compare"):
            self.assertTrue(any(step.get("uses") == "./.github/actions/blender-inputs" for step in jobs[job]["steps"]))
        self.assertEqual(workflow["permissions"]["contents"], "read")
        self.assertEqual(jobs["publish"]["permissions"]["contents"], "write")
        composite = (ROOT / ".github/actions/blender-inputs/action.yml").read_text()
        self.assertNotIn("matrix.pair", composite)

    def test_pair_ratios_use_raw_medians_and_show_direction(self):
        record = {"pair": "restic", "status": "PASS", "rows": [
            [label, "PASS", "0.000", "0.000", "0.000", "-", "0.000", "-", "-"]
            for label in ("gutch", "restic")], "summary": {}}
        for label, values in (("gutch", (0.00041, 10, 7, 100)), ("restic", (0.00082, 5, 7, 400))):
            record["summary"][label] = {metric: {"median": value, "samples": 3}
                for metric, value in zip(("backup", "restore", "repair", "repo_size"), values)}
        table = "\n".join(ci.pair_overview(record))
        self.assertIn("### Gutch vs Restic (PASS)", table)
        self.assertIn("| **Gutch relative** | - | 2.00x faster | 2.00x slower | ~same | 75% smaller |", table)
        record["summary"]["restic"]["backup"]["samples"] = 2
        self.assertIn("| **Gutch relative** | - | - | 2.00x slower", "\n".join(ci.pair_overview(record)))
        record["status"] = "ERROR"
        self.assertIn("| **Gutch relative** | - | - | - | - | - |", "\n".join(ci.pair_overview(record)))

    def test_pair_ratios_omit_missing_zero_nonfinite_and_failed_measurements(self):
        for value in (None, 0, -1, float("nan"), float("inf")):
            with self.subTest(value=value):
                record = {"pair": "rustic", "status": "PASS", "rows": [
                    [label, "PASS", *("-" for _ in range(7))] for label in ("gutch", "rustic")],
                    "summary": {"gutch": {"backup": {"median": value}},
                                "rustic": {"backup": {"median": 2}}}}
                self.assertIn("| **Gutch relative** | - | - | - | - | - |", "\n".join(ci.pair_overview(record)))
        record["summary"]["gutch"]["backup"]["median"] = 1
        record["rows"][1][1] = "UNAVAILABLE"
        self.assertNotIn("faster", "\n".join(ci.pair_overview(record)))

    def test_new_report_keeps_ranges_common_validation_and_unsupported_outcomes(self):
        record = {"pair": "borg", "status": "PASS", "rows": [], "measurement_contract": 2,
                  "summary": {"gutch": {"repair_validated": {"median": 2, "minimum": 1, "maximum": 3, "samples": 6}},
                              "borg": {}},
                  "operations": {"borg": {"hidden_repair": "UNSUPPORTED: metadata-only resume"}}}
        rendered = "\n".join(ci.pair_overview(record))
        self.assertIn("2.000 (1.000–3.000; n=6)", rendered)
        self.assertIn("Content repair + validation s", rendered)
        self.assertIn("UNSUPPORTED: metadata-only resume", rendered)

    def test_ci_fixture_keeps_pair_settings_and_records_selected_repetitions(self):
        shutil.copytree(ROOT / ci.SOURCE / "fixtures", self.package / "fixtures",
                        ignore=shutil.ignore_patterns("builds", "__pycache__"))
        ci.write_fixture("rustic", 5, self.root)
        fixture = yaml.safe_load((self.root / ".artifacts/ci/fixture.yaml").read_text())
        self.assertEqual(fixture["repetitions"], 5)
        self.assertIn("5 rotating measured repetitions", fixture["description"])
        self.assertEqual([lane["tool"] for lane in fixture["lanes"]], ["gutch", "rustic"])
        self.assertEqual(Path(fixture["dataset"]), self.package / "fixtures/blender/dataset.yaml")


if __name__ == "__main__":
    unittest.main()
