# Line-count reporting

This read-only tool uses `repositories.json` paths relative to its owning workspace,
not the current directory. `--commit` counts the latest committed tree against its
first parent; a first commit starts at an empty tree. Default mode counts the
working tree against HEAD, including new non-ignored source files.

Use `--repo <name>` for a configured repository, `--files <relative paths...>` for
task scope, and `--json` for structured output. Multiple repositories require an
explicit `--repo` when using `--files`. Renames retain content deltas attributed to
the destination module. Comments and blank physical lines count. Generated,
third-party, binary, cached and disposable outputs are excluded.

Gitless workspaces report maintained-source totals with deltas explicitly
unavailable; --commit cannot invent a baseline. Configuration/fixture boundaries
and category exclusions are declared in the tool; adjust them only for the owning
project. No global Git configuration is modified.
