"""Validated fixture loading for Gutch."""

import math
from pathlib import Path
from typing import Any

from comparison_benchmark_suite.scheduling.config import ScenarioCatalog, load_scenario
from comparison_benchmark_suite.support.artifacts import safe_component
from comparison_benchmark_suite.tools.models import FixtureSpec, GutchProfile, LaneSpec


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures"
CHUNK_PROFILES = {
    "chunk_512B", "chunk_2KiB", "chunk_8KiB", "chunk_2MiB", "chunk_4MiB",
    "chunk_1KiB",
    "chunk_4KiB",
    "chunk_16KiB",
    "chunk_32KiB",
    "chunk_64KiB",
    "chunk_128KiB",
    "chunk_256KiB",
    "chunk_512KiB",
    "chunk_1MiB",
}
BUNDLE_PROFILES = {
    "bundle_4MiB",
    "bundle_8MiB",
    "bundle_16MiB",
    "bundle_32MiB",
    "bundle_64MiB",
    "bundle_128MiB",
}
COMPRESSION_ALGORITHMS = {"none", "zstd", "lz4"}
COMPRESSION_LEVEL_RANGES = {"zstd": (1, 22), "lz4": (0, 9), "none": None}
STORAGE_MODES = {"bundled", "loose_chunks"}
DEFAULT_WAIT_SECONDS = 4.0


def _bool(values: dict[str, Any], key: str, default: bool) -> bool:
    value = values.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def _lane_arguments(values: dict[str, Any], name: str, kind: str) -> tuple[str, ...]:
    raw = values.get("arguments", [])
    if raw is None:
        raw = []
    if not isinstance(raw, list) or any(not isinstance(argument, str) or not argument for argument in raw):
        raise ValueError(f"{name} arguments must be a list of non-empty strings")
    if raw and not kind.startswith(("restic-", "kopia-", "borg-", "plakar-")):
        raise ValueError(f"{name} arguments are only supported for external lanes")
    return tuple(raw)


def _wait_seconds(values: dict[str, Any], key: str) -> float:
    value = values.get(key, DEFAULT_WAIT_SECONDS)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a non-negative number of seconds")
    if not math.isfinite(float(value)) or value < 0:
        raise ValueError(f"{key} must be a non-negative number of seconds")
    return float(value)


def _snapshot_limit(values: dict[str, Any], path: Path) -> int | None:
    value = values.get("snapshot_limit")
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"snapshot_limit must be a positive integer: {path}")
    return value


def _profile(values: dict[str, Any], name: str) -> GutchProfile:
    legacy_fields = {
        "chunk_profile",
        "bundle_profile",
        "compression_profile",
        "storage_mode",
    } & values.keys()
    if legacy_fields:
        fields = ", ".join(sorted(legacy_fields))
        raise ValueError(f"{name} uses unsupported legacy profile fields: {fields}")
    raw = values.get("profile")
    if isinstance(raw, str):
        if raw != "default":
            raise ValueError(f"unknown {name} profile {raw!r}")
        raw = {}
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError(f"{name} profile must be a mapping")
    unknown_fields = set(raw) - {"chunk", "bundle", "compression", "storage", "jobs"}
    if unknown_fields:
        fields = ", ".join(sorted(unknown_fields))
        raise ValueError(f"{name} profile contains unsupported fields: {fields}")
    chunk = raw.get("chunk", "chunk_128KiB")
    bundle = raw.get("bundle", "bundle_8MiB")
    compression = raw.get("compression", {})
    storage = raw.get("storage", "bundled")
    if chunk not in CHUNK_PROFILES or bundle not in BUNDLE_PROFILES:
        raise ValueError(f"invalid Gutch chunk or bundle profile for {name}")
    if not isinstance(compression, dict):
        raise ValueError(f"{name} compression must be a mapping")
    compression_algorithm = compression.get("algorithm", "zstd")
    compression_level = compression.get(
        "level", 3 if compression_algorithm == "zstd" else None
    )
    if compression_algorithm not in COMPRESSION_ALGORITHMS or storage not in STORAGE_MODES:
        raise ValueError(f"invalid Gutch compression or storage mode for {name}")
    if compression_level is not None and (
        isinstance(compression_level, bool) or not isinstance(compression_level, int)
    ):
        raise ValueError(f"{name} compression level must be an integer or null")
    if compression_level is not None:
        level_range = COMPRESSION_LEVEL_RANGES[compression_algorithm]
        if level_range is None:
            raise ValueError(f"{name} compression algorithm {compression_algorithm} does not accept a level")
        minimum, maximum = level_range
        if not minimum <= compression_level <= maximum:
            raise ValueError(
                f"{name} {compression_algorithm} compression level must be between {minimum} and {maximum}"
            )
    jobs = raw.get("jobs")
    if jobs is not None and (isinstance(jobs, bool) or not isinstance(jobs, int) or jobs < 1):
        raise ValueError("profile jobs must be a positive integer")
    return GutchProfile(
        name,
        chunk,
        bundle,
        compression_algorithm,
        compression_level,
        storage,
        jobs,
    )


