# Developer guide

Setup and commands are in the [README](../README.md). Development steps, tests
and tool updates are under
[maintaining the suite](../_docs/guide.md#maintaining-the-suite). Run every
command from the repository root; no parent workspace or sibling repository is
needed.

| Folder | Holds |
| --- | --- |
| `_dev_guide/` | This guide: how to work on the suite |
| `_docs/` | The benchmark guide, tool notes, notices and published reports |
| `_tools/` | Maintained developer scripts |
| `src/` | The benchmark suite package |
| `tests/` | Unit tests |
| `.artifacts/` | Generated output: tests in `tests/`, measurements in `benchmarks/`, tool output in `tools/`, experiments in `scratch/` |
| `.builds/` | Build output |

## Cleanup

`.artifacts/` and `.builds/` are ignored and fully disposable, including pinned
or failed runs; copy evidence you need later elsewhere before cleaning. Pinning
controls automatic run retention only, not this explicit cleanup.

Run `python _tools/cleanup/cleanup_artifacts.py --dry-run` or
`python _tools/cleanup/cleanup_builds.py --dry-run` to inspect targets. Remove
`--dry-run` to delete them. Default behavior includes declared children;
`--current-only` stays at this folder. Cleanup never stops applications.
The Python build backend may create ignored `build/` and `src/*.egg-info/`
metadata; cleanup leaves them alone.
