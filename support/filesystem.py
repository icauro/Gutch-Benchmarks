"""Filesystem measurements and deterministic directory comparisons."""

from dataclasses import dataclass
import hashlib
from pathlib import Path
import shutil
import os
import stat
import json


@dataclass(frozen=True)
class TreeStats:
    file_count: int
    total_bytes: int
    largest_file_bytes: int


def scan_tree(root: Path) -> TreeStats:
    file_count = 0
    total_bytes = 0
    largest_file_bytes = 0
    for path in root.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        size = path.stat().st_size
        file_count += 1
        total_bytes += size
        largest_file_bytes = max(largest_file_bytes, size)
    return TreeStats(file_count, total_bytes, largest_file_bytes)


def remove_tree(path: Path) -> None:
    if path.is_symlink():
        path.unlink()
        return
    if not path.exists():
        return

    def make_writable(function, target, _error):
        target_path = Path(target)
        target_path.chmod(0o700)
        function(target)

    for child in path.rglob("*"):
        if child.is_symlink():
            continue
        try:
            child.chmod(0o700)
        except OSError:
            pass
    try:
        path.chmod(0o700)
    except OSError:
        pass
    shutil.rmtree(path, onerror=make_writable)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inventory(root: Path) -> dict[str, dict]:
    if not root.is_dir():
        raise FileNotFoundError(f"dataset directory does not exist: {root}")
    entries = {}
    def fail(error):
        raise error
    for directory, directories, files in os.walk(root, followlinks=False, onerror=fail):
        for name in sorted(directories + files):
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            mode = path.lstat().st_mode
            if path.is_symlink():
                entries[relative] = {"kind": "symlink", "target": os.readlink(path)}
            elif stat.S_ISDIR(mode):
                entries[relative] = {"kind": "directory"}
            elif stat.S_ISREG(mode):
                entries[relative] = {"kind": "file", "bytes": path.stat().st_size,
                    "sha256": file_sha256(path), "read_only": not bool(mode & stat.S_IWUSR),
                    "executable": bool(mode & 0o111) if os.name != "nt" else False}
            else:
                raise ValueError(f"unsupported dataset entry: {relative}")
    return dict(sorted(entries.items()))


def compare_inventory(expected: dict, actual: Path) -> list[str]:
    if not actual.is_dir():
        return ["missing output directory"]
    observed = inventory(actual)
    differences = [f"missing: {path}" for path in sorted(expected.keys() - observed.keys())]
    differences.extend(f"unexpected: {path}" for path in sorted(observed.keys() - expected.keys()))
    differences.extend(f"different: {path}" for path in sorted(expected.keys() & observed.keys())
                       if expected[path] != observed[path])
    return differences


def compare_directories(expected: Path, actual: Path) -> list[str]:
    return compare_inventory(inventory(expected), actual)


def validate_output(expected: Path, actual: Path, evidence: Path, *, expected_inventory: dict | None = None) -> None:
    differences = compare_inventory(expected_inventory if expected_inventory is not None else inventory(expected), actual)
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps({"status": "failed" if differences else "passed",
        "differences": differences}, indent=2) + "\n", encoding="utf-8")
    if differences:
        raise RuntimeError(f"output validation failed; see {evidence}: {differences[:5]}")
