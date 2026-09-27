"""One benchmark schedule, outcome, and retention boundary."""
from dataclasses import asdict, replace
from pathlib import Path
import platform
import subprocess
import time
import statistics
from comparison_benchmark_suite.support.filesystem import file_sha256
from comparison_benchmark_suite.support.memory import process_utilization
from comparison_benchmark_suite.support.traces import combine_labeled_traces, open_trace_in_perfetto, write_lane_timeline


def execute_cases(fixture, layout, commands, execute, *, executable, keep_artifacts=False,
                  on_lane_complete=None, on_run_complete=None):
    results = []
    timelines = []
    failed_cases = []
    schedule = []
    for lane in fixture.lanes:
        if lane.warmup:
            schedule.append((lane, 0))
    measured = [lane for lane in fixture.lanes if not lane.warmup]
    if not measured:
        raise ValueError("fixture requires at least one measured case")
    for repetition in range(fixture.repetitions):
        # Rotate positions reproducibly instead of giving the same case first access every time.
        rotation = repetition % len(measured)
        schedule.extend((lane, repetition + 1) for lane in measured[rotation:] + measured[:rotation])
    try:
        revision = subprocess.run(['git', 'rev-parse', 'HEAD'], stdin=subprocess.DEVNULL, capture_output=True, text=True, check=False, cwd=Path(__file__).resolve().parents[1]).stdout.strip()
    except OSError:
        revision = None
    layout.write_manifest('running', schema_version=1, fixture=asdict(fixture),
        host={'platform': platform.platform(), 'python': platform.python_version()},
        source_revision=revision, binary_sha256=file_sha256(executable) if executable.is_file() else None,
        profile_mode=fixture.profile_mode, memory_profile=fixture.profile_mode == "detailed", cache_state='fresh_repository_os_cache_uncontrolled')
    try:
        for index, (specification, repetition) in enumerate(schedule):
            label = specification.label
            if specification.warmup: label += '-warmup'
            elif fixture.repetitions > 1: label += f'-sample-{repetition:03d}'
            case = replace(specification, label=label, configuration_label=specification.label)
            layout.write_manifest('running', current_case=label)
            commands.begin_lane()
            commands.evidence_directory = layout.lane(label).root / 'commands'
            measurement_start = len(commands.measurements)
            result = execute(case)
            result.metrics.update(process_utilization(commands.measurements[measurement_start:]))
            result.metadata["utilization_scope"] = "direct tool processes; CPU 100% = one logical core; excludes descendants and harness"
            if result.metadata.get('status') == 'ERROR':
                failed_cases.append(label)
            result.metadata.update(case=specification.label, repetition=repetition,
                warmup=specification.warmup, profile_mode=fixture.profile_mode, memory_profile=fixture.profile_mode == "detailed")
            if result.metadata.get('differences'):
                layout.write_results([item.as_json() for item in results] + [result.as_json()])
                raise RuntimeError(f"{label} produced incorrect output")
            layout.write_json(layout.lane(label).root / 'result.json', result.as_json())
            if not specification.warmup:
                results.append(result)
                timeline = layout.lane(label).traces / "timeline.json"
                write_lane_timeline(label, commands.measurements[measurement_start:], result.traces, timeline)
                timelines.append((label, timeline))
                layout.write_results([item.as_json() for item in results])
                if on_lane_complete: on_lane_complete(result)
            if index + 1 < len(schedule) and fixture.lane_wait_seconds:
                time.sleep(fixture.lane_wait_seconds)
        combine_labeled_traces(timelines, layout.root / 'trace.json')
        summary = {}
        for case in measured:
            samples = [result for result in results if result.metadata['case'] == case.label]
            metrics = {}
            for name in sorted(set.intersection(*(set(sample.metrics) for sample in samples))):
                values = [sample.metrics[name] for sample in samples if sample.metrics[name] is not None]
                if not values:
                    metrics[name] = None
                    continue
                metrics[name] = {'samples': len(values), 'median': statistics.median(values),
                    'minimum': min(values), 'maximum': max(values)}
            summary[case.label] = metrics
        layout.write_json(layout.root / 'summary.json', summary)
        if on_run_complete: on_run_complete(results)
        if failed_cases:
            layout.write_manifest('failed', current_case=None, cleanup_complete=False, failed_cases=failed_cases)
            return results
        layout.write_manifest('passed', current_case=None, cleanup_complete=False)
        layout.finish(keep=keep_artifacts or not fixture.delete_artifacts)
    except BaseException as error:
        layout.write_manifest('cancelled' if isinstance(error, KeyboardInterrupt) else 'failed', error=str(error))
        raise
    print(f"Wrote benchmark results: {layout.root / 'results.json'}")
    if fixture.open_perfetto:
        open_trace_in_perfetto(layout.root / 'trace.json', print)
    return results