def load_fixture(path: Path) -> FixtureSpec:
    document = load_scenario(path)
    values = document.values
    lanes_value = values.get("lanes", [])
    if isinstance(lanes_value, dict):
        lanes_value = [dict(lane, label=label) for label, lane in lanes_value.items()]
    if not isinstance(lanes_value, list) or not lanes_value:
        raise ValueError(f"fixture must define at least one lane: {path}")
    lanes: list[LaneSpec] = []
    labels: set[str] = set()
    for raw in lanes_value:
        if not isinstance(raw, dict):
            raise ValueError(f"fixture lane must be a mapping: {path}")
        lane_phase_options = {
            key
            for key in ("verify_reconstruct", "corrupt_reconstruct", "repair_reconstruct", "corrupt_repair")
            if key in raw
        }
        if lane_phase_options:
            names = ", ".join(sorted(lane_phase_options))
            raise ValueError(f"{names} must be configured at fixture level, not per lane: {path}")
        label = raw.get("label")
        tool = raw.get("tool", "gutch")
        workload = raw.get("workload", "copy" if tool == "filesystem" else "individual")
        kind = "filesystem-copy" if tool == "filesystem" else f"{tool}-{workload}"
        if tool == "filesystem" and workload != "copy":
            raise ValueError("filesystem cases only support the copy workload")
        if "kind" in raw:
            raise ValueError(f"{path}: lane {label!r}: configure tool and workload separately instead of kind")
        if not isinstance(label, str) or not label.strip() or label in labels:
            raise ValueError(f"fixture lane labels must be unique non-empty strings: {path}")
        if not isinstance(kind, str):
            raise ValueError(f"fixture lane kind must be a string: {path}")
        normalized_label = safe_component(label)
        if normalized_label in labels:
            raise ValueError(f"lane labels collide as artifact names: {label}")
        labels.add(normalized_label)
        if kind not in {"gutch-individual", "gutch-batch", "gutch-product-bulk", "filesystem-copy", "buildpatchtool-individual",
                       *(f"{tool}-{mode}" for tool in ("restic", "kopia", "borg", "plakar") for mode in ("individual", "exact-bulk"))}:
            raise ValueError(f"unsupported lane kind: {kind}")
        if tool != "gutch" and "profile" in raw:
            raise ValueError("Gutch profiles only apply to Gutch cases")
        arguments = _lane_arguments(raw, label, kind)
        lanes.append(
            LaneSpec(
                label=label,
                tool=tool,
                workload=workload,
                profile=_profile(raw, label) if tool == "gutch" else None,
                warmup=_bool(raw, "warmup", False),
                arguments=arguments,
            )
        )
    repetitions = values.get("repetitions", 1)
    if isinstance(repetitions, bool) or not isinstance(repetitions, int) or repetitions < 1:
        raise ValueError("repetitions must be a positive integer")
    mode = values.get("profile_mode", "off")
    if mode not in {"off", "summary", "detailed"}:
        raise ValueError("profile_mode must be off, summary, or detailed")
    if all(lane.warmup for lane in lanes):
        raise ValueError("fixture must contain a measured lane")
    if "memory_profile" in values or "measurement_mode" in values:
        raise ValueError("use profile_mode: off, summary, or detailed")
    return FixtureSpec(
        name=document.name,
        runner=str(values.get("runner", "gutch-fixture")),
        description=str(values.get("description", "")),
        delete_artifacts=_bool(values, "delete_artifacts", True),
        open_perfetto=_bool(values, "open_perfetto", False),
        lanes=tuple(lanes),
        source_path=path,
        corrupt_repair=_bool(values, "corrupt_repair", False),
        lane_wait_seconds=_wait_seconds(values, "lane_wait_seconds"),
        step_wait_seconds=_wait_seconds(values, "step_wait_seconds"),
        snapshot_limit=_snapshot_limit(values, path),
        repetitions=repetitions,
        profile_mode=mode,
    )


class FixtureCatalog:
    def __init__(self, root: Path = FIXTURE_ROOT):
        self.root = root

    def list(self) -> list[FixtureSpec]:
        return [
            load_fixture(document.source_path)
            for document in ScenarioCatalog(self.root).list()
            if document.values.get("runner", "gutch-fixture") == "gutch-fixture"
        ]

    def resolve(self, name: str) -> FixtureSpec:
        document = ScenarioCatalog(self.root).resolve(name)
        if document.values.get("runner", "gutch-fixture") != "gutch-fixture":
            raise ValueError(f"fixture {name!r} is not a local Gutch fixture")
        return load_fixture(document.source_path)
