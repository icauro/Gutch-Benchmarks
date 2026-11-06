# Development overview

Public setup and commands are in `README.md` at the repository root. Product
contracts are in `_docs/`. Maintained scripts are in `_tools/`; test inputs remain
in `tests/`. No parent workspace or sibling repository is needed at runtime.

Temporary test output belongs in `.artifacts/tests/`, measurements in
`.artifacts/benchmarks/`, tool output in `.artifacts/tools/`, and experiments in
`.artifacts/scratch/`. Build output belongs in `.builds/`.
