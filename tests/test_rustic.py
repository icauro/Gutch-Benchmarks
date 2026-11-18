"""Rustic command contracts and pairwise presets, without executing any tool."""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

import yaml

from comparison_benchmark_suite.benchmark import resolve_executable
from comparison_benchmark_suite.support.command import CommandError, CommandResult
from comparison_benchmark_suite.support.commands import GutchCli
from comparison_benchmark_suite.support.gutch import GutchOperations
from comparison_benchmark_suite.support.models import GutchProfile
from comparison_benchmark_suite.tools.config import load_fixture
from comparison_benchmark_suite.tools.external import ExternalTools, run_external
from comparison_benchmark_suite.tools.models import LaneSpec
from comparison_benchmark_suite.tools.report import pair_peer


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

    def test_plakar_recovery_wipes_each_build_and_restores_it_whole(self):
        binary, lane, dataset, commands = self.adapter_inputs()
        output = lane.payload / "installation"
        def recovery(dataset, lane, output_root, repair, restore, **options):
            self.assertTrue(options["delete_extra"])
            extra = output_root / "v2" / "extra.bin"
            extra.parent.mkdir(parents=True, exist_ok=True)
            extra.write_bytes(b"not in the snapshot")
            elapsed = repair("repair")
            self.assertFalse(extra.exists())
            self.assertTrue((output_root / "v2").is_dir())
            return {"repair": elapsed}, {"repair": "PASS"}
        with patch("comparison_benchmark_suite.tools.external.recovery_checks", side_effect=recovery), patch(
            "comparison_benchmark_suite.tools.external.validate_installation", return_value=0.0
        ):
            result = run_external(ExternalTools(commands, plakar=binary), lane, self.root / "product",
                                  LaneSpec("plakar", "plakar"), recovery_enabled=True, dataset=dataset)
        restores = [call.args[0] for call in commands.run.call_args_list if "restore" in call.args[0]]
        self.assertEqual(len(restores), 4)
        self.assertIn(output / "v2", restores[-2])
        self.assertEqual(result.metadata["recovery_mode"], "wipe_and_restore")
        self.assertEqual(result.metadata["extra_file_policy"], "wipe_and_restore")
        # Two timed restores plus the two timed wipes.
        self.assertGreaterEqual(result.metrics["repair"], 0.5)

    def test_restic_restores_without_rereading_output_the_suite_validates(self):
        binary, lane, dataset, commands = self.adapter_inputs()
        summary = '{"message_type": "summary", "snapshot_id": "abc"}'
        commands.run.return_value = CommandResult((), 0.25, 0, summary, "")
        with patch("comparison_benchmark_suite.tools.external.validate_installation", return_value=0.0):
            run_external(ExternalTools(commands, restic=binary), lane, self.root / "product",
                         LaneSpec("restic", "restic"), dataset=dataset)
        restores = [call.args[0] for call in commands.run.call_args_list if call.args[0][1] == "restore"]
        self.assertEqual(len(restores), 2)
        for command in restores:
            self.assertNotIn("--verify", command)

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
        expected = {"borg", "bpt", "kopia", "plakar", "restic", "rustic", "encrypted"}
        self.assertEqual({p.stem.removeprefix("gutch_vs_") for p in fixtures.glob("*.yaml")}, expected)
        shared = yaml.safe_load((fixtures / "blender/dataset.yaml").read_text(encoding="utf-8"))
        self.assertNotIn("lanes", shared)
        self.assertFalse((fixtures / "blender/fixture.yaml").exists())
        for other in expected:
            path = fixtures / f"gutch_vs_{other}.yaml"
            fixture = load_fixture(path)
            self.assertEqual([lane.tool for lane in fixture.lanes],
                             ["gutch", "gutch" if other == "encrypted" else pair_peer(other)])
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertEqual(document["dataset"], "blender/dataset.yaml")
            # Gutch encrypts exactly where the other tool cannot run unencrypted.
            self.assertEqual(fixture.lanes[0].profile.encrypted, other in {"kopia", "restic", "rustic"})
            if other == "encrypted":
                # Identical settings except encryption, so the ratio isolates its cost.
                plain, sealed = (lane.profile for lane in fixture.lanes)
                self.assertTrue(sealed.encrypted)
                self.assertEqual(replace(sealed, name=plain.name, encrypted=False), plain)
        rustic = load_fixture(fixtures / "gutch_vs_rustic.yaml")
        self.assertIn("--set-compression", rustic.lanes[1].arguments)
        self.assertIn("--set-datapack-size", rustic.lanes[1].arguments)
        # Rustic's bounds match the Gutch 1 MiB preset (256 KiB / 1 MiB / 4 MiB).
        arguments = rustic.lanes[1].arguments
        bounds = {flag: arguments[arguments.index(flag) + 1] for flag in
                  ("--set-chunk-min-size", "--set-chunk-size", "--set-chunk-max-size")}
        self.assertEqual(bounds, {"--set-chunk-min-size": "256kiB", "--set-chunk-size": "1MiB",
                                  "--set-chunk-max-size": "4MiB"})
        self.assertEqual(rustic.lanes[0].profile.chunk_profile, "chunk_1MiB")

    def test_local_rustic_discovery_on_both_platforms(self):
        for system, folder, name in (("Windows", "windows-x64", "rustic.exe"),
                                     ("Linux", "linux-x64", "rustic")):
            binary = self.root / "bin" / folder / "rustic" / name
            binary.parent.mkdir(parents=True)
            binary.touch()
            with patch("platform.system", return_value=system), patch("platform.machine", return_value="AMD64"), patch("shutil.which", return_value=None):
                self.assertEqual(resolve_executable("rustic", self.root / "fixture.yaml", self.root / "bin"), binary)

    def test_encrypted_gutch_profile_initializes_and_unlocks_with_the_test_password(self):
        commands = Mock()
        commands.run.return_value = SimpleNamespace(elapsed_seconds=1.0)
        operations = GutchOperations(GutchCli(Path("gutch-cli")), commands)
        repo = self.root / "repo"
        operations.init_repo(repo, GutchProfile("plain"), "gutch")
        operations.init_repo(repo, GutchProfile("sealed", encrypted=True), "gutch")
        plain, sealed = commands.run.call_args_list
        self.assertNotIn("--encrypt", plain.args[0])
        self.assertEqual(plain.kwargs["env"], {})
        self.assertIn("--encrypt", sealed.args[0])
        self.assertEqual(sealed.kwargs["env"], {"GUTCH_REPO_PASSWORD": "bench"})


if __name__ == "__main__":
    unittest.main()
