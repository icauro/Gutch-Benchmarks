"""Terminal navigation and real subprocess lifecycle checks; no browser launches."""

import asyncio
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import psutil
import yaml
from textual.widgets import DataTable, Static

ROOT = Path(__file__).resolve().parents[1]
from comparison_benchmark_suite.interactive import BenchmarkApp


class InteractiveTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        owner = ROOT / ".artifacts/tests"
        owner.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=owner)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.suite = self.root / "comparison_benchmark_suite"
        self.suite.mkdir()
        fixture_patch = patch("comparison_benchmark_suite.interactive.FIXTURES", self.suite / "fixtures")
        fixture_patch.start()
        self.addCleanup(fixture_patch.stop)
        (self.suite / "fixtures").mkdir()
        builds = []
        for version in (1, 2):
            source = self.root / f"v{version}"
            source.mkdir()
            (source / "file").write_text(str(version))
            builds.append({"path": str(source)})
        for name, tool, description in [("a_copy", "filesystem", "First fixture description"),
                                        ("b_error", "gutch", "Second fixture description")]:
            (self.suite / "fixtures" / f"{name}.yaml").write_text(yaml.safe_dump({
                "name": name, "description": description, "builds": builds,
                "warmups": 0, "repetitions": 1, "lane_wait_seconds": 0, "step_wait_seconds": 0,
                "lanes": [{"label": tool, "tool": tool}], "executables": {"gutch": sys.executable},
            }))

    async def wait_for_preview(self, app, pilot, index):
        # Focus posts a Preview message to the app. One idle barrier need not
        # drain messages posted by other queued messages, especially on fast CI.
        async def wait():
            while (app.selected != index or app.fixtures[index].name not in
                   str(app.query_one("#description", Static).content)):
                await pilot.pause()
        await asyncio.wait_for(wait(), timeout=3)

    async def test_hover_run_summary_perfetto_and_run_another(self):
        app = BenchmarkApp(self.suite)
        opened = []
        with patch("comparison_benchmark_suite.interactive.open_trace_in_perfetto",
                   side_effect=lambda path, log: opened.append(path) or True):
            async with app.run_test(size=(80, 24)) as pilot:
                await pilot.press("down")
                await self.wait_for_preview(app, pilot, 1)
                self.assertEqual(app.selected, 1)
                await pilot.hover("#fixture-1")
                await pilot.pause()
                self.assertIn("Second fixture", str(app.query_one("#description", Static).content))
                # Keep mouse hover from overriding the keyboard selection under test.
                self.assertTrue(await pilot.hover("#description"))
                app.query_one("#fixture-0").focus()
                await self.wait_for_preview(app, pilot, 0)
                self.assertEqual(app.selected, 0)
                await pilot.click("#run")
                await pilot.pause()
                await asyncio.wait_for(app.workers.wait_for_complete(), 30)
                await pilot.pause()  # Let the results view finish layout before clicking it.
                self.assertFalse(app.busy)
                self.assertIn("Run completed.", str(app.query_one("#outcome", Static).content))
                self.assertEqual(app.query_one("#table", DataTable).row_count, 1)
                self.assertTrue(app.report_path.is_file())
                self.assertEqual(app.query_one("#progress").progress, 1)
                self.assertTrue(await pilot.click("#perfetto"))
                await pilot.pause()
                await asyncio.wait_for(app.workers.wait_for_complete(), 10)
                self.assertEqual(opened, [app.run_root / "trace.json"])
                await pilot.click("#another")
                await pilot.pause()
                self.assertTrue(app.query_one("#picker").display)
                app.query_one("#fixture-1").focus()
                await self.wait_for_preview(app, pilot, 1)
                await pilot.click("#run")
                await pilot.pause()
                await asyncio.wait_for(app.workers.wait_for_complete(), 30)
                await pilot.pause()  # Let the results view finish layout before clicking it.
                self.assertIn("failed", str(app.query_one("#outcome", Static).content))
                self.assertEqual(app.query_one("#table", DataTable).row_count, 1)

    async def test_stop_terminates_only_owned_process_tree(self):
        marker = self.suite / "child.pid"
        (self.suite / "simulate_stop.py").write_text(
            "import subprocess, sys, time\n"
            "from pathlib import Path\n"
            "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
            "Path('child.pid').write_text(str(child.pid))\n"
            "run = Path('.artifacts/runs/stopped'); run.mkdir(parents=True)\n"
            "(run / 'run.json').write_text('{\"status\": \"running\"}')\n"
            "print('Running stop. Results: ' + str(run.resolve()), flush=True)\n"
            "print('Step: waiting', flush=True)\n"
            "time.sleep(60)\n"
        )
        create_process = asyncio.create_subprocess_exec

        async def simulate(*args, **kwargs):
            return await create_process(sys.executable, str(self.suite / "simulate_stop.py"), **kwargs)

        launcher = patch("comparison_benchmark_suite.interactive.asyncio.create_subprocess_exec", side_effect=simulate)
        launcher.start()
        self.addCleanup(launcher.stop)
        app = BenchmarkApp(self.suite)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.click("#run")
            await pilot.pause()
            async def child_started():
                while not marker.exists():
                    await asyncio.sleep(0.02)
            await asyncio.wait_for(child_started(), 10)
            child = psutil.Process(int(marker.read_text()))
            await pilot.click("#stop")
            await pilot.pause()
            await asyncio.wait_for(app.workers.wait_for_complete(), 10)
            self.assertFalse(app.busy)
            self.assertFalse(child.is_running())
            self.assertIn("Stopped", str(app.query_one("#outcome", Static).content))
            self.assertEqual(json.loads((app.run_root / "run.json").read_text())["status"], "cancelled")
            await pilot.click("#another")
            await pilot.pause()
            self.assertTrue(app.query_one("#picker").display)


if __name__ == "__main__":
    unittest.main()
