"""Explicit CI preparation and compact report publishing; never starts a benchmark."""

import argparse
import bz2
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil
from urllib.request import urlopen

import yaml

from comparison_benchmark_suite.datasets import extract_archive, prepare_dataset
from comparison_benchmark_suite.support.filesystem import file_sha256
from comparison_benchmark_suite.support.retention import remove_owned
from comparison_benchmark_suite.tools.report import COMPARISON_HEADERS, comparison_rows, relative_metric, measurement_details
from comparison_benchmark_suite.tools.chart import latest_records, render_svg


ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("src/comparison_benchmark_suite")
PAIRS = ("borg", "bpt", "kopia", "plakar", "restic", "rustic")
START = "<!-- latest-benchmarks:start -->"
END = "<!-- latest-benchmarks:end -->"


def selected_pairs(pair):
    if pair == "all":
        return list(PAIRS)
    if pair not in PAIRS:
        raise ValueError(f"Unknown pair: {pair}")
    return [pair]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def prepare_inputs(root=ROOT):
    recipe = root / SOURCE / "fixtures/blender/dataset.yaml"
    values = yaml.safe_load(recipe.read_text(encoding="utf-8"))
    return prepare_dataset(values, recipe, root / ".artifacts")


def install_tool(pair, root=ROOT):
    """Provision only the explicitly selected tool, checking archive AND executable."""
    tool = "buildpatchtool" if pair == "bpt" else pair
    manifest = json.loads((root / SOURCE / "resources/tools.json").read_text(encoding="utf-8"))
    record = next(item for item in manifest["executables"]
                  if item["platform"] == "linux-x64" and item["tool"] == tool)
    target = root / ".artifacts/tools" / record["path"]
    if target.is_file() and file_sha256(target) == record["sha256"]:
        return
    work = root / ".artifacts/provision" / tool
    work.mkdir(parents=True, exist_ok=True)
    archive = work / "download"
    with urlopen(record["source_url"], timeout=120) as response, archive.open("wb") as output:
        shutil.copyfileobj(response, output)
    if file_sha256(archive) != record["archive_sha256"]:
        raise ValueError(f"Archive checksum mismatch: {tool}")
    destination = root / ".artifacts/tools/linux-x64" / tool
    remove_owned(destination, root / ".artifacts/tools")
    target.parent.mkdir(parents=True, exist_ok=True)
    if tool == "borg":
        shutil.copyfile(archive, target)
    elif tool == "restic":
        with bz2.open(archive, "rb") as source, target.open("wb") as output:
            shutil.copyfileobj(source, output)
    else:
        extracted = work / "extract"
        remove_owned(extracted, work)
        extract_archive(archive, extracted)
        candidates = [path for path in extracted.rglob(target.name) if path.is_file()]
        if tool == "buildpatchtool":
            candidates = [path for path in candidates if path.parent.name == "Linux"]
        if len(candidates) != 1:
            raise ValueError(f"Expected one executable for {tool}, found {len(candidates)}")
        source = candidates[0]
        if tool == "buildpatchtool":
            shutil.copytree(source.parents[2], destination / "Engine", dirs_exist_ok=True)
        else:
            shutil.copytree(source.parent, target.parent, dirs_exist_ok=True)
    if file_sha256(target) != record["sha256"]:
        raise ValueError(f"Executable checksum mismatch: {tool}")
    target.chmod(0o755)
    remove_owned(work, root / ".artifacts")


