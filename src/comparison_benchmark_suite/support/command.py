"""One command execution boundary for all benchmark workflows."""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from typing import TextIO
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    elapsed_seconds: float
    returncode: int
    stdout: str
    stderr: str


class CommandError(RuntimeError):
    def __init__(self, result: CommandResult, description: str):
        self.result = result
        self.description = description
        rendered = " ".join(result.command)
        super().__init__(
            f"{description} failed with exit code {result.returncode}: {rendered}\n"
            f"{result.stderr.strip()}"
        )


def _redact(value: str) -> str:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return value
    if not parsed.scheme or not parsed.netloc or not parsed.query:
        return value
    query = [(key, "<redacted>") for key, _ in parse_qsl(parsed.query, keep_blank_values=True)]
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))


def redact_output(value: str) -> str:
    return re.sub(r"https?://[^\s\"<>]+", lambda match: _redact(match.group()), value)


class CommandRunner:
    def __init__(
        self,
        *,
        progress: bool | None = None,
        stream: TextIO | None = None,
        step_wait_seconds: float = 0.0,
        on_step: Callable[[str], None] | None = None,
        memory_profile: bool = False,
        timeout_seconds: float | None = None,
    ):
        self.timeout_seconds = float(timeout_seconds if timeout_seconds is not None else os.environ.get("GUTCH_BENCHMARK_TIMEOUT_SECONDS", "900"))
        if not 0 < self.timeout_seconds < float("inf"):
            raise ValueError("benchmark command timeout must be finite and positive")
        self.memory_profile = memory_profile
        self.temporary_directory: Path | None = None
        self.progress = (stream or sys.stderr).isatty() if progress is None else progress
        self.stream = stream or sys.stderr
        self.step_wait_seconds = step_wait_seconds
        self.on_step = on_step
        self._has_completed_step = False
        self.evidence_directory: Path | None = None
        self.measurements: list[dict] = []
        self.lane_started = time.perf_counter()

    def _print_progress(self, status: str, description: str) -> None:
        if self.progress:
            print(f"[{status}] {description}", file=self.stream, flush=True)

    def begin_lane(self) -> None:
        """Reset the step boundary before starting a new benchmark lane."""
        self._has_completed_step = False
        self.lane_started = time.perf_counter()

    def record_operation(self, description: str, started: float, elapsed: float) -> None:
        """Record an in-process operation on the same clock as subprocesses."""
        self.measurements.append({"operation": description, "boundary": "in_process_elapsed",
                                  "start_seconds": started - self.lane_started,
                                  "elapsed_seconds": elapsed})

    def _wait_for_step(self, description: str) -> None:
        if not self._has_completed_step or self.step_wait_seconds <= 0:
            return
        seconds = self.step_wait_seconds
        print(
            f"\r[wait] next step starts in {seconds:g} s: {description}",
            file=self.stream,
            flush=True,
        )
        time.sleep(seconds)

    def run(
        self,
        command: Sequence[str | Path],
        *,
        description: str,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        expected_failure: bool = False,
        on_output: Callable[[str, bool], None] | None = None,
    ) -> CommandResult:
        rendered = tuple(str(item) for item in command)
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        if self.temporary_directory is not None:
            self.temporary_directory.mkdir(parents=True, exist_ok=True)
            for name in ("TMPDIR", "TMP", "TEMP"):
                process_env[name] = str(self.temporary_directory.resolve())
        self._wait_for_step(description)
        if self.on_step is not None:
            self.on_step(description)
        self._print_progress("run", description)
        started = time.perf_counter()
        memory = {} if self.memory_profile else None
        memory_options = {}
        if memory is not None:
            memory_options = {"memory": memory, "memory_timeline":
                self.evidence_directory / f"{len(self.measurements) + 1:04d}.memory.jsonl"
                if self.evidence_directory is not None else None}
        try:
            stdout, stderr, returncode = self._run_streamed(
                rendered, cwd=cwd, env=process_env, timeout_seconds=self.timeout_seconds, **memory_options,
                on_output=on_output or (lambda line, is_stderr: None),
            )
        except BaseException as error:
            self._print_progress("FAIL", description)
            if self.evidence_directory is not None:
                self.evidence_directory.mkdir(parents=True, exist_ok=True)
                (self.evidence_directory / "command-failure.json").write_text(json.dumps({
                    "operation": description, "error": redact_output(str(error)),
                    "timeout_seconds": self.timeout_seconds}), encoding="utf-8")
            raise
        result = CommandResult(
            command=tuple(_redact(item) for item in rendered),
            elapsed_seconds=time.perf_counter() - started,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )
        measurement = {"operation": description, "boundary": "process_elapsed",
            "start_seconds": started - self.lane_started,
            "elapsed_seconds": result.elapsed_seconds, "command": result.command,
            "returncode": result.returncode}
        if memory is not None:
            measurement["memory"] = memory
        if memory is not None and "--profile-dir" in rendered:
            directory = Path(rendered[rendered.index("--profile-dir") + 1])
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "memory.json").write_text(json.dumps(memory, indent=2), encoding="utf-8")
        self.measurements.append(measurement)
        if self.evidence_directory is not None:
            self.evidence_directory.mkdir(parents=True, exist_ok=True)
            sequence = len(self.measurements)
            (self.evidence_directory / f"{sequence:04d}.json").write_text(
                json.dumps(measurement, indent=2) + "\n", encoding="utf-8")
            (self.evidence_directory / f"{sequence:04d}.stdout.log").write_text(redact_output(stdout), encoding="utf-8")
            (self.evidence_directory / f"{sequence:04d}.stderr.log").write_text(redact_output(stderr), encoding="utf-8")
        success = (result.returncode == 0) != expected_failure
        self._print_progress("done" if success else "FAIL", description)
        self._has_completed_step = True
        if not success:
            raise CommandError(result, description)
        return result

    @staticmethod
    def _run_streamed(
        rendered: tuple[str, ...],
        *,
        cwd: Path | None,
        env: Mapping[str, str],
        on_output: Callable[[str, bool], None],
        memory: dict | None = None,
        memory_timeline: Path | None = None,
        timeout_seconds: float = 900,
    ) -> tuple[str, str, int]:
        process = subprocess.Popen(
            rendered,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            start_new_session=os.name != "nt",
        )
        sampler = None
        if memory is not None:
            from comparison_benchmark_suite.support.memory import ProcessMemorySampler
            sampler = ProcessMemorySampler(process.pid, memory_timeline)
            sampler.start()
        events: queue.Queue[tuple[bool, str | BaseException | None]] = queue.Queue()

        def read_stream(stream: TextIO, is_stderr: bool) -> None:
            try:
                for line in iter(stream.readline, ""):
                    events.put((is_stderr, line))
            except BaseException as error:
                events.put((is_stderr, error))
            finally:
                stream.close()
                events.put((is_stderr, None))

        threads = [
            threading.Thread(
                target=read_stream,
                args=(stream, is_stderr),
                daemon=True,
            )
            for stream, is_stderr in (
                (process.stdout, False),
                (process.stderr, True),
            )
            if stream is not None
        ]
        for thread in threads:
            thread.start()

        stdout_lines: list[str] = []
        stderr_lines: list[str] = []
        closed_streams = 0
        deadline = time.monotonic() + timeout_seconds
        try:
            while closed_streams < len(threads):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(tuple(_redact(item) for item in rendered), timeout_seconds)
                try:
                    is_stderr, line = events.get(timeout=remaining)
                except queue.Empty:
                    raise subprocess.TimeoutExpired(tuple(_redact(item) for item in rendered), timeout_seconds) from None
                if line is None:
                    closed_streams += 1
                    continue
                if isinstance(line, BaseException):
                    raise line
                (stderr_lines if is_stderr else stdout_lines).append(line)
                on_output(line, is_stderr)
            returncode = process.wait(timeout=max(0.001, deadline - time.monotonic()))
        except BaseException:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
            else:
                import signal
                try: os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
            process.wait()
            raise
        finally:
            if sampler is not None:
                memory.update(sampler.finish())
            for thread in threads:
                thread.join(timeout=5)
        return "".join(stdout_lines), "".join(stderr_lines), returncode
