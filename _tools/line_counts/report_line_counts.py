"""Read-only physical line totals and Git deltas for explicitly owned repositories."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import subprocess
import sys

OWNER = Path(__file__).resolve().parents[2]
SKIP = {'.git', '.artifacts', '.builds', '.cache', '.tools', '.venv', 'node_modules',
        'Library', 'Temp', 'Logs', 'UserSettings', 'bin', 'obj', 'Bin', 'Obj',
        'target', 'dist', 'build', 'build-vs', 'build-window-ui', '__pycache__',
        'third_party', 'third-party', 'external', 'external_tools', 'references',
        'vendor', 'Plugins', 'ThirdParty', 'External', 'retained_evidence', 'retained_outputs', 'reconstruction', 'profiles'}
EXTENSIONS = {'.md', '.mdx', '.txt', '.py', '.cs', '.c', '.cpp', '.h', '.hpp', '.rs',
              '.js', '.mjs', '.ts', '.tsx', '.jsx', '.kt', '.kts', '.java', '.go',
              '.hlsl', '.shader', '.compute', '.slang', '.glsl', '.vert', '.frag',
              '.sh', '.ps1', '.bat', '.cmd', '.cmake', '.toml', '.yaml', '.yml',
              '.json', '.xml', '.props', '.targets', '.html', '.css'}
SPECIAL = {'CMakeLists.txt', '.gitignore', '.editorconfig', '.clang-format', '.csharpierignore'}


def git(root, *arguments, required=True):
    result = subprocess.run(['git', '--no-optional-locks', '-c', f'safe.directory={root.as_posix()}',
                             '-C', str(root), *arguments], capture_output=True)
    if required and result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8', 'replace').strip())
    return result


def eligible(path, scope):
    name = path.as_posix()
    if any(part in SKIP for part in path.parts):
        return False
    if path.name.endswith(('.g.cs', '.generated.cs', '.g.slang', '.g.h', '.min.js')):
        return False
    if path.suffix.lower() not in EXTENSIONS and path.name not in SPECIAL:
        return False
    return not scope or any(name == item or name.startswith(item.rstrip('/') + '/') for item in scope)


def physical_lines(payload):
    if b'\0' in payload:
        return None
    return payload.count(b'\n') + int(bool(payload) and not payload.endswith(b'\n'))


def identity(path):
    parts = path.parts
    bucket = 'documentation' if path.suffix.lower() in {'.md', '.mdx', '.txt'} else (
        'tests' if any(part.lower() in {'tests', 'test', 'fixtures'} for part in parts) else 'code_and_configuration')
    if len(parts) > 2 and parts[0] in {'modules', 'packages', 'crates'}:
        module = '/'.join(parts[:2])
    elif len(parts) > 3 and parts[:2] == ('Assets', 'Ica.Rend'):
        module = '/'.join(parts[:3])
    else:
        module = parts[0] if len(parts) > 1 else '(root)'
    return module, bucket


def diff_entries(payload):
    fields = payload.split(b'\0')
    index = 0
    while index < len(fields):
        field = fields[index]
        index += 1
        if not field:
            continue
        added, removed, name = field.split(b'\t', 2)
        if not name:
            # With -z, rename records contain old and new names as following fields.
            index += 1  # Old name; content delta is attributed to the destination.
            name = fields[index]
            index += 1
        if added == b'-' or removed == b'-':
            continue
        yield Path(name.decode('utf-8', 'surrogateescape')), int(added), int(removed)


def measure(spec, commit, scope):
    root = (OWNER / spec['path']).resolve()
    has_git = (root / '.git').exists()
    head = git(root, 'rev-parse', '--verify', 'HEAD', required=False).returncode == 0 if has_git else False
    if commit and not head:
        raise RuntimeError(f'{spec["name"]}: --commit needs an existing Git commit')
    rows = defaultdict(lambda: {'total': 0, 'added': 0, 'removed': 0})
    def add(path, key, count):
        rows[identity(path)][key] += count
    if has_git:
        command = ('ls-tree', '-r', '--name-only', '-z', 'HEAD') if commit else ('ls-files', '-z')
        names = git(root, *command).stdout.split(b'\0')
        untracked = [] if commit else git(root, 'ls-files', '--others', '--exclude-standard', '-z').stdout.split(b'\0')
        for raw in sorted(set(names + untracked)):
            if not raw:
                continue
            path = Path(raw.decode('utf-8', 'surrogateescape'))
            if not eligible(path, scope):
                continue
            if commit:
                payload = git(root, 'show', 'HEAD:' + path.as_posix()).stdout
            else:
                file = root / path
                if not file.exists():
                    continue
                if file.is_symlink() or not file.resolve().is_relative_to(root):
                    raise RuntimeError(f'Refusing a source path outside its declared owner: {file}')
                payload = file.read_bytes()
            count = physical_lines(payload)
            if count is not None:
                add(path, 'total', count)
                if not commit and (not head or raw in untracked):
                    add(path, 'added', count)
        if commit:
            parent = git(root, 'rev-parse', '--verify', 'HEAD^', required=False)
            if parent.returncode == 0:
                delta = git(root, 'diff', '-M', '--numstat', '-z', 'HEAD^', 'HEAD').stdout
            else:
                delta = git(root, 'diff-tree', '--root', '--no-commit-id', '-r', '-M', '--numstat', '-z', 'HEAD').stdout
        elif head:
            delta = git(root, 'diff', '-M', '--numstat', '-z', 'HEAD').stdout
        else:
            delta = b''
        for path, added, removed in diff_entries(delta):
            if eligible(path, scope):
                add(path, 'added', added)
                add(path, 'removed', removed)
    else:
        # A Gitless workspace can provide totals, but has no trustworthy delta baseline.
        import os
        included = spec.get('include', ['src', 'crates', 'ui', 'native', 'extension', 'tests',
                                        '_tools', '_dev_guide', '_docs', 'AGENTS.md', 'README.md'])
        for prefix in included:
            start = root / prefix
            candidates = [start] if start.is_file() else []
            if start.is_dir():
                for base, directories, files in os.walk(start, followlinks=False):
                    directories[:] = [name for name in directories if name not in SKIP and not (Path(base)/name).is_symlink()]
                    candidates.extend(Path(base)/name for name in files)
            for file in candidates:
                if file.is_symlink() or not file.resolve().is_relative_to(root):
                    continue
                path = file.relative_to(root)
                if eligible(path, scope):
                    count = physical_lines(file.read_bytes())
                    if count is not None:
                        add(path, 'total', count)
    result = []
    for (module, bucket), values in sorted(rows.items()):
        result.append({'repository': spec['name'], 'module': module, 'category': bucket,
                       'total': values['total'], 'added': values['added'] if has_git else None,
                       'removed': values['removed'] if has_git else None,
                       'net': values['added'] - values['removed'] if has_git else None})
    return {'name': spec['name'], 'path': str(root), 'baseline': 'latest commit' if commit else ('HEAD' if head else 'empty tree' if has_git else None),
            'delta_available': has_git, 'rows': result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit', action='store_true')
    parser.add_argument('--files', nargs='+', default=[])
    parser.add_argument('--repo', help='Select one configured repository by name')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    specs = json.loads(Path(__file__).with_name('repositories.json').read_text(encoding='utf-8'))['repositories']
    if args.repo:
        specs = [item for item in specs if item['name'] == args.repo]
    if not specs:
        raise RuntimeError('No repository matches the requested scope')
    if args.files and len(specs) != 1:
        raise RuntimeError('--files needs --repo when multiple repositories are configured')
    scope = []
    for name in args.files:
        path = Path(name)
        if path.is_absolute() or '..' in path.parts:
            raise RuntimeError('--files paths must be relative to the selected repository')
        scope.append(path.as_posix())
    reports = [measure(item, args.commit, scope) for item in specs]
    if args.json:
        print(json.dumps({'reports': reports}, indent=2))
    else:
        for report in reports:
            print(f"{report['name']}: baseline={report['baseline'] or 'unavailable (no Git)'}")
            print('module | category | total | added | removed | net')
            totals = defaultdict(lambda: {'total': 0, 'added': 0, 'removed': 0})
            for row in report['rows']:
                print(' | '.join(str(row[key]) if row[key] is not None else 'unavailable'
                                 for key in ('module', 'category', 'total', 'added', 'removed', 'net')))
                for key in ('total', 'added', 'removed'):
                    totals[row['category']][key] += row[key] or 0
            for category, values in sorted(totals.items()):
                delta = f"+{values['added']} / -{values['removed']} / net {values['added']-values['removed']:+}" if report['delta_available'] else 'delta unavailable (no Git baseline)'
                print(f"TOTAL {category}: {values['total']} lines; {delta}")
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print(f'Line counting failed: {error}', file=sys.stderr)
        raise SystemExit(2)