def write_fixture(pair, repetitions, root=ROOT):
    if not 1 <= repetitions <= 10:
        raise ValueError("Repetitions must be between 1 and 10")
    document = yaml.safe_load((root / SOURCE / f"fixtures/gutch_vs_{pair}.yaml").read_text(encoding="utf-8"))
    document["dataset"] = str((root / SOURCE / "fixtures/blender/dataset.yaml").resolve())
    document["repetitions"] = repetitions
    document["description"] = document["description"].replace(
        "six rotating measured repetitions", f"{repetitions} rotating measured repetitions"
    )
    document["open_perfetto"] = False
    path = root / ".artifacts/ci/fixture.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def collect(pair, outcome, root=ROOT):
    """Copy evidence through an allowlist, never repositories or restored files."""
    destination = root / ".artifacts/export" / pair
    destination.mkdir(parents=True, exist_ok=True)
    runs = sorted((root / ".artifacts/runs").glob("*/run.json"))
    compact = {"pair": pair, "job_outcome": outcome, "rows": [], "status": "ERROR"}
    if runs:
        run = runs[-1].parent
        record = json.loads((run / "run.json").read_text(encoding="utf-8"))
        compact["run_status"] = record.get("status")
        compact["description"] = record.get("fixture", {}).get("description", "")
        compact["fixture"] = record.get("fixture", {})
        compact["dataset"] = record.get("dataset", {})
        compact["executables"] = record.get("executables", {})
        for name in ("run.json", "results.json", "summary.json", "summary.md", "trace.json", "resources.json"):
            if (run / name).is_file():
                shutil.copyfile(run / name, destination / name)
        if (run / "summary.json").is_file() and (run / "results.json").is_file():
            summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))
            results = json.loads((run / "results.json").read_text(encoding="utf-8"))
            compact["rows"] = comparison_rows(summary, results)
            compact["summary"] = summary
            compact["measurement_contract"] = 2
            resources = run / "resources.json"
            if resources.is_file():
                compact["resources"] = json.loads(resources.read_text(encoding="utf-8"))
            compact["operations"] = {item["metadata"]["case"]: item["metadata"].get("operations", {}) for item in results}
            compact["reasons"] = list(dict.fromkeys(item["metadata"]["reason"]
                                      for item in results if item["metadata"].get("reason")))
            if outcome == "success" and record.get("status") == "passed" and all(
                item["metadata"].get("status") == "PASS" for item in results
            ):
                compact["status"] = "PASS"
        # Detailed logs/traces remain Actions artifacts, never Git report content.
        for lane in (run / "lanes").glob("*"):
            for folder in ("commands", "stats", "traces"):
                if (lane / folder).is_dir():
                    shutil.copytree(lane / folder, destination / "lanes" / lane.name / folder)
    compact["provenance"] = {
        key: os.environ.get(key, "unknown") for key in
        ("GITHUB_SHA", "GUTCH_REVISION", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "RUNNER_OS", "ImageOS", "ImageVersion")
    }
    compact["host"] = {"platform": platform.platform(), "cpu_count": os.cpu_count(),
                       "disk_bytes": shutil.disk_usage(root).total}
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.is_file():
        compact["host"]["cpu_model"] = next((line.split(":", 1)[1].strip()
            for line in cpuinfo.read_text().splitlines() if line.startswith("model name")), "unknown")
    compact["tools"] = [record for record in json.loads((root / SOURCE / "resources/tools.json").read_text())["executables"]
                        if record["platform"] == "linux-x64" and record["tool"] == ("buildpatchtool" if pair == "bpt" else pair)]
    build = root / ".artifacts/build/provenance.json"
    if build.exists():
        compact["gutch_build"] = json.loads(build.read_text(encoding="utf-8"))
    write_json(destination / "compact.json", compact)
    # A setup error can prevent the runtime's finally block from being reached.
    for run in (root / ".artifacts/runs").glob("*"):
        remove_owned(run, root / ".artifacts")
    return compact


def pair_overview(record):
    """Render one pair; derive ratios from raw medians, never rounded cells."""
    pair = record["pair"]
    other = "buildpatchtool" if pair == "bpt" else pair
    title = "BuildPatchTool" if pair == "bpt" else pair.title()
    lines = [f"### Gutch vs {title} ({record['status']})", "",
             "| Tool | Status | Capture s | Restore s | Repair s | Stored MiB | Peak RAM MiB | Peak disk MiB |",
             "|---|---|---:|---:|---:|---:|---:|---:|"]
    rows = record["rows"] or [[label, "NOT_RUN", *("-" for _ in range(7))]
                              for label in ("gutch", other)]
    for row in rows:
        resources = []
        for metric in ("peak_rss_bytes", "peak_disk_bytes"):
            value = (record.get("summary", {}).get(row[0], {}).get(metric) or {}).get("median")
            resources.append("-" if value is None else f"{value / 1048576:.1f}")
        lines.append("| " + " | ".join([*(row[i] for i in (0, 1, 2, 3, 4, 6)), *resources]) + " |")
    ratios = [relative_metric(record, metric) for metric in ("backup", "restore", "repair", "repo_size", "peak_rss_bytes", "peak_disk_bytes")]
    lines.extend(["| **Gutch relative** | - | " + " | ".join(ratios) + " |", ""])
    if record.get("measurement_contract") == 2:
        lines.extend(measurement_details(record.get("summary", {})))
        for label, operations in record.get("operations", {}).items():
            unsupported = [f"{name}: {status}" for name, status in operations.items() if status.startswith("UNSUPPORTED")]
            if unsupported:
                lines.extend([label + ": " + "; ".join(unsupported), ""])
    return lines


