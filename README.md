# Comparison benchmark suite

Compare storage tools using the same builds and independent SHA-256 checks.
This folder works on its own: copy it anywhere. It does not need the Gutch
repository, Rust, Docker, or cloud credentials.

## Run

Install Python 3.12 or newer, then run these commands in this folder:

```text
python -m pip install -r requirements.txt
python run.py
```

The default fixture downloads two pinned Blender releases for Windows x64 or
Linux x64. Downloads and extracted builds are cached in `.artifacts/`.
The fixture runs one warm-up and three measured repetitions, rotating tool order.
Preparation and independent output validation are outside tool-command timings.
OS cache state is uncontrolled; these are not cold-cache measurements.

The filesystem-copy baseline works without another executable. Other tools must
be on PATH, or configured in `fixtures/blender/fixture.yaml`:

```yaml
executables:
  gutch: C:/tools/gutch-cli.exe
  restic: C:/tools/restic.exe
  buildpatchtool: C:/tools/BuildPatchTool.exe
```

Missing tools are clearly reported as `UNAVAILABLE`; available tools still run.
Paths in a fixture are relative to that fixture's folder. No tool is downloaded
or built automatically. To compare two Gutch binaries, give their lanes distinct
labels and put each executable under its label in `executables`.

## Use your own builds

Create `fixtures/my_product/fixture.yaml` and put your builds beside it:

```text
fixtures/my_product/
  fixture.yaml
  build_001/
  build_002/
```

Use this small fixture:

```yaml
name: my_product
builds:
  - path: build_001
  - path: build_002
repetitions: 3
warmups: 1
lane_wait_seconds: 0
step_wait_seconds: 0
corrupt_repair: true
executables:
  gutch: gutch-cli
lanes:
  - label: filesystem
    tool: filesystem
  - label: gutch
    tool: gutch
```

```text
python run.py --fixture my_product
```

You can also pass a fixture directory or YAML path. List at least two builds,
oldest first. Their directory names do not determine ordering. Inputs are copied
into an owned cache and independently inventoried; originals are not mutated.
The cache is checked before reuse. Custom local builds also work on platforms
without a built-in Blender download.

## Results

The command prints the report path under `.artifacts/runs/`. Each run contains:

- `summary.md`: readable outcomes.
- `summary.json`: per-candidate medians and ranges.
- `results.json`: measured samples, operation semantics, and validation outcomes.
- `run.json`: fixture, input provenance, executable hashes, and environment.
- `lanes/`: command logs, validation records, and optional diagnostic traces.

Correct outputs are checked before corruption/repair, then checked again after
recovery. Corruption plans are deterministic and saved. Gutch in-place repair
and external full-restore recovery have separate metric names. Update, rollback,
and no-op restore are marked `NOT_RUN` in this initial fixture; they are not
silently approximated by clean restore. Compression settings and verification
work differ between tools, so this is an end-to-end workflow comparison.

Successful runs remove mutable repository/output payloads and retain evidence.
Failed runs retain their payloads and command evidence; other candidates continue.
The command exits nonzero if a measured candidate fails. The newest 20 unpinned
successful reports are retained. Plakar uses a short OS temporary socket/cache
path where needed; successful cleanup removes that run-owned path too.

Set `profile_mode: detailed` in the fixture only for diagnostic tracing and
sampled process memory. Its measurement overhead makes it a separate comparison
from the default `off` mode. The existing runtime modules also serve Gutch's
optional developer diagnostics; the simple command does not require those tools.

## BuildPatchTool

Supply your own executable. The adapter probes `-mode=PatchGeneration -help` and
runs only the supported local generation interface. Epic Store upload-only
interfaces are reported as `UNSUPPORTED`; no upload or authentication is attempted.
Successful local generation is `CAPTURE_ONLY`, not validated restore. This
adapter does not implement installation, update, or repair, and never claims
that a successful generation exit code establishes restored-content correctness.

Run the suite's own tests with:

```text
python -m unittest discover -s tests
```
