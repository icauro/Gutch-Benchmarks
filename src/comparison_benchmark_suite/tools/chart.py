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
        records.append(record)
    return records


def _median(record, label, metric):
    value = (record.get("summary", {}).get(label, {}).get(metric) or {}).get("median")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        return None
    return value / 1048576 if metric == "repo_size" else value


def render_svg(records: list[dict]) -> str:
    width, margin, pair_width, cell_width = 1440, 28, 184, 300
    table_top, header_height, row_height = 132, 56, 104
    table_bottom = table_top + header_height + row_height * len(records)
    height = table_bottom + 92
    sources = sorted({record["source_report"].split("/")[1] for record in records if record.get("source_report")})
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
             '<title id="title">Gutch benchmark comparisons</title>',
             '<desc id="description">Blue bars show Gutch; orange bars show the paired tool. Lower values are better. Each cell has its own linear scale. Ratios use raw medians.</desc>',
             f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
             '<g font-family="Segoe UI, Arial, sans-serif" fill="#132644">']

    def text(x, y, value, *, size=14, color="#132644", weight=400, anchor="start"):
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{escape(str(value))}</text>')

    def rect(x, y, w, h, color, radius=0):
        parts.append(f'<rect x="{x}" y="{y}" width="{w:.2f}" height="{h}" rx="{radius}" fill="{color}"/>')

    def line(x1, y1, x2, y2):
        parts.append(f'<path d="M{x1} {y1}H{x2}" stroke="#dde5ef"/>' if y1 == y2 else
                     f'<path d="M{x1} {y1}V{y2}" stroke="#dde5ef"/>')

    text(margin, 48, "Gutch benchmark comparisons", size=32, weight=700)
    text(margin, 80, "Latest saved result for each pair · median values · lower is better", size=16, color="#60718a")
    text(margin, 106, "Each cell uses its own linear scale. Compare the two bars within that cell; pair settings differ.", size=13, color="#60718a")
    for x, color, label in ((1080, BLUE, "Gutch"), (1200, ORANGE, "Paired tool")):
        rect(x, 36, 16, 13, color, 3)
        text(x + 25, 48, label, size=14)
    rect(margin, table_top, width - 2 * margin, table_bottom - table_top, "#f4f7fc", 10)
    text(margin + 20, table_top + 34, "COMPARISON", size=12, color="#60718a", weight=700)
    for index, (_, title, unit) in enumerate(METRICS):
        x = margin + pair_width + index * cell_width
        text(x + 18, table_top + 24, title, size=17, weight=650)
        text(x + 18, table_top + 44, unit, size=12, color="#60718a")
    for index, record in enumerate(records):
        y = table_top + header_height + index * row_height
        rect(margin, y, width - 2 * margin, row_height, "#ffffff" if index % 2 == 0 else "#f8fafd")
        line(margin, y, width - margin, y)
        other = "buildpatchtool" if record["pair"] == "bpt" else record["pair"]
        title = "BuildPatchTool" if record["pair"] == "bpt" else record["pair"].title()
        text(margin + 20, y + 27, "Gutch vs", size=12, color="#60718a")
        text(margin + 20, y + 51, title, size=19, weight=650)
        status = record["status"]
        rect(margin + 20, y + 65, 78, 22, "#e8f6ee" if status == "PASS" else "#fff0e5", 5)
        text(margin + 30, y + 80, status, size=11, color="#177448" if status == "PASS" else "#9a4b14", weight=650)
        for column, (metric, _, unit) in enumerate(METRICS):
            x = margin + pair_width + column * cell_width
            values = [_median(record, label, metric) for label in ("gutch", other)]
            maximum = max((value for value in values if value is not None), default=0)
            for slot, (value, color) in enumerate(zip(values, (BLUE, ORANGE))):
                bar_y = y + 28 + slot * 27
                rect(x + 18, bar_y, 98, 12, "#e8edf5", 2)
                if value is not None:
                    if maximum:
                        rect(x + 18, bar_y, 98 * value / maximum, 12, color, 2)
                    label = f"{value:,.1f} MiB" if unit == "MiB" else f"{value:.3f} s"
                else:
                    label = "—"
                text(x + 130, bar_y + 11, label, size=13, color="#42536b")
            ratio = relative_metric(record, metric)
            number, _, direction = ratio.partition(" ")
            slower = direction == "slower" or (metric == "repo_size" and all(v is not None for v in values) and values[0] > values[1])
            color = "#a65a17" if slower else "#155dc5"
            text(x + 220, y + 43, number.replace("x", "×"), size=20, color=color if ratio != "-" else "#8794a7", weight=700)
            text(x + 220, y + 64, direction, size=12, color=color)
    for column in range(5):
        x = margin + pair_width + column * cell_width
        line(x, table_top, x, table_bottom)
    line(margin, table_bottom, width - margin, table_bottom)
    text(margin, table_bottom + 29, "Time factors describe Gutch relative to its paired tool. Storage factors are Gutch / paired-tool size.", size=13, color="#60718a")
    text(margin, table_bottom + 52, "Source runs: " + ", ".join(sources) + ". OS cache state is uncontrolled; source reports contain settings and provenance.", size=13, color="#60718a")
    text(margin, table_bottom + 73, "Failed pairs and missing or invalid measurements have no relative factor.", size=12, color="#77869a")
    parts.extend(["</g>", "</svg>"])
    return "\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True, help="Saved reports directory")
    parser.add_argument("--output", type=Path, required=True, help="Output SVG path")
    args = parser.parse_args()
    if not args.reports.is_dir():
        parser.error("--reports must name an existing reports directory")
    records = latest_records(args.reports)
    if not any(record.get("source_report") for record in records):
        parser.error("No saved pair reports found")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_svg(records), encoding="utf-8", newline="\n")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
