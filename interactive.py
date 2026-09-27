"""Interactive terminal front end for the standalone comparison runner."""

import asyncio
import json
import os
from pathlib import Path
import re
import sys
import time

import psutil
import yaml
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import Button, DataTable, Footer, Header, ProgressBar, RichLog, Static

from .tools.config import load_fixture
from .tools.report import COMPARISON_HEADERS, comparison_rows
from .support.traces import open_trace_in_perfetto


class FixtureButton(Button):
    class Preview(Message):
        def __init__(self, index: int):
            super().__init__()
            self.index = index

    def __init__(self, label: str, index: int):
        super().__init__(label, id=f"fixture-{index}")
        self.index = index

    def on_enter(self):
        self.post_message(self.Preview(self.index))

    def on_focus(self):
        self.post_message(self.Preview(self.index))


class BenchmarkApp(App):
    TITLE = "Comparison benchmark suite"
    BINDINGS = [("q", "quit", "Quit"), ("ctrl+c", "stop_or_quit", "Stop / quit"),
                ("up", "previous_fixture", "Previous fixture"), ("down", "next_fixture", "Next fixture")]
    CSS = """
    Screen { background: $surface; }
    #picker { height: 1fr; }
    #fixtures { width: 34; padding: 1; border: round $primary; }
    FixtureButton { width: 100%; margin-bottom: 1; }
    FixtureButton:hover, FixtureButton:focus { background: $primary; color: $text; }
    #description-box { width: 1fr; border: round $primary; padding: 1 2; }
    #description { height: auto; }
    #controls, #result-actions { height: auto; padding: 1; }
    #controls Button, #result-actions Button { margin-right: 1; }
    #running { height: 1fr; padding: 1; }
    #status { height: auto; margin-bottom: 1; }
    #progress { width: 100%; margin-bottom: 1; }
    #log { height: 1fr; border: round $primary; }
    #results { height: 1fr; padding: 1; }
    #outcome, #report-path, #notes { height: auto; margin-bottom: 1; }
    #table { height: 1fr; min-height: 4; }
    #notes { height: 3; }
    #report-path { height: 2; }
    #errors { height: auto; max-height: 6; }
    """

    def __init__(self, root: Path):
        super().__init__()
        self.root = root.resolve()
        self.fixtures = []
        self.fixture_errors = []
        for path in sorted((self.root / "fixtures").rglob("*.yaml")):
            try:
                values = yaml.safe_load(path.read_text(encoding="utf-8"))
                if isinstance(values, dict) and "lanes" in values:
                    self.fixtures.append(load_fixture(path))
            except (OSError, ValueError, yaml.YAMLError) as error:
                self.fixture_errors.append(f"{path.name}: {error}")
        self.selected = 0
        self.busy = False
        self.stopping = False
        self.process = None
        self.report_path = None
        self.run_root = None
        self.started = 0.0
        self.step = "Preparing inputs"

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="picker"):
            with VerticalScroll(id="fixtures"):
                for index, fixture in enumerate(self.fixtures):
                    yield FixtureButton(fixture.name, index)
            with VerticalScroll(id="description-box"):
                yield Static("Hover or focus a fixture to preview its description.", id="description", markup=False)
        with Horizontal(id="controls"):
            yield Button("Run fixture", id="run", variant="primary", disabled=not self.fixtures)
            yield Button("Quit", id="quit")
        with Vertical(id="running"):
            yield Static("", id="status", markup=False)
            yield ProgressBar(total=None, show_eta=False, id="progress")
            yield RichLog(id="log", markup=False, highlight=False, max_lines=2000)
            yield Button("Stop run", id="stop", variant="error")
        with Vertical(id="results"):
            yield Static("", id="outcome", markup=False)
            yield DataTable(id="table")
            yield Static("Times are median seconds. Repair is in-place; recovery is full restore. CPU 100% = one core; child processes excluded. '-' means unavailable.", id="notes", markup=False)
            with VerticalScroll(id="errors"):
                yield Static("", id="reasons", markup=False)
            yield Static("", id="report-path", markup=False)
            with Horizontal(id="result-actions"):
                yield Button("Run another", id="another", variant="primary")
                yield Button("Open Perfetto", id="perfetto", disabled=True)
                yield Button("Show run log", id="show-log")
                yield Button("Quit", id="quit-results")
        yield Footer()

    def on_mount(self):
        self.query_one("#running").display = False
        self.query_one("#results").display = False
        self.query_one("#table", DataTable).add_columns(*COMPARISON_HEADERS)
        if self.fixtures:
            self.preview(0)
        else:
            self.query_one("#description", Static).update("No runnable fixtures found. Add a fixture YAML under fixtures/.")
        for error in self.fixture_errors:
            self.notify(error, severity="error", timeout=15)
        self.set_interval(1, self.update_elapsed)

    def preview(self, index):
        self.selected = index
        fixture = self.fixtures[index]
        self.query_one("#description", Static).update(
            f"{fixture.name}\n\n{fixture.description}\n\n{fixture.source_path}\n\nClick Run fixture to start."
        )

    def on_fixture_button_preview(self, message: FixtureButton.Preview):
        if not self.busy:
            self.preview(message.index)

    def on_button_pressed(self, event: Button.Pressed):
        identifier = event.button.id
        if identifier == "run":
            self.start_run()
        elif identifier == "another":
            self.show_picker()
        elif identifier == "perfetto":
            self.query_one("#perfetto", Button).disabled = True
            self.open_perfetto(self.run_root / "trace.json")
        elif identifier == "stop":
            self.request_stop()
        elif identifier == "show-log":
            self.query_one("#running").display = not self.query_one("#running").display
            self.query_one("#stop").display = False
        elif identifier in {"quit", "quit-results"}:
            self.action_quit()

    def action_previous_fixture(self):
        self.move_fixture(-1)

    def action_next_fixture(self):
        self.move_fixture(1)

    def move_fixture(self, offset):
        if self.fixtures and self.query_one("#picker").display:
            self.selected = (self.selected + offset) % len(self.fixtures)
            self.query_one(f"#fixture-{self.selected}").focus()

    def show_picker(self):
        if self.busy:
            return
        self.query_one("#picker").display = True
        self.query_one("#controls").display = True
        self.query_one("#running").display = False
        self.query_one("#results").display = False
        if self.fixtures:
            self.query_one(f"#fixture-{self.selected}").focus()

    def start_run(self):
        if self.busy or not self.fixtures:
            return
        self.busy, self.stopping = True, False
        self.report_path = self.run_root = None
        self.started = time.monotonic()
        self.step = "Preparing and validating inputs"
        self.query_one("#picker").display = False
        self.query_one("#controls").display = False
        self.query_one("#results").display = False
        self.query_one("#running").display = True
        self.query_one("#stop").display = True
        self.query_one("#stop", Button).disabled = False
        self.query_one("#log", RichLog).clear()
        self.query_one("#progress", ProgressBar).update(total=None, progress=0)
        self.update_elapsed()
        self.execute_fixture(self.fixtures[self.selected].source_path)

    def update_elapsed(self):
        if self.busy:
            elapsed = int(time.monotonic() - self.started)
            self.query_one("#status", Static).update(f"{self.step}  |  Elapsed {elapsed // 60:02d}:{elapsed % 60:02d}")

    def accept_line(self, line):
        self.query_one("#log", RichLog).write(line)
        if line.startswith("Step: "):
            self.step = line.removeprefix("Step: ")
        if line.startswith("Running ") and ". Results: " in line:
            self.run_root = Path(line.split(". Results: ", 1)[1])
        match = re.match(r"Progress: (\d+)/(\d+) measured cases", line)
        if match:
            self.query_one("#progress", ProgressBar).update(progress=int(match[1]), total=int(match[2]))
        if line.startswith("Report: "):
            self.report_path = Path(line.removeprefix("Report: "))
        self.update_elapsed()

    @work(exclusive=True, group="benchmark")
    async def execute_fixture(self, fixture):
        exit_code = 1
        try:
            env = dict(os.environ, PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
            self.process = await asyncio.create_subprocess_exec(
                sys.executable, str(self.root / "run.py"), "--fixture", str(fixture),
                "--no-open-perfetto", cwd=self.root, env=env,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
            )
            if self.stopping:
                await self.stop_process()
            while line := await self.process.stdout.readline():
                self.accept_line(line.decode("utf-8", errors="replace").rstrip())
            exit_code = await self.process.wait()
        except (OSError, ValueError) as error:
            self.accept_line(f"Could not run fixture: {error}")
        finally:
            if self.process is not None and self.process.returncode is None:
                await self.stop_process()
            self.process = None
            self.busy = False
        if self.stopping and self.run_root and self.run_root.resolve().is_relative_to(self.root / ".artifacts/runs"):
            manifest = self.run_root / "run.json"
            try:
                record = json.loads(manifest.read_text(encoding="utf-8"))
                record.update(status="cancelled", error="Stopped from interactive runner", cleanup_complete=False)
                manifest.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            except (OSError, ValueError) as error:
                self.accept_line(f"Could not update stopped-run status: {error}")
        self.show_results(exit_code)

    def show_results(self, exit_code):
        self.query_one("#running").display = False
        self.query_one("#results").display = True
        outcome = "Stopped; partial evidence retained." if self.stopping else (
            "Run completed." if exit_code == 0 else "Run failed; inspect the log and retained evidence.")
        self.query_one("#outcome", Static).update(outcome)
        table = self.query_one("#table", DataTable)
        table.clear()
        reasons = []
        if self.run_root:
            try:
                summary = json.loads((self.run_root / "summary.json").read_text(encoding="utf-8"))
                results = json.loads((self.run_root / "results.json").read_text(encoding="utf-8"))
                table.add_rows(comparison_rows(summary, results))
                reasons = list(dict.fromkeys(r["metadata"]["reason"] for r in results if r["metadata"].get("reason")))
            except (OSError, ValueError, KeyError) as error:
                reasons.append(f"Summary unavailable: {error}")
        self.query_one("#reasons", Static).update("\n".join(reasons))
        path_widget = self.query_one("#report-path", Static)
        path_widget.update(str(self.report_path or self.run_root or "No report generated."))
        path_widget.tooltip = str(self.report_path or self.run_root or "No report generated.")
        self.query_one("#perfetto", Button).disabled = not (self.run_root and (self.run_root / "trace.json").is_file())
        self.query_one("#another").focus()

    @work(thread=True, group="perfetto", exclusive=True)
    def open_perfetto(self, trace):
        opened = open_trace_in_perfetto(trace, lambda line: self.call_from_thread(self.notify, line))
        self.call_from_thread(self.notify, "Trace sent to Perfetto." if opened else "Could not open trace; see notification.")
        self.call_from_thread(self.finish_perfetto)

    def finish_perfetto(self):
        self.query_one("#perfetto", Button).disabled = not (self.run_root and (self.run_root / "trace.json").is_file())

    def request_stop(self):
        if self.busy and not self.stopping:
            self.stopping = True
            self.step = "Stopping owned benchmark processes"
            self.query_one("#stop", Button).disabled = True
            self.run_worker(self.stop_process(), group="stop")

    async def stop_process(self):
        process = self.process
        if process is None or process.returncode is not None:
            return
        # Only the subprocess launched by this app and its descendants are stopped.
        try:
            parent = psutil.Process(process.pid)
            for child in reversed(parent.children(recursive=True)):
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            parent.kill()
        except psutil.NoSuchProcess:
            pass
        await process.wait()

    def action_stop_or_quit(self):
        if self.busy:
            self.request_stop()
        else:
            self.action_quit()

    def action_quit(self):
        if self.busy:
            self.notify("Stop the running benchmark before quitting.", severity="warning")
        else:
            self.exit()
