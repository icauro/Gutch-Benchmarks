"""Saved-result selection, faithful bar geometry and safe static SVG output."""

import json
import math
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from comparison_benchmark_suite.tools.chart import BLUE, ORANGE, latest_records, render_svg, render_resources_svg


ROOT = Path(__file__).resolve().parents[1]


def pair_record(pair="restic", status="PASS"):
    other = "buildpatchtool" if pair == "bpt" else pair
    return {"pair": pair, "status": status,
            "rows": [[label, "PASS"] for label in ("gutch", other)],
            "summary": {label: {metric: {"median": value, "samples": 3}
                               for metric in ("backup", "restore", "repair", "repo_size")}
                        for label, value in (("gutch", 1), (other, 2))}}


class ChartTests(unittest.TestCase):
    def test_bar_lengths_are_linear_and_rendering_is_deterministic(self):
        chart = render_svg([pair_record()])
        self.assertEqual(chart, render_svg([pair_record()]))
        root = ET.fromstring(chart)
        lengths = {}
        for color in (BLUE, ORANGE):
            bars = [node for node in root.iter("{http://www.w3.org/2000/svg}rect")
                    if node.get("fill") == color and node.get("height") == "12"]
            self.assertEqual(len(bars), 4)
            lengths[color] = [float(node.get("width")) for node in bars]
        for gutch, other in zip(lengths[BLUE], lengths[ORANGE]):
            self.assertAlmostEqual(gutch / other, 0.5)
        self.assertIn("2.00×", chart)
        self.assertIn("50% smaller", chart)

    def test_failed_or_null_measurements_do_not_block_other_pairs(self):
        failed = pair_record("borg", "ERROR")
        failed["summary"]["gutch"]["repair"] = None
        failed["summary"]["borg"]["backup"]["median"] = float("nan")
        chart = render_svg([failed, pair_record()])
        root = ET.fromstring(chart)
        for node in root.iter("{http://www.w3.org/2000/svg}rect"):
            self.assertTrue(math.isfinite(float(node.get("width"))))
        self.assertIn("ERROR", chart)
        self.assertIn("Restic", chart)
        self.assertEqual(chart.count("2.00×"), 3)  # Only the successful pair's timings.

    def test_small_differences_are_not_misleading_one_times_factors(self):
        record = pair_record()
        record["summary"]["gutch"]["repo_size"]["median"] = 2.008
        record["summary"]["gutch"]["backup"]["median"] = 2.008
        chart = render_svg([record])
        self.assertIn("0.4% larger", chart)
        self.assertIn("~same", chart)
        self.assertNotIn("1.00×", chart)
        record["summary"]["gutch"]["repo_size"]["median"] = 1.992
        self.assertIn("0.4% smaller", render_svg([record]))
        record["summary"]["gutch"]["repo_size"]["median"] = 2
        self.assertIn("same size", render_svg([record]))

    def test_report_text_is_xml_escaped(self):
        chart = render_svg([pair_record("restic&<script>")])
        root = ET.fromstring(chart)
        self.assertIn("Restic&amp;&lt;Script&gt;", chart)
        self.assertFalse(list(root.iter("{http://www.w3.org/2000/svg}script")))

    def test_resource_svgs_share_four_operation_columns_and_pair_bars(self):
        record = pair_record()
        record["operation_resources"] = {
            "gutch": {"initial_capture": {"peak_rss_bytes": 1048576}},
            "restic": {"initial_capture": {"peak_rss_bytes": 2097152}}}
        chart = render_resources_svg([record], kind="ram")
        self.assertEqual(chart, render_resources_svg([record], kind="ram"))
        root = ET.fromstring(chart)
        labels = [node.text for node in root.iter("{http://www.w3.org/2000/svg}text")]
        self.assertIn("Peak RAM by operation", labels)
        self.assertEqual(labels.count("MiB"), 4)
        self.assertIn("First capture", labels)
        self.assertIn("Second capture", labels)
        self.assertIn("Gutch", labels)
        self.assertIn("Restic [4]", labels)
        self.assertIn("1.0", labels)
        self.assertIn("2.0", labels)
        self.assertEqual(labels.count("—"), 6)
        bars = [node for node in root.iter("{http://www.w3.org/2000/svg}rect")
                if node.get("height") == "12" and node.get("fill") in (BLUE, ORANGE)]
        self.assertEqual([float(node.get("width")) for node in bars], [21, 42])
        self.assertIn("50% smaller", labels)
        self.assertIn("Gutch vs", labels)
        disk = ET.fromstring(render_resources_svg([record], kind="disk"))
        disk_labels = [node.text for node in disk.iter("{http://www.w3.org/2000/svg}text")]
        self.assertIn("Peak disk by operation", disk_labels)
        self.assertEqual(disk_labels.count("—"), 8)
        self.assertEqual(root.attrib["viewBox"], disk.attrib["viewBox"])
        record["operation_resources"]["gutch"]["restore"] = {"peak_disk_bytes": 4194304}
        disk = ET.fromstring(render_resources_svg([record], kind="disk"))
        disk_labels = [node.text for node in disk.iter("{http://www.w3.org/2000/svg}text")]
        self.assertIn("4.0", disk_labels)
        self.assertEqual(disk_labels.count("—"), 7)

    def test_failed_resource_rows_do_not_display_successful_measurements(self):
        record = pair_record(status="ERROR")
        record["operation_resources"] = {"gutch": {"repair": {"peak_rss_bytes": 1048576}}}
        root = ET.fromstring(render_resources_svg([record], kind="ram"))
        labels = [node.text for node in root.iter("{http://www.w3.org/2000/svg}text")]
        self.assertNotIn("1.0", labels)
        self.assertEqual(labels.count("—"), 8)

    def test_main_chart_keeps_resources_in_separate_report_tables(self):
        chart = render_svg([pair_record()])
        self.assertIn("Stored size", chart)
        self.assertNotIn("Peak RAM", chart)
        self.assertNotIn("Peak disk", chart)

    def test_chart_references_match_readme_notes_and_survive_row_reordering(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for pair, title, number in (("borg", "Borg", 1), ("plakar", "Plakar", 2),
                                    ("kopia", "Kopia", 3), ("restic", "Restic", 4),
                                    ("rustic", "Rustic", 5), ("bpt", "BuildPatchTool", 6)):
            chart = render_svg([pair_record(pair)])
            self.assertIn(f"{title} [{number}]", chart)
            self.assertIn(f"{number}. **{title}:**", readme)

    def test_latest_selection_uses_numeric_run_order_and_keeps_bad_reports_visible(self):
        owner = ROOT / ".artifacts/tests"
        owner.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=owner) as temporary:
            reports = Path(temporary)
            for run, pair, value in (("9-1", "bpt", pair_record("bpt", "ERROR")),
                                     ("10-1", "bpt", pair_record("bpt")),
                                     ("11-1", "restic", pair_record())):
                path = reports / "2026-10-31" / run / f"{pair}.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value), encoding="utf-8")
            (reports / "2026-10-31/11-1/restic.json").write_text("broken JSON", encoding="utf-8")
            records = {record["pair"]: record for record in latest_records(reports)}
            self.assertEqual(records["bpt"]["status"], "PASS")
            self.assertIn("10-1", records["bpt"]["source_report"])
            self.assertEqual(records["restic"]["status"], "ERROR")
            self.assertEqual(records["borg"]["status"], "NOT_RUN")
