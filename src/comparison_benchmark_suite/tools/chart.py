"""Render a paired-bar SVG from the latest saved result for each comparison."""

import argparse
from html import escape
import json
import math
from pathlib import Path

from .. import FIXTURES
from .report import relative_metric


METRICS = (("backup", "Capture", "seconds"), ("restore", "Restore", "seconds"),
           ("repair", "Repair", "seconds"), ("repo_size", "Stored size", "MiB"))
RESOURCE_METRICS = tuple(
    (f"{operation}_{kind}", f"{title}\n{kind.upper() if kind == 'ram' else 'disk'}", "MiB")
    for operation, title in (("initial_capture", "First capture"), ("incremental_capture", "Second capture"),
                             ("restore", "Restore"), ("repair", "Repair"))
    for kind in ("ram", "disk")
)
# Keep references stable when chart rows are reordered or only one pair is rendered.
PAIR_NOTES = {"borg": 1, "plakar": 2, "kopia": 3, "restic": 4, "rustic": 5, "bpt": 6}
BLUE, ORANGE = "#2474f5", "#f78b32"


def latest_records(reports: Path) -> list[dict]:
    """Select by report date, numeric run ID and attempt; keep failures visible."""
    records = []
    for fixture in sorted(FIXTURES.glob("gutch_vs_*.yaml")):
        pair = fixture.stem.removeprefix("gutch_vs_")
        candidates = list(reports.glob(f"*/*/{pair}.json"))
        record = {"pair": pair, "status": "NOT_RUN", "rows": []}
        if candidates:
            source = max(candidates, key=lambda path: (
                path.parent.parent.name, tuple(int(part) for part in path.parent.name.split("-"))))
            try:
                record = json.loads(source.read_text(encoding="utf-8"))
                if not isinstance(record, dict) or record.get("pair") != pair:
                    raise ValueError("Pair report does not match its filename")
            except (OSError, ValueError):
                record = {"pair": pair, "status": "ERROR", "rows": []}
            record["source_report"] = source.relative_to(reports).as_posix()
            resources = source.with_name(f"{pair}-resources.json")
            if resources.is_file():
                record["operation_resources"] = json.loads(resources.read_text(encoding="utf-8"))["operation_resources"]
        records.append(record)
    return records


def _median(record, label, metric, unit):
    value = (record.get("summary", {}).get(label, {}).get(metric) or {}).get("median")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        return None
    return value / 1048576 if unit == "MiB" else value


