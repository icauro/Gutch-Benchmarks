"""Shared comparison summary for the CLI, Markdown, and interactive UI."""

import json
import math
from pathlib import Path
from .models import LaneResult


COMPARISON_HEADERS = ["Tool", "Status", "Capture s", "Restore s", "Repair s", "Recovery s", "Stored MiB", "CPU %", "Peak RAM MiB", "Peak disk MiB"]


TOOL_SOURCES = {
    "gutch": ("Gutch", "https://github.com/icauro/Gutch"),
    "restic": ("Restic", "https://github.com/restic/restic"),
    "kopia": ("Kopia", "https://github.com/kopia/kopia"),
    "borg": ("Borg", "https://github.com/borgbackup/borg"),
    "rustic": ("Rustic", "https://github.com/rustic-rs/rustic"),
    "plakar": ("Plakar", "https://github.com/PlakarKorp/plakar"),
    "buildpatchtool": ("BuildPatchTool", "https://github.com/EpicGames/UnrealEngine"),
}


def markdown_tool_name(label):
    source = TOOL_SOURCES.get(label)
    return f"[{source[0]}]({source[1]})" if source else label


def relative_metric(record: dict, metric: str, *, size_metric: bool = False) -> str:
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
    if size_metric or metric in {"repo_size", "peak_rss_bytes", "peak_disk_bytes"}:
        percent = round(100 * (gutch_value / peer_value - 1), 1)
        if percent == 0:
            return "same size" if metric == "repo_size" else "~same"
        return f"{abs(percent):g}% {'smaller' if percent < 0 else 'larger'}"
    if max(gutch_value, peer_value) / min(gutch_value, peer_value) < 1.005:
        return "~same"
    if gutch_value < peer_value:
        return f"{peer_value / gutch_value:.2f}x faster"
    return f"{gutch_value / peer_value:.2f}x slower"


def comparison_rows(summary: dict, results: list[dict]) -> list[list[str]]:
    rows = []
    columns = [("backup", 1), ("restore", 1), ("repair", 1), ("full_restore_recovery", 1),
               ("repo_size", 1048576), ("cpu_percent", 1), ("peak_rss_bytes", 1048576), ("peak_disk_bytes", 1048576)]
    for label in sorted(summary, key=lambda label: label != "gutch"):
        metrics = summary[label]
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



def operation_resource_table(record):
    resources = record.get("operation_resources", {})
    if not resources:
        return []
    other = "buildpatchtool" if record["pair"] == "bpt" else record["pair"]
    lines = ["**Resources by operation (MiB)**", "",
             "| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |",
             "|---|" + "---:|" * 8]
    for label in ("gutch", other):
        cells = []
        for operation in ("initial_capture", "incremental_capture", "restore", "repair"):
            for metric in ("peak_rss_bytes", "peak_disk_bytes"):
                value = resources.get(label, {}).get(operation, {}).get(metric)
                cells.append("—" if value is None else f"{value / 1048576:,.1f}")
        lines.append("| " + markdown_tool_name(label) + " | " + " | ".join(cells) + " |")
    lines.extend(["", "RAM is the largest sampled process-tree RSS across commands in that operation. "
                  "Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; "
                  "whole-workflow disk peaks are not reused here.", ""])
    return lines

DETAIL_METRICS = (("initial_capture", "First capture s"), ("incremental_capture", "Later-version capture s"),
                  ("repo_growth_bytes", "Later-version stored growth bytes"),
                  ("restore_validated", "Restore + independent validation s"),
                  ("repair_validated", "Content repair + validation s"),
                  ("hidden_repair_validated", "Preserved-mtime repair + validation s"),
                  ("exact_recovery_validated", "Extra-file cleanup + validation s"),
                  ("full_restore_recovery_validated", "Full restore recovery + validation s"))


def measurement_details(summary):
    """Display medians and observed ranges without implying statistical confidence."""
    labels = sorted(summary, key=lambda label: label != "gutch")
    lines = ["| Measurement | " + " | ".join(markdown_tool_name(label) for label in labels) + " |",
             "|---|" + "---:|" * len(labels)]
    for metric, title in DETAIL_METRICS:
        cells = []
        for label in labels:
            value = summary[label].get(metric)
            cells.append("-" if not value else
                         f"{value['median']:.3f} ({value['minimum']:.3f}–{value['maximum']:.3f}; n={value['samples']})")
        lines.append("| " + title + " | " + " | ".join(cells) + " |")
    return ["Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.", "", *lines, ""]


def write_comparison_report(directory: Path, description: str, results: list[LaneResult]) -> None:
    utilization_note = "RAM/disk: sampled in a separate resource pass; RSS includes descendants. Disk is owned apparent file bytes. CPU 100% = one core; harness excluded."
    summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
    lines = ["# Comparison benchmark", "", description, "", "OS cache state: uncontrolled. Times are median seconds.", "",
             "| " + " | ".join(COMPARISON_HEADERS) + " |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    rows = comparison_rows(summary, [result.as_json() for result in results])
    for row in rows:
        lines.append("| " + " | ".join([markdown_tool_name(row[0]), *row[1:]]) + " |")
    reasons = dict.fromkeys(result.metadata["reason"] for result in results if result.metadata.get("reason"))
    lines.extend(["", *reasons, "", "Restore includes the tool's own verification. Independent SHA-256 validation is outside command timing.",
                  "", "Raw samples and operation semantics: results.json. Aggregate medians and ranges: summary.json. Perfetto overview: trace.json (compacted tool time; harness gaps omitted, not concurrent execution)."])
    if any(result.metadata.get("measurement_contract") == 2 for result in results):
        lines.extend(["", "## Common outcomes and variability", "", *measurement_details(summary)])
        for result in results:
            lines.extend([f"{result.label} operations: `{result.metadata.get('operations', {})}`", ""])
    lines.extend(["", utilization_note])
    (directory / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\nComparison: median seconds across measured runs; warm-ups excluded.")
    print(ascii_comparison_table(rows))
    print("Repair = in-place; recovery = full restore. '-' = not measured.")
    print("Independent validation is outside timings. OS cache is uncontrolled.")
    print(utilization_note)
    for reason in reasons:
        print(reason)
