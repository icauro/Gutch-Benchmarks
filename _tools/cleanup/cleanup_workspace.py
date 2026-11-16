"""Clean explicitly owned disposable output; never start or stop applications."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from storage_targets import cleanup_targets, remove_disposable_tree


def config(root):
    return json.loads((root / '_tools/workspace.json').read_text(encoding='utf-8'))


def verify_path(path, owner):
    if not path.is_relative_to(owner) or path == owner:
        raise ValueError(f'Target is outside its owner: {path}')
    current = path
    while current != owner:
        if current.is_symlink() or current.is_junction():
            raise ValueError(f'Refusing linked path: {current}')
        current = current.parent
    if path.resolve() != path:
        raise ValueError(f'Target resolves elsewhere: {path}')


def main(root, kind):
    parser = argparse.ArgumentParser(description=f'Clean {kind} in this workspace and declared children.')
    parser.add_argument('--current-only', action='store_true', help='Do not invoke child workspace cleanup.')
    parser.add_argument('--dry-run', action='store_true', help='List targets without deleting anything.')
    args = parser.parse_args()
    root = Path(root).resolve()
    failures = 0
    try:
        targets = cleanup_targets(root, kind, require_unity_closed=not args.dry_run)
    except (OSError, ValueError) as error:
        print(f'FAILED: {error}', file=sys.stderr, flush=True)
        return 1
    for target, target_owner in targets:
        try:
            verify_path(target, target_owner)
            if target.exists():
                if not target.is_dir():
                    raise ValueError(f'Expected directory: {target}')
                if args.dry_run:
                    print(f'Would remove: {target}', flush=True)
                else:
                    remove_disposable_tree(target, target_owner)
                    print(f'Removed: {target}', flush=True)
            else:
                print(f'Absent: {target}', flush=True)
        except (OSError, ValueError) as error:
            print(f'FAILED: {error}', file=sys.stderr, flush=True)
            failures += 1

    seen = {root}

    def visit(parent):
        nonlocal failures
        for relative in config(parent).get('children', []):
            try:
                child = Path(parent / relative).absolute()
                verify_path(child, parent)
                if child in seen:
                    raise ValueError(f'Duplicate child: {child}')
                seen.add(child)
                script = child / '_tools/cleanup' / ('cleanup_artifacts.py' if kind == '.artifacts' else 'cleanup_builds.py')
                verify_path(script, child)
                if not script.is_file():
                    raise ValueError(f'Missing child cleanup script: {script}')
                command = [sys.executable, str(script), '--current-only']
                if args.dry_run:
                    command.append('--dry-run')
                result = subprocess.run(command, check=False)
                if result.returncode:
                    failures += 1
                visit(child)
            except (OSError, ValueError) as error:
                print(f'FAILED: {error}', file=sys.stderr, flush=True)
                failures += 1

    if not args.current_only:
        try:
            visit(root)
        except (OSError, ValueError) as error:
            print(f'FAILED: {error}', file=sys.stderr, flush=True)
            failures += 1
    return 1 if failures else 0
