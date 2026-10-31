"""Recovery outcomes, canonical damage and strict validation without native tools."""
import json
import os
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest

from comparison_benchmark_suite.scheduling.dataset import DatasetSelection
from comparison_benchmark_suite.support.recovery import build_corruption_plan, apply_corruption_plan, recovery_checks

ROOT = Path(__file__).resolve().parents[1]

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        owner = ROOT / ".artifacts/tests"
        owner.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=owner)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.product = self.root / "builds"
        source = self.product / "v1"
        source.mkdir(parents=True)
        for name, count in (("small", 10), ("medium", 100), ("large", 1000)):
            (source / name).write_bytes(b"x" * count)
        self.dataset = DatasetSelection.resolve(self.product)
        self.output = self.root / "output"
        self.lane = SimpleNamespace(stats=self.root / "stats")
        self.restore()

    def restore(self):
        shutil.copytree(self.product, self.output, dirs_exist_ok=True)
        return 1.0

    def repair(self, operation):
        shutil.rmtree(self.output)
        return self.restore()

    def test_canonical_plan_and_hidden_damage_preserve_size_and_mtime(self):
        source = self.product / "v1"
        destination = self.output / "v1"
        plan = build_corruption_plan(destination, self.root / "plan.json", 1,
            expected_inventory=self.dataset.inventories["v1"], preserve_mtime=True, add_extra=False)
        operations = json.loads(plan.read_text())["operations"]
        self.assertEqual({item["path"] for item in operations if item["kind"] == "flipByte"}, {"small", "large"})
        times = {name: (destination / name).stat().st_mtime_ns for name in ("small", "large")}
        apply_corruption_plan(destination, plan)
        for name in times:
            self.assertEqual((destination / name).stat().st_mtime_ns, times[name])
            self.assertEqual((destination / name).stat().st_size, (source / name).stat().st_size)
            self.assertNotEqual((destination / name).read_bytes(), (source / name).read_bytes())
        self.assertFalse((destination / "medium").exists())

    def test_recovery_cases_validate_each_outcome_and_include_validation_time(self):
        metrics, operations = recovery_checks(self.dataset, self.lane, self.output,
            self.repair, self.restore, delete_extra=True)
        self.assertEqual(set(operations.values()), {"PASS"})
        for name in ("repair", "hidden_repair", "exact_recovery", "full_restore_recovery"):
            self.assertEqual(metrics[name], 1.0)
            self.assertGreaterEqual(metrics[name + "_validated"], metrics[name])
        self.assertTrue((self.lane.stats / "validate-exact_recovery-v1.json").is_file())
        self.assertEqual(len(list(self.lane.stats.glob("corruption-*.json"))), 2)

    def test_unsupported_cases_have_no_fake_zero_timing(self):
        metrics, operations = recovery_checks(self.dataset, self.lane, self.output,
            self.repair, self.restore, delete_extra=False, hidden_damage=False)
        for name in ("hidden_repair", "exact_recovery"):
            self.assertTrue(operations[name].startswith("UNSUPPORTED"))
            self.assertNotIn(name, metrics)
        self.assertEqual(operations["repair"], "PASS")

    def test_successful_command_with_wrong_bytes_fails_validation(self):
        with self.assertRaisesRegex(RuntimeError, "output validation failed"):
            recovery_checks(self.dataset, self.lane, self.output,
                lambda operation: 0.01, self.restore, delete_extra=False)
