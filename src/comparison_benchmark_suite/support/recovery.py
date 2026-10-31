"""Shared reconstructed-output corruption used by benchmark lanes."""

import json
import os
import stat
import time
from pathlib import Path
from typing import Any

from comparison_benchmark_suite.support.filesystem import remove_tree


def build_corruption_plan(destination: Path, plan_path: Path, sequence: int, *, expected_inventory=None, preserve_mtime=False, add_extra=True) -> Path:
    # Select by canonical source inventory, never by a tool's restored metadata.
    from .filesystem import inventory
    entries = expected_inventory if expected_inventory is not None else inventory(destination)
    writable = sorted(name for name, item in entries.items()
                      if item["kind"] == "file" and not item["read_only"])
    non_empty = sorted((name for name in writable if entries[name]["bytes"] > 0),
                       key=lambda name: (entries[name]["bytes"], name))
    if not writable:
        raise RuntimeError(f"cannot corrupt reconstruction without writable files: {destination}")
    targets = list(dict.fromkeys(non_empty[:1] + non_empty[-1:]))
    operations = [{"kind": "flipByte", "path": name, "offset": entries[name]["bytes"] // 2,
                   "mask": 255, "preserve_mtime": preserve_mtime} for name in targets]
    delete_candidates = [name for name in writable if name not in targets]
    if delete_candidates:
        operations.append({"kind": "delete", "path": delete_candidates[0]})
    extra = destination / f".gutch-benchmark-extra-{sequence:03d}.bin"
    suffix = 1
    while extra.exists():
        extra = destination / f".gutch-benchmark-extra-{sequence:03d}-{suffix}.bin"
        suffix += 1
    if add_extra:
        operations.append({"kind": "addFile", "path": extra.relative_to(destination).as_posix(),
                           "content": list(f"gutch benchmark corruption {sequence}\n".encode())})
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps({"operations": operations}, indent=2), encoding="utf-8")
    return plan_path


def _safe_path(destination: Path, relative: str) -> Path:
    path = (destination / relative).resolve()
    try:
        path.relative_to(destination.resolve())
    except ValueError as error:
        raise ValueError(f"corruption path escapes destination: {relative}") from error
    return path


def apply_corruption_plan(destination: Path, plan_path: Path) -> None:
    document: Any = json.loads(plan_path.read_text(encoding="utf-8"))
    operations = document.get("operations") if isinstance(document, dict) else None
    if not isinstance(operations, list):
        raise ValueError(f"corruption plan has no operations: {plan_path}")
    for operation in operations:
        if not isinstance(operation, dict) or not isinstance(operation.get("path"), str):
            raise ValueError(f"invalid corruption operation in {plan_path}")
        path = _safe_path(destination, operation["path"])
        kind = operation.get("kind")
        if kind == "flipByte":
            previous = path.stat()
            offset = int(operation.get("offset", 0))
            if offset < 0 or offset >= previous.st_size:
                raise ValueError(f"corruption byte offset is outside file: {path}")
            with path.open("r+b") as stream:
                stream.seek(offset)
                value = stream.read(1)[0] ^ (int(operation.get("mask", 255)) & 255)
                stream.seek(offset)
                stream.write(bytes([value]))
            if operation.get("preserve_mtime", False):
                os.utime(path, ns=(previous.st_atime_ns, previous.st_mtime_ns))
        elif kind == "setReadOnly":
            mode = path.stat().st_mode
            if bool(operation.get("read_only", False)):
                path.chmod(mode & ~stat.S_IWRITE)
            else:
                path.chmod(mode | stat.S_IWRITE)
        elif kind == "delete":
            if path.is_dir():
                remove_tree(path)
            else:
                path.unlink()
        elif kind == "addFile":
            content = operation.get("content")
            if not isinstance(content, list) or not all(isinstance(value, int) for value in content):
                raise ValueError(f"invalid added-file content in {plan_path}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(bytes(content))
        else:
            raise ValueError(f"unknown corruption operation {kind!r}")


def validate_installation(dataset, output, evidence, operation):
    """One strict validation boundary shared by every native adapter."""
    from .filesystem import validate_output
    started = time.perf_counter()
    for source in dataset.sources:
        validate_output(source, output / source.name, evidence / f"validate-{operation}-{source.name}.json",
                        expected_inventory=dataset.inventories[source.name])
    return time.perf_counter() - started


def capture_metrics(snapshot_metrics):
    snapshots = list(snapshot_metrics.values())
    return {"initial_capture": snapshots[0]["backup"],
            "incremental_capture": sum(item["backup"] for item in snapshots[1:]),
            "repo_growth_bytes": sum(item["repo_growth_bytes"] for item in snapshots[1:])}


def recovery_checks(dataset, lane, output, repair, restore, *, delete_extra, hidden_damage=True):
    """Keep detection/repair, namespace cleanup and full restore distinct.

    Each successful case starts from validated content. Unsupported cases never
    mutate output or receive a timing; the harness never repairs on a tool's behalf.
    """
    metrics, operations = {}, {}
    for name in ("repair", "hidden_repair"):
        if name == "hidden_repair" and not hidden_damage:
            operations[name] = "UNSUPPORTED: native resume trusts size and mtime"
            continue
        started = time.perf_counter()
        for index, source in enumerate(reversed(dataset.sources), 1):
            destination = output / source.name
            plan = build_corruption_plan(destination, lane.stats / f"corruption-{name}-{index}.json", index,
                expected_inventory=dataset.inventories[source.name], preserve_mtime=name == "hidden_repair", add_extra=False)
            apply_corruption_plan(destination, plan)
        metrics["corrupt"] = metrics.get("corrupt", 0) + time.perf_counter() - started
        elapsed = repair(name)
        validation = validate_installation(dataset, output, lane.stats, name)
        metrics[name] = elapsed
        metrics[name + "_validated"] = elapsed + validation
        operations[name] = "PASS"
    if delete_extra:
        for index, source in enumerate(dataset.sources, 1):
            destination = output / source.name
            extra = destination / f".gutch-benchmark-extra-{index:03d}.bin"
            if extra.exists():
                raise ValueError("extra-file probe collides with dataset")
            extra.write_bytes(b"extra file cleanup probe")
        elapsed = repair("exact_recovery")
        validation = validate_installation(dataset, output, lane.stats, "exact_recovery")
        metrics.update(exact_recovery=elapsed, exact_recovery_validated=elapsed + validation)
        operations["exact_recovery"] = "PASS"
    else:
        operations["exact_recovery"] = "UNSUPPORTED: no native extra-file deletion in this adapter"
    remove_tree(output)
    elapsed = restore()
    validation = validate_installation(dataset, output, lane.stats, "full_restore_recovery")
    metrics.update(full_restore_recovery=elapsed, full_restore_recovery_validated=elapsed + validation)
    operations["full_restore_recovery"] = "PASS"
    return metrics, operations
