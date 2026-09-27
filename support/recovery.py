"""Shared reconstructed-output corruption used by benchmark lanes."""

import json
from pathlib import Path
import stat
from typing import Any

from comparison_benchmark_suite.support.filesystem import remove_tree


def build_corruption_plan(destination: Path, plan_path: Path, sequence: int) -> Path:
    files = sorted(
        (path for path in destination.rglob("*") if path.is_file() and not path.is_symlink()),
        key=lambda path: path.as_posix(),
    )
    if not files:
        raise RuntimeError(f"cannot corrupt empty reconstruction: {destination}")
    writable = [path for path in files if path.stat().st_mode & stat.S_IWRITE]
    non_empty = [path for path in writable if path.stat().st_size > 0]
    flip_target = non_empty[0] if non_empty else None
    permission_target = non_empty[0] if non_empty else (writable[0] if writable else files[0])
    operations: list[dict[str, object]] = []
    if flip_target:
        operations.append(
            {
                "kind": "flipByte",
                "path": flip_target.relative_to(destination).as_posix(),
                "offset": 0,
                "mask": 255,
            }
        )
    operations.append(
        {
            "kind": "setReadOnly",
            "path": permission_target.relative_to(destination).as_posix(),
            "read_only": bool(permission_target.stat().st_mode & stat.S_IWRITE),
        }
    )
    delete_candidates = [path for path in writable if path not in {flip_target, permission_target}]
    if delete_candidates:
        operations.append({"kind": "delete", "path": delete_candidates[0].relative_to(destination).as_posix()})
    extra = destination / f".gutch-benchmark-extra-{sequence:03d}.bin"
    suffix = 1
    while extra.exists():
        extra = destination / f".gutch-benchmark-extra-{sequence:03d}-{suffix}.bin"
        suffix += 1
    operations.append(
        {
            "kind": "addFile",
            "path": extra.relative_to(destination).as_posix(),
            "content": list(f"gutch benchmark corruption {sequence}\n".encode("utf-8")),
        }
    )
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
            data = bytearray(path.read_bytes())
            offset = int(operation.get("offset", 0))
            if offset < 0 or offset >= len(data):
                raise ValueError(f"corruption byte offset is outside file: {path}")
            data[offset] ^= int(operation.get("mask", 255)) & 255
            path.write_bytes(data)
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
