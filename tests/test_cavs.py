"""CAVS command contracts, server lifetime and pair preset, without executing CAVS."""

from contextlib import contextmanager
from pathlib import Path
import sys
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

from comparison_benchmark_suite.support.command import CommandResult
from comparison_benchmark_suite.tools import cavs
from comparison_benchmark_suite.tools.config import load_fixture
from comparison_benchmark_suite.tools.models import LaneSpec


ROOT = Path(__file__).resolve().parents[1]
# A venv `python.exe` on Windows is a launcher with a child interpreter, so a
# terminated launcher would leave the fake server running; use the real one.
PYTHON = getattr(sys, "_base_executable", sys.executable)
FAKE_SERVER = """
import socket, sys, time
host, port = sys.argv[sys.argv.index("--listen") + 1].rsplit(":", 1)
listener = socket.socket()
listener.bind((host, int(port)))
listener.listen()
time.sleep(60)
"""


class CavsTests(unittest.TestCase):
    def setUp(self):
        owner = ROOT / ".artifacts" / "tests"
        owner.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=owner)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def adapter_inputs(self):
        tools = self.root / "tools"
        tools.mkdir()
        for name in ("cavs", "cavs-client", "cavs-server"):
            (tools / name).write_bytes(name.encode())
        lane = SimpleNamespace(root=self.root, payload=self.root / "payload", stats=self.root / "stats")
        lane.stats.mkdir()
        sources = tuple(self.root / "product" / name for name in ("5.0.0", "5.1.0"))
        dataset = Mock(sources=sources)
        dataset.snapshot_metrics.return_value = {source.name: {} for source in sources}
        dataset.metadata.return_value = {}

        def run(command, **options):
            # `cavs pack-dir` writes the container that `store add` ingests.
            if command[1] == "pack-dir":
                Path(command[4]).write_bytes(b"container")
            if command[1] == "store" and command[3] == "add":
                Path(command[2]).mkdir(parents=True, exist_ok=True)
                (Path(command[2]) / f"{command[4]}.cavspack").write_bytes(b"x" * 10)
            return CommandResult((), 0.25, 0, "", "")

        commands = Mock()
        commands.run.side_effect = run
        return tools / "cavs", lane, dataset, commands

    @contextmanager
    def fake_origin(self, *arguments):
        yield "http://127.0.0.1:9"

    def test_capture_installs_and_recovery_follow_the_cavs_contract(self):
        binary, lane, dataset, commands = self.adapter_inputs()
        tools = binary.parent

        def recovery(dataset, lane, output, repair, restore, **options):
            self.assertFalse(options["delete_extra"])
            return {"repair": repair("repair")}, {"repair": "PASS", "exact_recovery": "UNSUPPORTED: generic"}

        with patch.object(cavs, "serve_store", self.fake_origin), patch.object(
            cavs, "recovery_checks", side_effect=recovery
        ), patch.object(cavs, "validate_installation", return_value=0.0):
            result = cavs.run_cavs(binary, commands, lane, self.root / "product",
                                   LaneSpec("cavs", "cavs", arguments=("--profile", "fastcdc-256k")),
                                   dataset=dataset, recovery_enabled=True)
        calls = [call.args[0] for call in commands.run.call_args_list]
        self.assertEqual(len(calls), 9)  # two packs, two adds, two restores, two repairs, verify
        store = lane.payload / "store"
        packages = lane.payload / "packages"
        for index, source in enumerate(dataset.sources):
            asset = f"v{index + 1:04d}"
            self.assertEqual(calls[2 * index], [tools / "cavs", "pack-dir", source, "-o",
                                                packages / f"{asset}.cavs", "--profile", "fastcdc-256k"])
            self.assertEqual(calls[2 * index + 1], [tools / "cavs", "store", store, "add", asset,
                                                    packages / f"{asset}.cavs", "--storage", "packfiles"])
        output = lane.payload / "installation"
        for offset in (4, 6):
            for index, (source, asset) in enumerate(zip(reversed(dataset.sources), ("v0002", "v0001"))):
                self.assertEqual(calls[offset + index], [
                    tools / "cavs-client", "fetch", "http://127.0.0.1:9", asset, "-o", output / source.name,
                    "--cache", lane.payload / "client-cache", "--no-resume", "--prune", "--connections", "4"])
        self.assertEqual(calls[-1], [tools / "cavs", "store", store, "verify"])
        for call in commands.run.call_args_list:
            self.assertEqual(call.kwargs["env"], {"RAYON_NUM_THREADS": "4"})
        # Containers are intermediates; only the deduplicated store is measured.
        self.assertFalse(packages.exists())
        self.assertEqual(result.metrics["repo_size"], 20)
        self.assertEqual(result.metrics["backup"], 1.0)
        self.assertEqual(result.metrics["initial_capture"], 0.5)
        self.assertEqual(result.metrics["restore"], 0.5)
        self.assertEqual(result.metrics["repair"], 0.5)
        self.assertEqual(result.metrics["repository_check"], 0.25)
        self.assertEqual(result.metadata["operations"]["exact_recovery"], cavs.EXTRA_FILE_REASON)
        self.assertEqual(set(result.metadata["binary_sha256"]), {"cavs", "cavs-client", "cavs-server"})

    def test_missing_companion_binary_is_reported_before_any_command(self):
        binary, lane, dataset, commands = self.adapter_inputs()
        (binary.parent / "cavs-server").unlink()
        with self.assertRaisesRegex(FileNotFoundError, "cavs-server"):
            cavs.run_cavs(binary, commands, lane, self.root / "product", LaneSpec("cavs", "cavs"), dataset=dataset)
        commands.run.assert_not_called()

    def test_server_listens_before_use_and_stops_afterwards(self):
        script = self.root / "server.py"
        script.write_text(FAKE_SERVER, encoding="utf-8")
        launched = []
        real_popen = cavs.subprocess.Popen

        def popen(command, **options):
            process = real_popen([PYTHON, "-I", str(script), *command[1:]], **options)
            launched.append(process)
            return process

        with patch.object(cavs.subprocess, "Popen", side_effect=popen):
            with cavs.serve_store(Path("cavs-server"), self.root / "store", self.root,
                                  self.root / "server.log", None) as origin:
                self.assertRegex(origin, r"^http://127\.0\.0\.1:\d+$")
                self.assertIsNone(launched[0].poll())
        self.assertIsNotNone(launched[0].poll())

    def test_server_that_exits_early_fails_with_its_log(self):
        script = self.root / "exit.py"
        script.write_text("raise SystemExit(3)\n", encoding="utf-8")
        real_popen = cavs.subprocess.Popen
        with patch.object(cavs.subprocess, "Popen",
                          side_effect=lambda command, **options: real_popen([PYTHON, "-I", str(script)], **options)):
            with self.assertRaisesRegex(RuntimeError, "exited with 3"):
                with cavs.serve_store(Path("cavs-server"), self.root / "store", self.root,
                                      self.root / "server.log", None):
                    self.fail("an exited server must not be used")

    def test_pair_matches_gutch_chunk_bounds_and_compression(self):
        fixture = load_fixture(ROOT / "src/comparison_benchmark_suite/fixtures/gutch_vs_cavs.yaml")
        gutch, peer = fixture.lanes
        # CAVS fastcdc-256k is 64 KiB / 256 KiB / 1 MiB, the same bounds as Gutch's 256 KiB preset.
        self.assertEqual(gutch.profile.chunk_profile, "chunk_256KiB")
        self.assertEqual(peer.tool, "cavs")
        self.assertEqual(peer.arguments, ("--profile", "fastcdc-256k", "--zstd-level", "3"))
        self.assertEqual(fixture.repetitions, 6)
        self.assertTrue(fixture.corrupt_repair)


if __name__ == "__main__":
    unittest.main()
