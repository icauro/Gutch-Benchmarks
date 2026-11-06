# Folders and cleanup

`_dev_guide/` holds development guidance, `_docs/` retained explanations and
findings, and `_tools/` maintained scripts. `.artifacts/` and `.builds/` are always
ignored and fully disposable, including pinned or failed runs. Promote evidence
needed later to retained storage before cleanup; pinning controls automatic run
retention, not the explicit full cleanup command.

Run `python _tools/cleanup/cleanup_artifacts.py --dry-run` or
`python _tools/cleanup/cleanup_builds.py --dry-run` to inspect targets. Remove
`--dry-run` to delete them. Default behavior includes declared children;
`--current-only` stays at this workspace. Cleanup never stops applications.

The Python build backend may create native `build/` and `src/*.egg-info/` metadata. These ignored ecosystem paths are outside the explicit disposable cleanup targets.
