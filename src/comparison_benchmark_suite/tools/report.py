"""Shared comparison summary for the CLI, Markdown, and interactive UI."""

import json
import math
from pathlib import Path
from .models import LaneResult


COMPARISON_HEADERS = ["Tool", "Status", "Capture s", "Restore s", "Repair s", "Recovery s", "Stored MiB", "CPU %", "Peak RSS MiB"]


def relative_metric(record: dict, metric: str) -> str:
    """Compare valid, equally sampled raw medians for a successful pair."""
    other = "buildpatchtool" if record["pair"] == "bpt" else record["pair"]
    statuses = {row[0]: row[1] for row in record.get("rows", [])}
    if record["status"] != "PASS" or any(statuses.get(label) != "PASS" for label in ("gutch", other)):
        return "-"
    summary = record.get("summary", {})
    gutch = summary.get("gutch", {}).get(metric) or {}
    peer = summary.get(other, {}).get(metric) or {}
    values = (gutch.get("median"), peer.get("median"))
    if (gutch.get("samples") != peer.get("samples") or
            any(isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value <= 0 for value in values)):
        return "-"
    gutch_value, peer_value = values
    if metric == "repo_size":
        percent = round(100 * (gutch_value / peer_value - 1), 1)
        if percent == 0:
            return "same size"
        return f"{abs(percent):g}% {'smaller' if percent < 0 else 'larger'}"
    if max(gutch_value, peer_value) / min(gutch_value, peer_value) < 1.005:
        return "~same"
    if gutch_value < peer_value:
        return f"{peer_value / gutch_value:.2f}x faster"
    return f"{gutch_value / peer_value:.2f}x slower"


def comparison_rows(summary: dict, results: list[dict]) -> list[list[str]]:
    rows = []
    columns = [("backup", 1), ("restore", 1), ("repair", 1), ("full_restore_recovery", 1),
               ("repo_size", 1048576), ("cpu_percent", 1), ("peak_rss_bytes", 1048576)]
    for label, metrics in summary.items():
        statuses = sorted({result["metadata"]["status"] for result in results
                           if result["metadata"]["case"] == label})
        row = [label, ", ".join(statuses)]
        for key, divisor in columns:
            median = metrics.get(key, {}).get("median") if isinstance(metrics.get(key), dict) else None
            row.append("-" if median is None else f"{median / divisor:.3f}")
        rows.append(row)
    return rows


def ascii_comparison_table(rows: list[list[str]]) -> str:
    """Render the same comparison cells used by the Markdown report."""
    headers = COMPARISON_HEADERS
    widths = [max(len(row[index]) for row in [headers, *rows]) for index in range(len(headers))]
    border = "+-" + "-+-".join("-" * width for width in widths) + "-+"

    def line(cells, *, numeric=False):
        return "| " + " | ".join(
            cell.rjust(width) if numeric and index >= 2 else cell.ljust(width)
            for index, (cell, width) in enumerate(zip(cells, widths, strict=True))
        ) + " |"

    return "\n".join([border, line(headers), border,
                       *(line(row, numeric=True) for row in rows), border])


def write_comparison_report(directory: Path, description: str, results: list[LaneResult]) -> None:
    utilization_note = "CPU/RSS: detailed mode only, direct tool processes; 100% CPU = one core. Child processes and harness excluded."
    summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
    lines = ["# Comparison benchmark", "", description, "", "OS cache state: uncontrolled. Times are median seconds.", "",
             "| " + " | ".join(COMPARISON_HEADERS) + " |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    rows = comparison_rows(summary, [result.as_json() for result in results])
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    reasons = dict.fromkeys(result.metadata["reason"] for result in results if result.metadata.get("reason"))
    lines.extend(["", *reasons, "", "Restore includes the tool's own verification. Independent SHA-256 validation is outside command timing.",
                  "", "Raw samples and operation semantics: results.json. Aggregate medians and ranges: summary.json. Perfetto overview: trace.json (compacted tool time; harness gaps omitted, not concurrent execution)."])
    lines.extend(["", utilization_note])
    (directory / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\nComparison: median seconds across measured runs; warm-ups excluded.")
    print(ascii_comparison_table(rows))
    print("Repair = in-place; recovery = full restore. '-' = not measured.")
    print("Independent validation is outside timings. OS cache is uncontrolled.")
    print(utilization_note)
    for reason in reasons:
        print(reason)