def render_svg(records: list[dict], *, metrics=METRICS, title="Gutch benchmark comparisons") -> str:
    margin, pair_width, cell_width = 8, 148, 150
    width = 2 * margin + pair_width + len(metrics) * cell_width
    table_top, header_height, row_height = 52, 46, 90
    table_bottom = table_top + header_height + row_height * len(records)
    height = table_bottom + 10
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
             f'<title id="title">{escape(title)}</title>',
             '<desc id="description">Blue bars show Gutch; orange bars show the paired tool. Lower values are better. Each cell has its own linear scale. Ratios use raw medians. Bracketed numbers refer to the README comparison notes.</desc>',
             f'<rect width="{width}" height="{height}" fill="#000000"/>',
             '<g font-family="Segoe UI, Arial, sans-serif" fill="#edf2fa">']

    def text(x, y, value, *, size=14, color="#edf2fa", weight=400, anchor="start"):
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{escape(str(value))}</text>')

    def rect(x, y, w, h, color, radius=0):
        parts.append(f'<rect x="{x}" y="{y}" width="{w:.2f}" height="{h}" rx="{radius}" fill="{color}"/>')

    def line(x1, y1, x2, y2):
        parts.append(f'<path d="M{x1} {y1}H{x2}" stroke="#29313d"/>' if y1 == y2 else
                     f'<path d="M{x1} {y1}V{y2}" stroke="#29313d"/>')

    text(margin, 34, title, size=25, weight=700)
    for x, color, label in ((width - 274, BLUE, "Gutch"), (width - 164, ORANGE, "Paired tool")):
        rect(x, 23, 16, 13, color, 3)
        text(x + 23, 34, label, size=16)
    rect(margin, table_top, width - 2 * margin, table_bottom - table_top, "#161b22", 10)
    text(margin + 6, table_top + 28, "COMPARISON", size=13, color="#a3afc2", weight=700)
    for index, (_, title, unit) in enumerate(metrics):
        x = margin + pair_width + index * cell_width
        heading, _, detail = title.partition("\n")
        text(x + 7, table_top + 21, heading, size=17, weight=650)
        text(x + 7, table_top + 38, f"{detail} · {unit}" if detail else unit, size=13, color="#a3afc2")
    for index, record in enumerate(records):
        y = table_top + header_height + index * row_height
        rect(margin, y, width - 2 * margin, row_height, "#000000" if index % 2 == 0 else "#0d1117")
        line(margin, y, width - margin, y)
        other = "buildpatchtool" if record["pair"] == "bpt" else record["pair"]
        title = "BuildPatchTool" if record["pair"] == "bpt" else record["pair"].title()
        text(margin + 6, y + 23, "Gutch vs", size=14, color="#a3afc2")
        reference = PAIR_NOTES.get(record["pair"])
        label = f"{title} [{reference}]" if reference is not None else title
        text(margin + 6, y + 47, label, size=14 if record["pair"] == "bpt" else 17, weight=650)
        status = record["status"]
        if status != "PASS":
            text(margin + 6, y + 77, status, size=13, color="#ffba78", weight=650)
        for column, (metric, _, unit) in enumerate(metrics):
            x = margin + pair_width + column * cell_width
            values = [_median(record, label, metric, unit) for label in ("gutch", other)]
            maximum = max((value for value in values if value is not None), default=0)
            for slot, (value, color) in enumerate(zip(values, (BLUE, ORANGE))):
                bar_y = y + 16 + slot * 25
                rect(x + 7, bar_y, 42, 12, "#252d3a", 2)
                if value is not None:
                    if maximum:
                        rect(x + 7, bar_y, 42 * value / maximum, 12, color, 2)
                    label = f"{value:,.1f}" if unit == "MiB" else f"{value:.3f}"
                else:
                    label = "—"
                text(x + 58, bar_y + 12, label, size=17, color="#c5cedc")
            ratio = relative_metric(record, metric, size_metric=unit == "MiB")
            slower = ratio.endswith(("slower", "larger"))
            neutral = ratio in ("-", "~same", "same size")
            color = "#a3afc2" if neutral else ("#ffb36b" if slower else "#71a7ff")
            text(x + 7, y + 79, ratio.replace("x", "×"), size=17, color=color, weight=700)
    for column in range(len(metrics) + 1):
        x = margin + pair_width + column * cell_width
        line(x, table_top, x, table_bottom)
    line(margin, table_bottom, width - margin, table_bottom)
    parts.extend(["</g>", "</svg>"])
    return "\n".join(parts) + "\n"



def render_resources_svg(records: list[dict]) -> str:
    """Use the same paired-bar template with resource columns and saved values."""
    resource_records = []
    for record in records:
        summary = {}
        for tool, operations in record.get("operation_resources", {}).items():
            summary[tool] = {}
            for metric, _, _ in RESOURCE_METRICS:
                operation, kind = metric.rsplit("_", 1)
                field = "peak_rss_bytes" if kind == "ram" else "peak_disk_bytes"
                value = operations.get(operation, {}).get(field) if record.get("status") == "PASS" else None
                summary[tool][metric] = {"median": value, "samples": 1}
        resource_records.append({**record, "summary": summary})
    return render_svg(resource_records, metrics=RESOURCE_METRICS, title="Peak resources by operation")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True, help="Saved reports directory")
    parser.add_argument("--output", type=Path, required=True, help="Output SVG path")
    parser.add_argument("--resources-output", type=Path, help="Optional resource-table SVG output")
    args = parser.parse_args()
    if not args.reports.is_dir():
        parser.error("--reports must name an existing reports directory")
    records = latest_records(args.reports)
    if not any(record.get("source_report") for record in records):
        parser.error("No saved pair reports found")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_svg(records), encoding="utf-8", newline="\n")
    print(args.output.resolve())
    if args.resources_output is not None:
        args.resources_output.parent.mkdir(parents=True, exist_ok=True)
        args.resources_output.write_text(render_resources_svg(records), encoding="utf-8", newline="\n")
        print(args.resources_output.resolve())


if __name__ == "__main__":
    main()
