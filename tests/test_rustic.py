"""Rustic command contracts and pairwise presets, without executing any tool."""

from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

import yaml

from comparison_benchmark_suite.benchmark import resolve_executable
from comparison_benchmark_suite.support.command import CommandError, CommandResult
from comparison_benchmark_suite.tools.config import load_fixture
from comparison_benchmark_suite.tools.external import ExternalTools, run_external
from comparison_benchmark_suite.tools.models import LaneSpec


ROOT = Path(__file__).resolve().parents[1]


class RusticTests(unittest.TestCase):
    def setUp(self):
        owner = ROOT / ".artifacts" / "tests"
        owner.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=owner)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        # Every test must remain safe even if a command mock is removed by mistake.
        blocked = patch("subprocess.Popen", side_effect=AssertionError("tools must not run"))
        blocked.start()
        self.addCleanup(blocked.stop)

    def adapter_inputs(self):
        binary = self.root / "rustic"
        binary.write_bytes(b"mock executable")
        lane = SimpleNamespace(root=self.root, payload=self.root / "payload", stats=self.root / "stats")
        sources = tuple(self.root / "product" / name for name in ("v1", "v2"))
        dataset = Mock(sources=sources)
        dataset.snapshot_metrics.return_value = {source.name: {"repo_growth_bytes": 0} for source in sources}
        commands = Mock()
        commands.run.return_value = CommandResult((), 0.25, 0, "", "")
        return binary, lane, dataset, commands

    def test_commands_isolate_state_select_versions_and_scope_recovery(self):
        binary, lane, dataset, commands = self.adapter_inputs()
        def recovery(dataset, lane, output, repair, restore, **options):
            self.assertTrue(options["delete_extra"])
            return {"repair": repair("repair")}, {"repair": "PASS"}
        with patch("comparison_benchmark_suite.tools.external.recovery_checks", side_effect=recovery), patch(
            "comparison_benchmark_suite.tools.external.validate_installation", return_value=0.0
        ):
            result = run_external(
                ExternalTools(commands, rustic=binary), lane, self.root / "product",
                LaneSpec("rustic", "rustic", arguments=("--set-compression", "3")),
                recovery_enabled=True, dataset=dataset,
            )
        calls = commands.run.call_args_list
        self.assertEqual(len(calls), 8)  # init, two backups, four restores, check
        profile = self.root / "rustic-profile.toml"
        self.assertEqual(profile.read_text(encoding="utf-8"), "")
        prefix = [binary, "--use-profile", profile, "--repository", lane.payload / "repo",
                  "--cache-dir", self.root / "rustic-cache", "--no-progress", "--log-level", "warn"]
        self.assertEqual(calls[0].args[0], [*prefix, "init", "--set-compression", "3"])
        for call in calls:
            self.assertEqual(call.kwargs["env"], {"RUSTIC_PASSWORD": "bench", "RAYON_NUM_THREADS": "4"})
        for index, source in enumerate(dataset.sources, start=1):
            self.assertEqual(calls[index].args[0], [*prefix, "backup", "--as-path", source.name,
                             "--tag", f"gutch-benchmark-{index:04d}", source.name])
            self.assertEqual(calls[index].kwargs["cwd"], self.root / "product")
        output = lane.payload / "installation"
        for recovery, offset in ((False, 3), (True, 5)):
            for index, source in enumerate(reversed(dataset.sources)):
                tag = "gutch-benchmark-0002" if source.name == "v2" else "gutch-benchmark-0001"
                self.assertEqual(calls[offset + index].args[0], [*prefix, "restore",
                                 f"latest:{source.name}", output / source.name, "--filter-tags", tag,
                                 "--verify-existing", "--no-ownership", *(["--delete"] if recovery else [])])
        self.assertEqual(calls[-1].args[0], [*prefix, "check", "--read-data"])
        self.assertEqual(result.metadata["status"], "PASS")
        self.assertEqual(result.metrics["backup"], 0.5)
        self.assertEqual(result.metrics["restore"], 0.5)
        self.assertEqual(result.metrics["repair"], 0.5)
        self.assertEqual(result.metrics["repository_check"], 0.25)

    def test_backup_failure_stops_before_restore_and_validation(self):
        binary, lane, dataset, commands = self.adapter_inputs()
        failure = CommandError(CommandResult(("rustic", "backup"), 0.25, 1, "", "failed"), "backup")
        commands.run.side_effect = [CommandResult((), 0.25, 0, "", ""), failure]
        with self.assertRaises(CommandError):
            run_external(ExternalTools(commands, rustic=binary), lane, self.root / "product",
                         LaneSpec("rustic", "rustic"), dataset=dataset)
        self.assertEqual(commands.run.call_count, 2)
        dataset.validate.assert_not_called()

    def test_shipped_catalog_has_only_gutch_versus_one_tool(self):
        fixtures = ROOT / "src/comparison_benchmark_suite/fixtures"
        expected = {"borg", "bpt", "kopia", "plakar", "restic", "rustic"}
        self.assertEqual({p.stem.removeprefix("gutch_vs_") for p in fixtures.glob("*.yaml")}, expected)
        shared = yaml.safe_load((fixtures / "blender/dataset.yaml").read_text(encoding="utf-8"))
        self.assertNotIn("lanes", shared)
        self.assertFalse((fixtures / "blender/fixture.yaml").exists())
        for other in expected:
            path = fixtures / f"gutch_vs_{other}.yaml"
            fixture = load_fixture(path)
            self.assertEqual([lane.tool for lane in fixture.lanes],
                             ["gutch", "buildpatchtool" if other == "bpt" else other])
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertEqual(document["dataset"], "blender/dataset.yaml")
        rustic = load_fixture(fixtures / "gutch_vs_rustic.yaml")
        self.assertIn("--set-compression", rustic.lanes[1].arguments)
        self.assertIn("--set-datapack-size", rustic.lanes[1].arguments)

    def test_local_rustic_discovery_on_both_platforms(self):
        for system, folder, name in (("Windows", "windows-x64", "rustic.exe"),
                                     ("Linux", "linux-x64", "rustic")):
            binary = self.root / "bin" / folder / "rustic" / name
            binary.parent.mkdir(parents=True)
            binary.touch()
            with patch("platform.system", return_value=system), patch("platform.machine", return_value="AMD64"), patch("shutil.which", return_value=None):
                self.assertEqual(resolve_executable("rustic", self.root / "fixture.yaml", self.root / "bin"), binary)


if __name__ == "__main__":
    unittest.main()
