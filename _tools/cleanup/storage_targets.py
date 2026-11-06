"""Resolve explicitly configured disposable targets, including native Unity cache."""
import json
import os
from pathlib import Path
import stat


def verify_target(path, owner):
    if not path.is_relative_to(owner) or path == owner:
        raise ValueError(f'Target leaves its owner: {path}')
    current = path
    while True:
        try:
            info = current.lstat()
        except FileNotFoundError:
            info = None
        if info is not None and (stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400):
            raise ValueError(f'Refusing linked/reparse target path: {current}')
        if current == owner:
            break
        current = current.parent
    if path.resolve() != path:
        raise ValueError(f'Target resolves elsewhere: {path}')


def unity_project_root(owner, config):
    relative = config.get('unity_project')
    if relative is None:
        return None
    if relative not in ('.', '..'):
        raise ValueError('Unity project must be this workspace or its direct parent')
    project = Path(os.path.abspath(owner / relative))
    if project.is_symlink() or project.is_junction() or project.resolve() != project:
        raise ValueError(f'Refusing linked Unity project: {project}')
    if not (project / 'ProjectSettings/ProjectVersion.txt').is_file() or not (project / 'Assets').is_dir():
        raise ValueError(f'Configured Unity project lacks its source/settings markers: {project}')
    return project


def ensure_unity_closed():
    if os.name != 'nt':
        return
    import csv
    import subprocess
    result = subprocess.run(['tasklist.exe', '/FI', 'IMAGENAME eq Unity.exe', '/FO', 'CSV', '/NH'],
                            capture_output=True, text=True, encoding='mbcs', errors='replace',
                            creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        raise ValueError('Cannot verify that Unity is closed; Library cleanup was not started')
    if any(row and row[0].casefold() == 'unity.exe' for row in csv.reader(result.stdout.splitlines())):
        raise ValueError('Close Unity Editor before cleaning Library; no application was stopped')


def cleanup_targets(owner, kind, require_unity_closed=False):
    if kind not in ('.artifacts', '.builds'):
        raise ValueError(f'Unknown disposable output kind: {kind}')
    config = json.loads((owner / '_tools/workspace.json').read_text(encoding='utf-8-sig'))
    targets = [(owner / kind, owner)]
    project = unity_project_root(owner, config)
    if kind == '.builds' and project is not None:
        targets.append((project / 'Library', project))
        if require_unity_closed:
            ensure_unity_closed()
    if kind == '.builds':
        native = configured_native_build_targets(owner, config)
        protect_tracked_native_files(owner, native)
        targets.extend((path, owner) for path in native)
    for path, target_owner in targets:
        verify_target(path, target_owner)
    return targets


def remove_disposable_tree(target, owner):
    """Remove one verified target; retry only Windows read-only unlink/rmdir failures."""
    import shutil
    verify_target(target, owner)

    def retry_readonly(function, filename, error):
        path = Path(filename)
        if os.name != 'nt' or not isinstance(error, PermissionError) or function not in (os.unlink, os.remove, os.rmdir):
            raise error
        if path != target and not path.is_relative_to(target):
            raise ValueError(f'Read-only retry leaves the approved target: {path}')
        verify_target(path, owner)
        info = path.lstat()
        if not getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_READONLY:
            raise error
        os.chmod(path, info.st_mode | stat.S_IWRITE)
        function(path)

    shutil.rmtree(target, onexc=retry_readonly)


def configured_native_build_targets(owner, config):
    values = config.get('native_build_targets', [])
    if not isinstance(values, list):
        raise ValueError('Native build targets must be a list')
    result = []
    protected = {'.git', 'Assets', 'Packages', 'ProjectSettings', '_docs', '_dev_guide', 'research', 'reference', 'references'}
    for value in values:
        relative = Path(value)
        if relative.is_absolute() or not relative.parts or '..' in relative.parts or protected.intersection(relative.parts):
            raise ValueError(f'Invalid native build output: {value}')
        if not ({'bin', 'obj'}.intersection(relative.parts) or relative.name in {'artifacts', 'build'}):
            raise ValueError(f'Native target is not a recognized build-output location: {value}')
        path = owner / relative
        verify_target(path, owner)
        if any(path == previous or path.is_relative_to(previous) or previous.is_relative_to(path) for previous in result):
            raise ValueError(f'Duplicate/overlapping native build target: {path}')
        if any(path == owner / item or path.is_relative_to(owner / item) for item in ('.builds', '.artifacts')):
            raise ValueError(f'Native target duplicates standard disposable output: {path}')
        if path.exists() and not path.is_dir():
            raise ValueError(f'Native build target must be a directory: {path}')
        result.append(path)
    return result


def protect_tracked_native_files(owner, targets):
    import subprocess
    repositories = {}
    for target in targets:
        current = target
        while current.is_relative_to(owner):
            if (current / '.git').exists():
                repositories.setdefault(current, []).append(target)
                break
            if current == owner:
                break
            current = current.parent
    for repository, paths in repositories.items():
        command = ['git', '--no-optional-locks', '-c', f'safe.directory={repository.as_posix()}', '-C', str(repository),
                   'ls-files', '-z', '--', *[path.relative_to(repository).as_posix() for path in paths]]
        result = subprocess.run(command, capture_output=True)
        if result.returncode:
            raise ValueError(f'Cannot verify native output Git ownership: {repository}')
        for value in result.stdout.split(b'\0'):
            if value:
                file = repository / value.decode('utf-8', 'surrogateescape')
                if file.exists() or file.is_symlink():
                    raise ValueError(f'Refusing native cleanup containing a tracked file: {file}')
