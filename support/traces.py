"""Perfetto trace composition without workflow-specific knowledge."""

from collections import Counter
import hashlib
import http.server
import json
import re
from pathlib import Path
import socketserver
import time
from functools import partial
from typing import Callable, Iterable
import urllib.parse
import webbrowser


PERFETTO_ORIGIN = "https://ui.perfetto.dev"
PERFETTO_PORT = 9001
PERFETTO_REQUEST_TIMEOUT_SECONDS = 30


class _TraceServer(socketserver.TCPServer):
    allow_reuse_address = True


class _TraceHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", PERFETTO_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        requested_path = urllib.parse.urlsplit(self.path).path
        if requested_path != f"/{self.server.trace_name}":
            self.send_error(404, "File not found")
            return
        self.server.trace_requested = True
        super().do_GET()

    def log_message(self, format: str, *args: object) -> None:
        del format, args


def combine_traces(inputs: Iterable[Path], output: Path) -> None:
    events: list[dict] = []
    pid_offset = 0
    tid_offset = 0
    timestamp_offset = 0.0
    for source in inputs:
        if not source.exists():
            continue
        document = json.loads(source.read_text(encoding="utf-8"))
        local_events = document.get("traceEvents", [])
        if not local_events:
            continue
        pids = [event.get("pid", 0) for event in local_events if isinstance(event.get("pid", 0), int)]
        tids = [event.get("tid", 0) for event in local_events if isinstance(event.get("tid", 0), int)]
        minimum_ts = min((event.get("ts", 0.0) for event in local_events), default=0.0)
        for event in local_events:
            copied = dict(event)
            if isinstance(copied.get("pid"), int):
                copied["pid"] += pid_offset
            if isinstance(copied.get("tid"), int):
                copied["tid"] += tid_offset
            if isinstance(copied.get("ts"), (int, float)):
                copied["ts"] = copied["ts"] - minimum_ts + timestamp_offset
            events.append(copied)
        pid_offset += max(pids, default=0) + 1
        tid_offset += max(tids, default=0) + 1
        timestamp_offset = max((event.get("ts", 0.0) + event.get("dur", 0.0) for event in events), default=0.0) + 1.0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps({"traceEvents": events, "displayTimeUnit": "ms"}, indent=2) + "\n",
        encoding="utf-8",
    )


def combine_labeled_traces(inputs: Iterable[tuple[str, Path]], output: Path,
                           *, source_offsets: dict[Path, float] | None = None) -> None:
    """Combine phase traces while keeping every benchmark lane in one process."""
    events: list[dict] = []
    lane_process_ids: dict[str, int] = {}
    lane_thread_ids: dict[str, dict[object, int]] = {}
    lane_offsets: dict[str, int] = {}
    named_tracks: set[tuple[int, int]] = set()

    for label, source in inputs:
        if not source.is_file():
            continue
        document = json.loads(source.read_text(encoding="utf-8"))
        local_events = [
            event
            for event in document.get("traceEvents", [])
            if isinstance(event, dict)
        ]
        if not local_events:
            continue
        if label not in lane_process_ids:
            lane_process_ids[label] = len(lane_process_ids) + 1
            lane_thread_ids[label] = {}
            lane_offsets[label] = 0
            events.append(
                {
                    "name": "process_name",
                    "cat": "__metadata",
                    "ph": "M",
                    "ts": 0,
                    "pid": lane_process_ids[label],
                    "tid": 1,
                    "args": {"name": label},
                }
            )

        process_id = lane_process_ids[label]
        thread_ids = lane_thread_ids[label]
        offset = source_offsets.get(source, lane_offsets[label]) if source_offsets else lane_offsets[label]
        source_duration = 0
        # Inputs are deliberately concatenated, so unique role names can reuse
        # a row across commands. Ambiguous/unnamed threads stay source-local.
        names = {
            (event.get("pid", 0), event.get("tid", 0)): event.get("args", {}).get("name")
            for event in local_events
            if event.get("ph") == "M" and event.get("name") == "thread_name"
        }
        # Pool numbers describe reusable display rows, not OS thread identity.
        neutral_names = {
            thread: re.sub(r"^(Capture|Reconstruction|Verification) worker #", "Worker #", name)
            if isinstance(name, str) else name
            for thread, name in names.items()
        }
        reusable_names = set()
        for candidate in set(neutral_names.values()):
            members = [thread for thread, name in neutral_names.items() if name == candidate]
            intervals = []
            for thread in members:
                spans = [event for event in local_events
                         if (event.get("pid", 0), event.get("tid", 0)) == thread
                         and event.get("ph") == "X"]
                if spans:
                    intervals.append((min(event["ts"] for event in spans),
                                      max(event["ts"] + event.get("dur", 0) for event in spans)))
            intervals.sort()
            distinct_roles = len({names[thread] for thread in members}) == len(members)
            if distinct_roles and len(intervals) == len(members) and all(
                left[1] <= right[0] for left, right in zip(intervals, intervals[1:])
            ):
                reusable_names.add(candidate)
        names = {
            thread: neutral_names[thread] if neutral_names[thread] in reusable_names else name
            for thread, name in names.items()
        }
        name_counts = Counter(names.values())
        for source_event in local_events:
            if source_event.get("cat") == "__metadata" and source_event.get("name") == "process_name":
                continue
            event = dict(source_event)
            original_thread = (event.get("pid", 0), event.get("tid", 0))
            name = names.get(original_thread)
            source_thread_id = ("name", name) if name and (name_counts[name] == 1 or name in reusable_names) else (str(source), original_thread)
            if source_thread_id not in thread_ids:
                thread_ids[source_thread_id] = len(thread_ids) + 1
            event["pid"] = process_id
            event["tid"] = thread_ids[source_thread_id]
            if event.get("ph") == "M" and event.get("name") == "thread_name":
                track = (process_id, event["tid"])
                if track in named_tracks:
                    continue
                named_tracks.add(track)
                event["args"] = {**event.get("args", {}), "name": name}
            source_timestamp = event.get("ts", 0)
            if isinstance(source_timestamp, (int, float)):
                source_duration = max(source_duration, int(source_timestamp + event.get("dur", 0)))
                event["ts"] = int(source_timestamp) + offset
            events.append(event)
        lane_offsets[label] = offset + source_duration + 1

    events.sort(key=lambda event: (event.get("ts", 0), event.get("pid", 0)))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps({"traceEvents": events, "displayTimeUnit": "ms"}, indent=2) + "\n",
        encoding="utf-8",
    )


