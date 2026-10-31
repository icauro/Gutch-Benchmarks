"""Opt-in process CPU and memory sampling for detailed benchmark runs."""
import json
from pathlib import Path
import threading
import time

import psutil


class ProcessMemorySampler:
    def __init__(self, pid: int, timeline: Path | None, interval: float = 0.002):
        self.pid = pid
        self.timeline = timeline
        self.interval = interval
        self.stopped = threading.Event()
        self.result = {"scope": "process_tree_rss; direct_process_cpu", "sampling_interval_seconds": interval,
                       "sample_count": 0, "observed_mean_interval_seconds": None, "sampled_peak_rss_bytes": None,
                       "observed_os_peak_working_set_bytes": None,
                       "sampled_peak_private_bytes": None,
                       "sampled_cpu_seconds": None, "cpu_observed_seconds": None}
        self.thread = threading.Thread(target=self._sample, name="benchmark-memory")

    def start(self):
        self.started = time.perf_counter()
        self.thread.start()

    def finish(self):
        self.stopped.set()
        self.thread.join()
        return self.result

    def _sample(self):
        output = None
        try:
            if self.timeline is not None:
                self.timeline.parent.mkdir(parents=True, exist_ok=True)
                output = self.timeline.open("w", encoding="utf-8")
            process = psutil.Process(self.pid)
            previous = None
            first_cpu = None
            first_seconds = None
            interval_total = 0.0
            while True:
                info = process.memory_info()
                sample = {"seconds": time.perf_counter() - self.started,
                          "rss_bytes": info.rss,
                          "os_peak_working_set_bytes": getattr(info, "peak_wset", None),
                          "private_bytes": getattr(info, "private", None)}
                for child in process.children(recursive=True):
                    try:
                        sample["rss_bytes"] += child.memory_info().rss
                    except psutil.NoSuchProcess:
                        pass
                cpu = process.cpu_times()
                cpu_seconds = cpu.user + cpu.system
                sample["cpu_seconds"] = cpu_seconds
                if first_cpu is None:
                    first_cpu, first_seconds = cpu_seconds, sample["seconds"]
                else:
                    self.result["sampled_cpu_seconds"] = max(0.0, cpu_seconds - first_cpu)
                    self.result["cpu_observed_seconds"] = sample["seconds"] - first_seconds
                self.result["sample_count"] += 1
                if previous is not None:
                    interval_total += sample["seconds"] - previous
                    self.result["observed_mean_interval_seconds"] = interval_total / (self.result["sample_count"] - 1)
                previous = sample["seconds"]
                for source, target in (("rss_bytes", "sampled_peak_rss_bytes"),
                                       ("os_peak_working_set_bytes", "observed_os_peak_working_set_bytes"),
                                       ("private_bytes", "sampled_peak_private_bytes")):
                    value = sample[source]
                    if value is not None:
                        self.result[target] = max(self.result[target] or 0, value)
                if output is not None:
                    output.write(json.dumps(sample) + "\n")
                if self.stopped.wait(self.interval):
                    break
        except psutil.NoSuchProcess:
            pass
        except (psutil.Error, OSError) as error:
            self.result["error"] = str(error)
        finally:
            if output is not None:
                output.close()


def process_utilization(measurements: list[dict]) -> dict:
    """Summarize sequential direct-child commands, weighting CPU by observed time."""
    raw_samples = [item["memory"] for item in measurements if item.get("memory")]
    samples = [item for item in raw_samples if not item.get("error")]
    cpu_samples = [item for item in samples if item.get("sampled_cpu_seconds") is not None
                   and (item.get("cpu_observed_seconds") or 0) > 0]
    result = {}
    if cpu_samples:
        cpu_seconds = sum(item["sampled_cpu_seconds"] for item in cpu_samples)
        observed_seconds = sum(item["cpu_observed_seconds"] for item in cpu_samples)
        result["cpu_percent"] = 100 * cpu_seconds / observed_seconds
        result["sampled_cpu_seconds"] = cpu_seconds
    peaks = [item["sampled_peak_rss_bytes"] for item in samples
             if item.get("sampled_peak_rss_bytes") is not None]
    if peaks and all(not item.get("error") and item.get("sampled_peak_rss_bytes") is not None for item in raw_samples):
        result["peak_rss_bytes"] = max(peaks)
    return result


