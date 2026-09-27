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
        self.result = {"scope": "process", "sampling_interval_seconds": interval,
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
    samples = [item["memory"] for item in measurements if item.get("memory")]
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
    if peaks:
        result["peak_rss_bytes"] = max(peaks)
    return result