def open_trace_in_perfetto(trace_path: Path, log: Callable[[str], None]) -> bool:
    trace_path = trace_path.resolve()
    if not trace_path.is_file():
        log(f"Perfetto trace does not exist: {trace_path}")
        return False

    try:
        document = json.loads(trace_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        log(f"Cannot read Perfetto trace {trace_path}: {error}")
        return False
    events = document.get("traceEvents", []) if isinstance(document, dict) else document
    if not isinstance(events, list) or not any(
        isinstance(event, dict) and event.get("ph") not in (None, "M") for event in events
    ):
        log(f"Perfetto trace has no recorded events; browser not opened: {trace_path}")
        return False

    handler = partial(_TraceHandler, directory=str(trace_path.parent))
    try:
        with _TraceServer(("127.0.0.1", PERFETTO_PORT), handler) as server:
            server.trace_name = trace_path.name
            server.trace_requested = False
            # A changed trace must not reuse a browser tab/import for an older file
            # served under the same localhost path.
            with trace_path.open("rb") as trace_file:
                revision = hashlib.file_digest(trace_file, "sha256").hexdigest()[:12]
            local_url = f"http://127.0.0.1:{PERFETTO_PORT}/{urllib.parse.quote(trace_path.name)}?v={revision}"
            browser_url = f"{PERFETTO_ORIGIN}/#!/?url={urllib.parse.quote(local_url, safe='')}&referrer=gutch_benchmark"
            deadline = time.monotonic() + PERFETTO_REQUEST_TIMEOUT_SECONDS
            server.timeout = 1
            if not webbrowser.open_new_tab(browser_url):
                log(f"Could not open a browser automatically. Open: {browser_url}")
                return False
            while not server.trace_requested and time.monotonic() < deadline:
                server.handle_request()
            if not server.trace_requested:
                log("Perfetto did not request the trace within 30 seconds.")
            return server.trace_requested
    except OSError as error:
        log(f"Could not start the local Perfetto trace server: {error}")
        return False


def write_lane_timeline(label: str, measurements: list[dict], traces: dict,
                        output: Path) -> None:
    """Concatenate measured operations, shifting engine spans with their command."""
    command_trace = output.with_name("commands.json")
    events = [{"ph": "M", "name": "thread_name", "pid": 1, "tid": 1,
               "args": {"name": "Compacted tool time"}}]
    offsets = {command_trace: 0.0}
    start = 0.0
    for measurement in measurements:
        duration = measurement["elapsed_seconds"] * 1_000_000
        events.append({"ph": "X", "name": measurement["operation"], "pid": 1, "tid": 1,
                       "ts": start, "dur": duration,
                       "cat": measurement["boundary"],
                       "args": {"returncode": measurement.get("returncode", 0)}})
        command = measurement.get("command", ())
        if "--profile-dir" in command:
            path = Path(command[command.index("--profile-dir") + 1]) / "trace.json"
            # Engine clocks start after process launch. Align to the envelope's
            # start as an approximation; do not imply cross-process clock sync.
            offsets[path] = start
        start += duration
    command_trace.parent.mkdir(parents=True, exist_ok=True)
    command_trace.write_text(json.dumps({"traceEvents": events}), encoding="utf-8")
    sources = [command_trace, *dict.fromkeys(Path(path) for paths in traces.values() for path in paths)]
    combine_labeled_traces([(label, path) for path in sources], output, source_offsets=offsets)