class DiskSpaceSampler:
    """Sample apparent owned file bytes; never traverse inputs, binaries or logs."""
    def __init__(self, roots, interval=0.1):
        self.roots = roots
        self.interval = interval
        self.stopped = threading.Event()
        self.result = {"peak_disk_bytes": None, "sample_count": 0,
                       "sampling_interval_seconds": interval, "scope": "owned apparent file bytes"}
        self.thread = threading.Thread(target=self._sample, name="benchmark-disk")

    def start(self):
        self.thread.start()

    def finish(self):
        self.stopped.set()
        self.thread.join()
        self.sample()
        return self.result

    def sample(self):
        import os
        total = 0
        seen = set()
        try:
            for root in self.roots:
                def fail(error):
                    raise error
                for directory, dirs, files in os.walk(root, followlinks=False, onerror=fail):
                    excluded = {"commands", "stats", "traces", "kopia-logs"} if Path(directory) == self.roots[0] else set()
                    dirs[:] = [name for name in dirs if name not in excluded
                               and not (Path(directory) / name).is_symlink()]
                    for name in files:
                        path = Path(directory) / name
                        try:
                            if path.is_symlink():
                                continue
                            info = path.stat()
                        except FileNotFoundError:
                            continue  # Tools can remove temporary files between listing and stat.
                        identity = (info.st_dev, info.st_ino)
                        if identity not in seen:
                            seen.add(identity)
                            total += info.st_size
            self.result["sample_count"] += 1
            self.result["peak_disk_bytes"] = max(self.result["peak_disk_bytes"] or 0, total)
        except FileNotFoundError:
            pass  # A tool may atomically replace a directory during traversal.
        except OSError as error:
            self.result["error"] = str(error)

    def _sample(self):
        while True:
            self.sample()
            if self.stopped.wait(self.interval):
                break


def summarize_operation_resources(results, lanes_root):
    """Recover operation peaks from recorded command samples, never workflow totals."""
    from .artifacts import compact_component
    tools = {}
    for result in results:
        if result.get("metadata", {}).get("status") != "PASS":
            continue
        snapshots = result["metadata"].get("snapshots", [])
        if not snapshots:
            continue
        folder = lanes_root / compact_component(result["label"], 32) / "commands"
        commands = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(folder.glob("*.json"))
                    if path.stem.isdecimal()]
        captures, restores, repairs = [], [], []
        for command in commands:
            operation = command.get("operation", "")
            if any(f" {word} " in operation for word in ("capture", "backup", "create", "generate")) and any(operation.endswith(" " + name) for name in snapshots):
                captures.append(command)
            elif " restore " in operation or operation.startswith("reconstruct "):
                restores.append(command)
            elif " repair " in operation or " in-place recovery " in operation:
                repairs.append(command)
        count = len(snapshots)
        groups = {"initial_capture": (captures[:1], 1),
                  "incremental_capture": (captures[1:count], count - 1),
                  "restore": (restores[:count], count), "repair": (repairs[:count], count)}
        values = {}
        for operation, (samples, expected_count) in groups.items():
            if expected_count < 1 or len(samples) != expected_count:
                continue
            peak = process_utilization(samples).get("peak_rss_bytes")
            if peak is not None:
                values[operation] = {"peak_rss_bytes": peak}
            # Only use disk samples explicitly recorded for these commands.
            disk = [sample.get("peak_disk_bytes") for sample in samples]
            if disk and all(value is not None for value in disk):
                values.setdefault(operation, {})["peak_disk_bytes"] = max(disk)
        if values:
            tools[result["metadata"]["case"]] = values
    return tools
