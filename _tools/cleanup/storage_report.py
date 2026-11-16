"""Workspace-local disposable storage reporting with child-process delegation."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from storage_targets import unity_project_root, configured_native_build_targets

KINDS = {'artifacts': '.artifacts', 'builds': '.builds'}


def checked(owner, relative):
    relative = Path(relative)
    if relative.is_absolute() or not relative.parts or '..' in relative.parts:
        raise ValueError(f'Expected a relative owned path: {relative}')
    current = owner
    for part in relative.parts:
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError(f'Refusing linked/reparse path: {current}')
    if not current.resolve().is_relative_to(owner.resolve()):
        raise ValueError(f'Path leaves its owner: {current}')
    return current


def scan_storage(owner, excluded, kinds, container_only, unity_library=False, native_build_paths=()):
    targets = {kind: {'kind': kind, 'path': str(owner / KINDS[kind]), 'bytes': 0,
                      'files': 0, 'status': 'absent', 'issues': []} for kind in kinds}
    if unity_library:
        targets['unity_library'] = {'kind': 'builds', 'label': 'Unity Library', 'path': str(owner / 'Library'), 'bytes': 0, 'files': 0, 'status': 'absent', 'issues': []}
    native_buckets = {}
    for index, path in enumerate(native_build_paths):
        key = f'native_build_{index}'
        targets[key] = {'kind': 'builds', 'label': 'Native build output', 'path': str(path), 'bytes': 0,
                        'files': 0, 'status': 'absent', 'issues': []}
        native_buckets[os.path.normcase(str(path))] = key
    issues = []
    total = 0
    owner_text = str(owner)
    excluded_text = {os.path.normcase(str(path)) for path in excluded}
    buckets = {KINDS[kind]: kind for kind in kinds}
    if unity_library:
        buckets['Library'] = 'unity_library'
    pending = [(owner_text, None)]
    container_folders = {'_tools', '_dev_guide', '.artifacts', '.builds'}

    def problem(path, bucket, message):
        issues.append(message)
        if bucket is not None:
            targets[bucket]['issues'].append(message)
            targets[bucket]['status'] = 'incomplete'

    while pending:
        directory, inherited_bucket = pending.pop()
        at_root = directory == owner_text
        try:
            info = os.lstat(directory)
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                problem(directory, inherited_bucket, f'Skipped linked/reparse directory: {directory}')
                continue
            with os.scandir(directory) as entries:
                for entry in entries:
                    bucket = buckets.get(entry.name) if at_root else inherited_bucket
                    if native_buckets:
                        bucket = native_buckets.get(os.path.normcase(entry.path), bucket)
                    try:
                        if excluded_text and os.path.normcase(entry.path) in excluded_text:
                            continue
                        info = entry.stat(follow_symlinks=False)
                        mode = info.st_mode
                        if container_only and at_root and entry.name not in container_folders and stat.S_ISDIR(mode):
                            continue
                        if stat.S_ISLNK(mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                            problem(entry.path, bucket, f'Skipped linked/reparse entry: {entry.path}')
                        elif stat.S_ISDIR(mode):
                            if bucket is not None:
                                targets[bucket]['status'] = 'incomplete' if targets[bucket]['issues'] else 'present'
                            pending.append((entry.path, bucket))
                        elif stat.S_ISREG(mode):
                            total += info.st_size
                            if bucket is not None:
                                if at_root:
                                    problem(entry.path, bucket, f'Expected a disposable directory: {entry.path}')
                                else:
                                    targets[bucket]['bytes'] += info.st_size
                                    targets[bucket]['files'] += 1
                    except OSError as error:
                        problem(entry.path, bucket, f'{entry.path}: {error}')
        except OSError as error:
            problem(directory, inherited_bucket, f'{directory}: {error}')
    return list(targets.values()), total, issues


def collect(owner, children, kind, current_only, container_only=False, storage_root=None, jobs=8, child_current_only=False, progress=False, unity_project=None, native_build_paths=()):
    if not 1 <= jobs <= 32:
        raise ValueError('Report worker budget must be between 1 and 32')
    kinds = list(KINDS) if kind == 'all' else [kind]
    declared = []
    declaration_issues = []
    for relative in children:
        try:
            if set(Path(relative).parts) & set(KINDS.values()):
                raise ValueError(f'Child workspace inside disposable output: {relative}')
            child = checked(owner, relative)
            if any(child == previous or child.is_relative_to(previous) or previous.is_relative_to(child) for previous in declared):
                raise ValueError(f'Duplicate or overlapping child workspace: {relative}')
            declared.append(child)
        except (OSError, ValueError, TypeError) as error:
            declaration_issues.append(str(error))
    targets, workspace_bytes, storage_issues = scan_storage(owner, set(declared), kinds, container_only, unity_library=unity_project == owner and 'builds' in kinds, native_build_paths=native_build_paths if 'builds' in kinds else ())
    if storage_root is not None and storage_root != owner:
        if storage_root != owner.parent or storage_root.is_symlink() or storage_root.is_junction():
            raise ValueError('An extended storage root must be the direct, unlinked parent workspace')
        # Rend keeps maintenance ownership in _development, while assets live beside it.
        additional_targets, additional_bytes, additional_issues = scan_storage(storage_root, {owner}, [], False, unity_library=unity_project == storage_root and 'builds' in kinds)
        targets.extend(additional_targets)
        workspace_bytes += additional_bytes
        storage_issues.extend(additional_issues)
    report = {'root': str(owner), 'own_bytes': sum(item['bytes'] for item in targets),
              'own_workspace_bytes': workspace_bytes, 'targets': targets,
              'children': [], 'issues': declaration_issues + storage_issues,
              'complete': not declaration_issues and not storage_issues}
    def child_report(child, child_jobs):
        script = checked(child, '_tools/cleanup/report_deletable_storage.py')
        if not script.is_file():
            raise ValueError(f'Missing child report script: {script}')
        command = [sys.executable, str(script), '--json', '--no-pause', '--kind', kind,
                   '--jobs', str(child_jobs)]
        if child_current_only:
            command.append('--current-only')
        result = subprocess.run(command, cwd=child, capture_output=True, text=True,
                                encoding='utf-8', errors='replace')
        if result.returncode not in (0, 1):
            raise ValueError(f'Child report failed ({result.returncode}): {child}: {result.stderr.strip()}')
        try:
            payload = json.loads(result.stdout)
        except ValueError as error:
            raise ValueError(f'Invalid child report from {child}: {result.stderr.strip() or str(error)}') from error
        if Path(payload['root']) != child or not isinstance(payload['total_bytes'], int) or payload['total_bytes'] < 0 or not isinstance(payload['workspace_bytes'], int):
            raise ValueError(f'Unexpected child report identity/totals: {child}')
        if result.returncode:
            payload['complete'] = False
        return payload

    if not current_only and declared:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        # Divide the worker budget between branches instead of multiplying it at every level.
        workers = min(4, len(declared), jobs)
        child_jobs = max(1, jobs // workers)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(child_report, child, child_jobs): child for child in declared}
            completed = 0
            for future in as_completed(futures):
                child = futures[future]
                try:
                    payload = future.result()
                    report['children'].append(payload)
                    if not payload['complete']:
                        report['complete'] = False
                except (OSError, ValueError, KeyError, TypeError) as error:
                    report['issues'].append(str(error))
                    report['complete'] = False
                completed += 1
                if progress:
                    print(f'[{completed}/{len(declared)}] Finished {child.relative_to(owner)}', flush=True)
        report['children'].sort(key=lambda item: item['root'].casefold())
    report['total_bytes'] = report['own_bytes'] + sum(child['total_bytes'] for child in report['children'])
    report['workspace_bytes'] = report['own_workspace_bytes'] + sum(child['workspace_bytes'] for child in report['children'])
    report['workspace_owners'] = 1 + sum(child['workspace_owners'] for child in report['children'])
    return report


def human_size(size):
    value = float(size)
    for unit in ('B', 'KiB', 'MiB', 'GiB', 'TiB'):
        if value < 1024 or unit == 'TiB':
            return f'{value:.1f} {unit}'
        value /= 1024


def table_rows(report, label=None):
    state = 'ok' if report['complete'] else 'INCOMPLETE'
    yield [label or Path(report['root']).name, human_size(report['workspace_bytes']), human_size(report['total_bytes']), state]
    children = sorted(report['children'], key=lambda item: item['workspace_bytes'], reverse=True)
    for index, child in enumerate(children):
        last = index == len(children) - 1
        name = Path(child['root']).relative_to(Path(report['root'])).as_posix()
        rows = list(table_rows(child, name))
        yield [('`- ' if last else '+- ') + rows[0][0], *rows[0][1:]]
        for row in rows[1:]:
            yield [('   ' if last else '|  ') + row[0], *row[1:]]


def display(report):
    rows = [['Workspace', 'Total size', 'Cleanable', 'Status'], *table_rows(report)]
    widths = [max(len(row[index]) for row in rows) for index in range(4)]
    border = '+' + '+'.join('-' * (width + 2) for width in widths) + '+'
    print(border)
    for index, row in enumerate(rows):
        cells = [value.rjust(widths[column]) if column in (1, 2) else value.ljust(widths[column]) for column, value in enumerate(row)]
        print('| ' + ' | '.join(cells) + ' |')
        if index == 0:
            print(border)
    print(border)


def all_issues(report):
    yield from report['issues']
    for child in report['children']:
        yield from all_issues(child)


def print_report(report, structured):
    if structured:
        print(json.dumps(report, indent=2, ensure_ascii=True))
    else:
        for issue in all_issues(report):
            print('INCOMPLETE: ' + issue)
        print(f'Total size: {human_size(report["workspace_bytes"])}; cleanable: {human_size(report["total_bytes"])}.')
        print('Each row includes its children; do not add parent and child rows together.')
        print('Logical file sizes; physical disk space recovered may differ.')
        if 'scan_seconds' in report:
            print(f"Scan completed in {report['scan_seconds']:.1f} seconds.")
        display(report)
    return 0 if report['complete'] else 1


def local_main(owner):
    parser = argparse.ArgumentParser(description='Report this workspace and cascade to its declared children.')
    parser.add_argument('--jobs', type=int, default=8, help='Parallel scan budget, 1 to 32')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--no-pause', action='store_true')
    parser.add_argument('--current-only', action='store_true')
    parser.add_argument('--kind', choices=('all', 'artifacts', 'builds'), default='all')
    args = parser.parse_args()
    config = json.loads(checked(owner, '_tools/workspace.json').read_text(encoding='utf-8-sig'))
    children = config.get('children', [])
    if not isinstance(children, list):
        raise ValueError('Workspace children must be a list')
    storage_root = None
    if 'storage_root' in config:
        relative = Path(config['storage_root'])
        if relative.is_absolute():
            raise ValueError('Storage root must be relative to this workspace')
        storage_root = Path(os.path.abspath(owner / relative))
    project = unity_project_root(owner, config)
    native_paths = configured_native_build_targets(owner, config)
    return print_report(collect(owner, children, args.kind, args.current_only, storage_root=storage_root, jobs=args.jobs, progress=not args.json, unity_project=project, native_build_paths=native_paths), args.json)


def pause_before_exit():
    if '--no-pause' not in sys.argv and sys.stdin is not None and sys.stdin.isatty():
        try:
            input('\nPress Enter to close...')
        except (EOFError, OSError, KeyboardInterrupt):
            pass
