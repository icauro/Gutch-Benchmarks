"""Resource scope and separation from performance samples."""
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from comparison_benchmark_suite.support.memory import DiskSpaceSampler, ProcessMemorySampler, process_utilization, summarize_operation_resources
from comparison_benchmark_suite.support.artifacts import RunLayout
from comparison_benchmark_suite.support.command import CommandRunner
from comparison_benchmark_suite.scheduling.runner import execute_cases
from comparison_benchmark_suite.tools.models import FixtureSpec, LaneResult, LaneSpec

ROOT = Path(__file__).resolve().parents[1]

class ResourceTests(unittest.TestCase):
    def setUp(self):
        owner = ROOT / ".artifacts/tests"
        owner.mkdir(parents=True, exist_ok=True)
        temp = tempfile.TemporaryDirectory(dir=owner)
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def test_disk_excludes_inputs_and_evidence_and_keeps_peak_after_removal(self):
        lane = self.root / "lane"
        payload = lane / "payload"
        payload.mkdir(parents=True)
        (payload / "repo.bin").write_bytes(b"x" * 200)
        (payload / "stats").mkdir()
        (payload / "stats/dataset-file").write_bytes(b"x" * 50)
        (lane / "cache").mkdir()
        (lane / "cache/index").write_bytes(b"x" * 100)
        for name in ("commands", "stats", "traces", "kopia-logs"):
            folder = lane / name
            folder.mkdir()
            (folder / "log").write_bytes(b"x" * 1000)
        (self.root / "input.bin").write_bytes(b"x" * 5000)
        sampler = DiskSpaceSampler([lane])
        sampler.sample()
        self.assertEqual(sampler.result["peak_disk_bytes"], 350)
        (payload / "repo.bin").unlink()
        sampler.sample()
        self.assertEqual(sampler.result["peak_disk_bytes"], 350)

    def test_memory_sums_parent_and_descendants_in_one_sample(self):
        parent = Mock()
        parent.memory_info.return_value = SimpleNamespace(rss=1000)
        child = Mock()
        child.memory_info.return_value = SimpleNamespace(rss=500)
        parent.children.return_value = [child]
        parent.cpu_times.return_value = SimpleNamespace(user=0, system=0)
        sampler = ProcessMemorySampler(42, None)
        sampler.started = time.perf_counter()
        sampler.stopped.set()
        with patch("comparison_benchmark_suite.support.memory.psutil.Process", return_value=parent):
            sampler._sample()
        self.assertEqual(sampler.result["sampled_peak_rss_bytes"], 1500)
        parent.children.assert_called_once_with(recursive=True)

    def test_failed_memory_sample_does_not_publish_a_partial_workflow_peak(self):
        measurements = [{"memory": {"sampled_peak_rss_bytes": 100}},
                        {"memory": {"error": "sampling denied", "sampled_peak_rss_bytes": 200}}]
        self.assertNotIn("peak_rss_bytes", process_utilization(measurements))

    def test_operation_peaks_do_not_include_later_recovery_or_workflow_disk_totals(self):
        folder = self.root / "gutch-resources/commands"
        folder.mkdir(parents=True)
        operations = [("gutch-resources capture v1", 10), ("gutch-resources capture v2", 20),
                      ("reconstruct gutch-resources v2", 30), ("reconstruct gutch-resources v1", 40),
                      ("gutch-resources repair v2", 50), ("gutch-resources repair v1", 60),
                      ("gutch-resources hidden_repair v2", 999), ("reconstruct v2", 999)]
        for index, (operation, peak) in enumerate(operations):
            (folder / f"{index:04d}.json").write_text(json.dumps({"operation": operation,
                "memory": {"sampled_peak_rss_bytes": peak}}))
        results = [{"label": "gutch-resources", "metrics": {"peak_disk_bytes": 99999},
                    "metadata": {"case": "gutch", "status": "PASS", "snapshots": ["v1", "v2"]}}]
        values = summarize_operation_resources(results, self.root)["gutch"]
        self.assertEqual([values[name]["peak_rss_bytes"] for name in
            ("initial_capture", "incremental_capture", "restore", "repair")], [10, 20, 40, 60])
        self.assertTrue(all("peak_disk_bytes" not in value for value in values.values()))

    def test_resource_temp_environment_is_owned_and_does_not_change_parent_environment(self):
        import os
        commands = CommandRunner()
        commands.temporary_directory = self.root / "owned-temp"
        original = dict(os.environ)
        with patch.object(commands, "_run_streamed", return_value=("", "", 0)) as launch:
            commands.run(["synthetic"], description="test")
        env = launch.call_args.kwargs["env"]
        for name in ("TMPDIR", "TMP", "TEMP"):
            self.assertEqual(env[name], str(commands.temporary_directory.resolve()))
        self.assertEqual(dict(os.environ), original)

    def test_resource_timings_are_excluded_from_speed_summary(self):
        layout = RunLayout(self.root / "run", retain_evidence=True)
        fixture = FixtureSpec("test", "local", "", True, False,
            (LaneSpec("gutch", "gutch"),), self.root / "fixture.yaml",
            lane_wait_seconds=0, repetitions=1, resource_sampling=True)
        commands = CommandRunner()
        seen = []
        def execute(case):
            seen.append((case.resource_sample, commands.memory_profile))
            payload = layout.lane(case.label).payload
            (payload / "data").write_bytes(b"x" * 123)
            return LaneResult(case.label, case.kind,
                metrics={"backup": 999 if case.resource_sample else 1,
                         **({"peak_rss_bytes": 456} if case.resource_sample else {})},
                metadata={"status": "PASS"})
        module = "comparison_benchmark_suite.scheduling.runner."
        with patch(module + "subprocess.run", return_value=SimpleNamespace(stdout="test")), patch(
            module + "platform.platform", return_value="test"), patch(module + "write_lane_timeline"), patch(
            module + "combine_labeled_traces"):
            execute_cases(fixture, layout, commands, execute, executable=self.root / "missing", discard_outputs=True)
        summary = json.loads((layout.root / "summary.json").read_text())["gutch"]
        self.assertEqual(summary["backup"]["median"], 1)
        self.assertEqual(summary["backup"]["samples"], 1)
        self.assertEqual(summary["peak_rss_bytes"]["median"], 456)
        self.assertEqual(summary["peak_disk_bytes"]["median"], 123)
        self.assertEqual(summary["peak_disk_bytes"]["source"], "separate_resource_pass")
        self.assertEqual(len(json.loads((layout.root / "results.json").read_text())), 1)
        self.assertEqual(len(json.loads((layout.root / "resources.json").read_text())), 1)
        self.assertEqual(seen, [(False, False), (True, True)])