def publish(pair, inputs, run_id, attempt, root=ROOT):
    # IDs are used in tracked paths and URLs; reject arbitrary path fragments.
    if not run_id.isdecimal() or not attempt.isdecimal():
        raise ValueError("Run ID and attempt must be numeric")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    relative = Path("reports") / stamp / f"{run_id}-{attempt}"
    destination = root / relative
    records = []
    for name in selected_pairs(pair):
        source = inputs / f"benchmark-{name}" / name / "compact.json"
        record = json.loads(source.read_text(encoding="utf-8")) if source.exists() else {
            "pair": name, "status": "ERROR", "rows": [], "reasons": ["Job produced no report; see Actions logs."]}
        records.append(record)
        write_json(destination / f"{name}.json", record)
    latest = latest_records(root / "reports")
    chart = render_svg(latest)
    for path in (destination / "comparison.svg", root / "reports/comparison.svg"):
        path.write_text(chart, encoding="utf-8", newline="\n")
    repository = os.environ.get("GITHUB_REPOSITORY", "icauro/Gutch-Benchmarks")
    url = f"https://github.com/{repository}/actions/runs/{run_id}"
    lines = ["# Linux benchmark results", "", f"Run: [{run_id}, attempt {attempt}]({url}) | UTC date: {stamp}", "",
             "Each pair has its own settings. Hosted-runner timings are indicative; OS cache state is uncontrolled.", ""]
    dates = sorted({item["source_report"].split("/")[0] for item in latest if item.get("source_report")})
    protocol_note = " · includes earlier measurement protocols" if any(item.get("measurement_contract") != 2 for item in latest) else " · measurement contract 2"
    overview = ["Latest per pair · Linux · Blender 5.0.0 → 5.1.0 · " + ", ".join(dates) + protocol_note, "",
                f"[This run's report]({relative.as_posix()}/README.md) · [Actions logs and artifacts]({url})", "",
                "Lower values are better. Pair settings differ; bars scale independently within each cell.",
                "Hosted-runner timings are indicative; OS caches are uncontrolled.", "",
                "<details>", "<summary>Detailed results and source reports</summary>", ""]
    for item in latest:
        if item.get("source_report"):
            overview.extend([f"[Source: Gutch vs {item['pair']}](reports/{item['source_report']})", ""])
        overview.extend(pair_overview(item))
    overview.extend(["</details>", ""])
    for record in records:
        name = record["pair"]
        provenance = record.get("provenance", {})
        lines.extend([f"## Gutch vs {name}: {record['status']}", "", record.get("description", ""), "",
                      f"Suite commit: `{provenance.get('GITHUB_SHA', 'unknown')}`; Gutch commit: `{provenance.get('GUTCH_REVISION', 'unknown')}`.", "",
                      f"Host: `{record.get('host', {})}`", "",
                      f"[Machine-readable report]({name}.json)", "",
                      "| " + " | ".join(COMPARISON_HEADERS) + " |", "|" + "---|" * len(COMPARISON_HEADERS)])
        lines.extend("| " + " | ".join(row) + " |" for row in record["rows"])
        if record.get("measurement_contract") == 2:
            lines.extend(["", *measurement_details(record.get("summary", {}))])
        lines.extend(["", *record.get("reasons", []), ""])
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    readme = root / "README.md"
    text = readme.read_text(encoding="utf-8")
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    readme.write_text(before + START + "\n" + "\n".join(overview) + "\n" + END + after, encoding="utf-8")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        Path(summary).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    matrix = commands.add_parser("matrix")
    matrix.add_argument("--pair", choices=("all", *PAIRS), required=True)
    commands.add_parser("dataset")
    install = commands.add_parser("tool")
    install.add_argument("--pair", choices=PAIRS, required=True)
    fixture = commands.add_parser("fixture")
    fixture.add_argument("--pair", choices=PAIRS, required=True)
    fixture.add_argument("--repetitions", type=int, required=True)
    export = commands.add_parser("collect")
    export.add_argument("--pair", choices=PAIRS, required=True)
    export.add_argument("--outcome", required=True)
    report = commands.add_parser("publish")
    report.add_argument("--pair", choices=("all", *PAIRS), required=True)
    report.add_argument("--inputs", type=Path, required=True)
    report.add_argument("--run-id", required=True)
    report.add_argument("--attempt", required=True)
    args = parser.parse_args()
    if args.command == "matrix":
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            output.write("pairs=" + json.dumps(selected_pairs(args.pair)) + "\n")
    elif args.command == "dataset":
        prepare_inputs()
    elif args.command == "tool":
        install_tool(args.pair)
    elif args.command == "fixture":
        write_fixture(args.pair, args.repetitions)
    elif args.command == "collect":
        collect(args.pair, args.outcome)
    elif args.command == "publish":
        publish(args.pair, args.inputs, args.run_id, args.attempt)


if __name__ == "__main__":
    main()
