"""Human-readable benchmark reports for completed Gutch lanes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from comparison_benchmark_suite.tools.models import FixtureSpec, LaneResult


def _format_mib(byte_count: int) -> str:
    return f"{byte_count / 1_048_576:.2f} MiB"


def _number(result: LaneResult, *keys: str) -> float | int | None:
    for key in keys:
        value = result.metrics.get(key)
        if isinstance(value, (int, float)):
            return value
    return None


def _seconds(result: LaneResult, *keys: str) -> str:
    value = _number(result, *keys)
    return "-" if value is None else f"{float(value):.2f} s"


def _speed(source_mib: float, result: LaneResult, *keys: str) -> str:
    value = _number(result, *keys)
    return "-" if value is None or float(value) <= 0 else f"{source_mib / float(value):.1f} MiB/s"


def _comparison(result: LaneResult) -> str:
    if result.metadata.get("status") not in {None, "PASS"}:
        return result.metadata["status"]
    differences = result.metadata.get("differences", [])
    if not differences:
        return "OK"
    return f"FAIL ({len(differences)})" if isinstance(differences, list) else "FAIL"


def _table(title: str, headers: list[str], rows: list[tuple[str, list[str]]]) -> None:
    label_width = max(20, max(len(label) for label, _ in rows))
    lane_widths = [
        max(14, len(header), max(len(values[index]) for _, values in rows))
        for index, header in enumerate(headers)
    ]
    separator = "+" + "-" * (label_width + 2) + "+"
    for width in lane_widths:
        separator += "-" * (width + 2) + "+"
    print(separator)
    header_cells = [" " * label_width]
    header_cells.extend(header.ljust(width) for header, width in zip(headers, lane_widths, strict=True))
    print("| " + " | ".join(header_cells) + " |")
    print(separator)
    for label, values in rows:
        cells = [label.ljust(label_width)]
        cells.extend(value.rjust(width) for value, width in zip(values, lane_widths, strict=True))
        print("| " + " | ".join(cells) + " |")
    print(separator)


def print_comparison_table(
    fixture: FixtureSpec,
    product: Path,
    results: list[LaneResult],
) -> None:
    """Show measured snapshots, then totals and optional verification/recovery."""
    if not results:
        return
    headers = [result.label for result in results]
    measurements = [result.metadata.get("snapshot_metrics", {}) for result in results]
    snapshot_names = list(dict.fromkeys(name for values in measurements for name in values))

    def seconds(value):
        return "-" if value is None else f"{value:.2f} s"

    def average(values, key):
        samples = [metrics[key] for metrics in values.values() if metrics.get(key) is not None]
        return seconds(sum(samples) / len(samples)) if samples else "-"

    def bytes_value(result, *keys):
        value = _number(result, *keys)
        return "-" if value is None else _format_mib(int(value))

    def ratio(result):
        size = _number(result, "repo_size", "growth")
        source = result.metrics.get("input_bytes", 0)
        return "-" if size is None or source == 0 else f"{size / source * 100:.1f} %"

    print()
    print(f"  Fixture Benchmark: {fixture.name} / {product.name}")
    fingerprints = {result.metadata.get("dataset_sha256") for result in results}
    if len(fingerprints - {None}) > 1:
        print("  Note: lanes use different input inventories; compare matching workloads only.")
    if any(result.kind == "filesystem-copy" for result in results):
        print("  Filesystem capture/restore = source-to-storage / storage-to-output copies.")
    if any(result.kind == "gutch-batch" for result in results):
        print("  Batch capture is timed as one operation; individual capture times are unavailable.")
    for name in snapshot_names:
        print(f"\n  Snapshot: {name}")
        rows = [
            ("Input bytes", [_format_mib(values[name]["input_bytes"]) if name in values else "-" for values in measurements]),
            ("Capture time", [seconds(values.get(name, {}).get("backup")) for values in measurements]),
            ("Reconstruct time", [seconds(values.get(name, {}).get("restore")) for values in measurements]),
            ("Comparison", [_comparison(result) if name in values else "-"
                            for result, values in zip(results, measurements, strict=True)]),
        ]
        _table("Snapshot", headers, rows)

    rows = [
        ("Total input bytes", [bytes_value(result, "input_bytes") for result in results]),
        ("Capture total", [_seconds(result, "backup") for result in results]),
        ("Capture average", [average(values, "backup") for values in measurements]),
        ("Reconstruct total", [_seconds(result, "restore", "fetch_reconstruct") for result in results]),
        ("Reconstruct average", [average(values, "restore") for values in measurements]),
        ("Capture speed", [_speed(float(result.metrics.get("input_bytes", 0)) / 1_048_576, result, "backup") for result in results]),
        ("Reconstruct speed", [_speed(float(result.metrics.get("input_bytes", 0)) / 1_048_576, result, "restore", "fetch_reconstruct") for result in results]),
        ("Stored size (final)", [bytes_value(result, "repo_size", "growth") for result in results]),
        ("Stored size ratio", [ratio(result) for result in results]),
        ("Comparison", [_comparison(result) for result in results]),
    ]
    print("\n  Summary (averages per measured snapshot; speed = total bytes / total time)")
    _table("Summary", headers, rows)

    additional = []
    for label, key in [("Embedded verify", "verify"), ("Repository check", "repository_check"),
                       ("Corrupt time", "corrupt"), ("Incremental repair", "repair"),
                       ("Full restore recovery", "full_restore_recovery")]:
        values = [
            _seconds(result, key) if key in {"verify", "repository_check"}
            or result.metadata.get("corrupt_repair_after_reconstruct") else "-"
            for result in results
        ]
        if any(value != "-" for value in values):
            additional.append((label, values))
    if additional:
        print("\n  Verification and recovery (embedded verify is included in reconstruct time)")
        _table("Verification and recovery", headers, additional)


def _trace_paths(result: LaneResult) -> list[Path]:
    return [
        Path(path)
        for paths in result.traces.values()
        for path in paths
        if Path(path).is_file()
    ]


def _read_trace_spans(path: Path) -> list[tuple[str, float, dict[str, Any]]]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    events = document.get("traceEvents", [])
    if not isinstance(events, list):
        return []
    stacks: dict[tuple[object, object, str], list[tuple[int, dict[str, Any]]]] = {}
    spans: list[tuple[str, float, dict[str, Any]]] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        name = event.get("name")
        phase = event.get("ph")
        timestamp = event.get("ts")
        if not isinstance(name, str) or not isinstance(timestamp, int) or name == "cli.command":
            continue
        key = (event.get("pid"), event.get("tid"), name)
        if phase == "X":
            spans.append((name, max(0, event.get("dur", 0)) / 1_000_000, event.get("args", {})))
        elif phase == "B":
            args = event.get("args", {})
            stacks.setdefault(key, []).append((timestamp, args if isinstance(args, dict) else {}))
        elif phase == "E" and stacks.get(key):
            started_at, args = stacks[key].pop()
            spans.append((name, max(0, timestamp - started_at) / 1_000_000, args))
    return spans


def _aggregate_spans(paths: list[Path]) -> dict[str, tuple[int, float]]:
    aggregates: dict[str, tuple[int, float]] = {}
    for path in paths:
        for name, seconds, _ in _read_trace_spans(path):
            count, total = aggregates.get(name, (0, 0.0))
            aggregates[name] = (count + 1, total + seconds)
    return aggregates


def _aggregate_hash_metrics(paths: list[Path]) -> dict[str, Any]:
    count = 0
    mib = 0.0
    seconds = 0.0
    modes: dict[str, int] = {}
    workers: set[int] = set()
    for path in paths:
        for name, elapsed, args in _read_trace_spans(path):
            if name != "installation.file.verify":
                continue
            size_mib = args.get("size_bytes", 0) / 1048576
            if not isinstance(size_mib, (int, float)):
                continue
            count += 1
            mib += float(size_mib)
            seconds += elapsed
            mode = args.get("hash_mode")
            if isinstance(mode, str):
                modes[mode] = modes.get(mode, 0) + 1
            configured_workers = args.get("configured_workers")
            if isinstance(configured_workers, int):
                workers.add(configured_workers)
    return {"count": count, "mib": mib, "seconds": seconds, "modes": modes, "workers": workers}


def _format_hash_modes(value: Any) -> str:
    return "-" if not isinstance(value, dict) or not value else ", ".join(
        f"{mode}={count}" for mode, count in sorted(value.items()) if isinstance(mode, str) and isinstance(count, int)
    )


def _format_workers(value: Any) -> str:
    return "-" if not isinstance(value, set) or not value else ", ".join(str(worker) for worker in sorted(value))


def print_gutch_profile_table(results: list[LaneResult]) -> None:
    """Print detailed Gutch trace spans and hash workload information."""
    aggregates = [(result.label, _aggregate_spans(_trace_paths(result))) for result in results]
    aggregates = [(label, values) for label, values in aggregates if values]
    if not aggregates:
        return
    names = sorted(
        set().union(*(values for _, values in aggregates)),
        key=lambda name: sum(values[name][1] for _, values in aggregates if name in values),
        reverse=True,
    )[:32]
    rows = [
        (
            name,
            ["-" if name not in values else f"{values[name][1]:.2f} s ({values[name][0]})" for _, values in aggregates],
        )
        for name in names
    ]
    hash_metrics = [(result.label, _aggregate_hash_metrics(_trace_paths(result))) for result in results]
    if any(int(metrics["count"]) > 0 for _, metrics in hash_metrics):
        by_label = {label: metrics for label, metrics in hash_metrics}
        rows.extend(
            [
                ("Hash files", [str(int(by_label[label]["count"])) for label, _ in aggregates]),
                ("Hash bytes", [f"{float(by_label[label]['mib']):.2f} MiB" for label, _ in aggregates]),
                ("Hash time", [f"{float(by_label[label]['seconds']):.2f} s" for label, _ in aggregates]),
                (
                    "Hash speed",
                    [
                        (
                            f"{float(by_label[label]['mib']) / float(by_label[label]['seconds']):.1f} MiB/s"
                            if float(by_label[label]["seconds"]) > 0
                            else "-"
                        )
                        for label, _ in aggregates
                    ],
                ),
                ("Hash modes", [_format_hash_modes(by_label[label]["modes"]) for label, _ in aggregates]),
                ("Reconstruct workers", [_format_workers(by_label[label]["workers"]) for label, _ in aggregates]),
            ]
        )
    print()
    print("  Gutch Perfetto Profiles")
    print("  note: values are inclusive recorded spans; nested spans overlap and recording limits may omit jobs.")
    _table("Gutch Perfetto Profiles", [label for label, _ in aggregates], rows)


def print_fixture_report(fixture: FixtureSpec, product: Path, results: list[LaneResult]) -> None:
    print_comparison_table(fixture, product, results)
    print_gutch_profile_table(results)


def ascii_comparison_table(rows: list[list[str]]) -> str:
    """Render the same comparison cells used by the Markdown report."""
    headers = ["Tool", "Status", "Capture s", "Restore s", "Repair s", "Recovery s", "Stored MiB", "CPU %", "Peak RSS MiB"]
    widths = [max(len(row[index]) for row in [headers, *rows]) for index in range(len(headers))]
    border = "+-" + "-+-".join("-" * width for width in widths) + "-+"

    def line(cells, *, numeric=False):
        return "| " + " | ".join(
            cell.rjust(width) if numeric and index >= 2 else cell.ljust(width)
            for index, (cell, width) in enumerate(zip(cells, widths, strict=True))
        ) + " |"

    return "\n".join([border, line(headers), border,
                       *(line(row, numeric=True) for row in rows), border])
