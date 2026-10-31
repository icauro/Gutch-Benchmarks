"""Owned artifact deletion and bounded retention for the standalone suite."""
import json
import os
from pathlib import Path
import shutil
import stat


def remove_owned(path: Path, owner: Path) -> None:
    owner = owner.resolve()
    if path.is_symlink() or path.is_junction():
        if not path.parent.resolve().is_relative_to(owner):
            raise ValueError(f"cleanup link escapes its owner: {path}")
        path.rmdir() if path.is_junction() else path.unlink()
        return
    target = path.resolve()
    if target == owner or not target.is_relative_to(owner):
        raise ValueError(f"cleanup target is not a child of its owner: {path}")
    if not target.exists():
        return
    if target.is_file():
        target.chmod(target.stat().st_mode | stat.S_IWUSR)
        target.unlink()
        return
    for directory, directories, files in os.walk(target, followlinks=False):
        directories[:] = [name for name in directories
                          if not (Path(directory) / name).is_symlink() and not (Path(directory) / name).is_junction()]
        for name in directories + files:
            child = Path(directory) / name
            try:
                metadata = child.lstat()
            except FileNotFoundError:
                # A tool's helper process can remove its socket while exiting.
                continue
            # Windows Unix sockets are reparse points that cannot be chmod'ed.
            # Leave links and special files to rmtree's non-following deletion.
            if (not getattr(metadata, "st_reparse_tag", 0) and
                    (stat.S_ISREG(metadata.st_mode) or stat.S_ISDIR(metadata.st_mode))):
                child.chmod(metadata.st_mode | stat.S_IWUSR | stat.S_IXUSR)
    target.chmod(target.stat().st_mode | stat.S_IWUSR | stat.S_IXUSR)
    shutil.rmtree(target)


def compact_success(root: Path, *, keep=False, reports=("run.json", "summary.md")) -> None:
    """Called by the owning supervisor only after all workers/services have stopped."""
    if keep:
        return
    for child in root.iterdir():
        if child.name not in reports:
            remove_owned(child, root)


def prune_successful_runs(parent: Path, *, retain=20) -> list[Path]:
    """Only finalized managed successes are eligible; failures and pinned runs survive."""
    eligible = []
    for path in parent.glob("*/run.json"):
        if path.parent.is_symlink() or path.parent.is_junction():
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if (record.get("status") == "passed" and record.get("cleanup_complete") is True
                and not record.get("keep_artifacts", False)):
            eligible.append(path.parent)
    eligible.sort(key=lambda path: (path.stat().st_mtime_ns, path.name), reverse=True)
    removed = []
    for path in eligible[retain:]:
        remove_owned(path, parent)
        removed.append(path)
    return removed
