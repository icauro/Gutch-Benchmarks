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

## Comparison settings

The Blender fixture explicitly targets **1 MiB chunks** and **Zstd level 3 or
its closest standard preset** where the tool exposes those controls. This is
an approximate alignment, not equal compression work or identical chunk boundaries.
The settings below belong to `fixtures/blender/fixture.yaml`; custom fixtures
choose their own settings. Recorded fixture settings and command logs accompany
every run. Earlier results using tool defaults are not directly comparable.

| Tool | Compression selected | Chunking selected | Controls and remaining differences |
|---|---|---|---|
| Gutch | Zstd, level 3 | `chunk_1MiB`: FastCDC, 256 KiB minimum / 1 MiB target / 4 MiB maximum | Numeric compression level and chunk profiles are selectable. Default 8 MiB bundles remain enabled. |
| Restic | `--compression auto`: Zstd standard preset | Rabin, 512 KiB minimum / roughly 1 MiB target / 8 MiB maximum | CLI exposes named compression modes, not a numeric Zstd level or chunk-size setting. `auto` is an approximate level-3 counterpart, not an identical encoder. |
| Kopia | `--compression=zstd`: standard preset | `--splitter=DYNAMIC-1M-BUZHASH`: 512 KiB minimum / 1 MiB target / 2 MiB maximum | Named codec/presets and splitter profiles are selectable; no numeric Zstd level in this policy. |
| Borg | `--compression zstd,3` | `--chunker-params fastcdc,19,23,20,2`: 512 KiB minimum / 1 MiB target / 8 MiB maximum | Borg 2 only. Retains native FastCDC and normalization level 2; only the target size changes. Borg 1 is rejected. |
| Plakar | LZ4, tool-managed level | Default FastCDC: 512 KiB minimum / 1 MiB target / 8 MiB maximum | Tested 1.1.5 CLI exposes compression on/off, but no codec, level, or chunk-size selector. Retained as a documented exception; no claim of Zstd-equivalent effort. |
| BuildPatchTool | Tool-managed compression; codec/level not selected | `-ChunkWindowSize=1048576` (1 MiB) | Tested 1.8.8 local-generation help exposes a chunk window, but no compression codec/level control. Its window is not a CDC average. Local restore and restore-over-existing are independently validated. |
| Filesystem | None | None | Copy baseline; no deduplication or compression. |

Chunk targets are nominal parameters, not measured means. File boundaries,
minimum/maximum sizes, hashes, compression libraries and skip heuristics still
change the resulting chunks and compression cost. Worker counts remain tool
defaults; Restic and Kopia retain encryption, while Gutch, Borg and Plakar lanes
use unencrypted storage. Packing, metadata and verification costs also differ.
Interpret results as complete tool workflows, not isolated codec benchmarks.

Settings were checked against the installed CLIs on 2026-09-27 and upstream
[Kopia compressors](https://github.com/kopia/kopia/blob/v0.23.1/repo/compression/compressor_zstd.go),
[Kopia splitters](https://github.com/kopia/kopia/blob/v0.23.1/repo/splitter/splitter_buzhash32.go),
[Restic chunker](https://github.com/restic/chunker/blob/master/chunker.go),
[Restic compression](https://github.com/restic/restic/blob/master/internal/repository/repository.go),
[Borg chunker parameters](https://borgbackup.readthedocs.io/en/stable/usage/notes.html),
and [Plakar chunking](https://github.com/PlakarKorp/kloset/blob/v1.1.5/chunking/chunking.go).
Recheck the table when changing tool versions or fixture arguments.

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

The command prints an ASCII comparison table with status, median capture/restore
and repair/recovery seconds, stored MiB, CPU usage, and peak RSS MiB. Missing measurements show `-`;
failure and capability reasons appear below the table. It also prints the report
path under `.artifacts/runs/`. Each run contains:

- `summary.md`: readable outcomes.
- `summary.json`: per-candidate medians and ranges.
- `results.json`: measured samples, operation semantics, and validation outcomes.
- `run.json`: fixture, input provenance, executable hashes, and environment.
- `trace.json`: all measured tools together in Perfetto, including command durations and filesystem copies.
- `lanes/`: command logs, validation records, and optional diagnostic traces.

Correct outputs are checked before corruption/repair, then checked again after
recovery. Corruption plans are deterministic and saved. Tool recovery preserves
the damaged installation and is reported as `Repair`; the filesystem baseline
still deletes and recopies output, reported as `Recovery`. Restore-over-existing
does not imply that a tool reuses healthy bytes. Update, rollback,
and no-op restore are marked `NOT_RUN` in this initial fixture; they are not
silently approximated by clean restore. Compression settings and verification
work differ between tools, so this is an end-to-end workflow comparison.

Successful runs remove mutable repository/output payloads and retain evidence.
Failed runs retain their payloads and command evidence; other candidates continue.
The command exits nonzero if a measured candidate fails. The newest 20 unpinned
successful reports are retained. Plakar uses a short OS temporary socket/cache
path where needed; successful cleanup removes that run-owned path too.

Open `trace.json` in Perfetto, or set `open_perfetto: true` in the fixture to
open it after the run. The shared overview works with `profile_mode: off`.
Each tool/repetition starts at zero on a **Compacted tool time** track.
Operations appear back-to-back with their measured durations preserved; this
is not an elapsed run clock and rows do not imply concurrent execution.
Warm-ups are excluded. Operation spans use wall-clock duration and
include setup/probes as well as capture, restore, checking and recovery commands.
Trace timestamps and durations share integer-microsecond precision to prevent
rounding overlaps; raw benchmark measurements retain their original precision.
Harness validation, preparation, cleanup and waits between operations are omitted
from the timeline. Raw command timestamps and performance metrics are unchanged.

Set `profile_mode: detailed` in the fixture only for Gutch internal tracing and
sampled process memory. Engine spans are approximately aligned to their command
start; process startup is not synchronized with the engine clock. External tools
provide operation spans, not internal worker traces. Its measurement overhead makes it a separate comparison
from the default `off` mode. The existing runtime modules also serve Gutch's
optional developer diagnostics; the simple command does not require those tools.

## Native recovery and extra files

Recovery changes bytes, leaves permissions unchanged, deletes a writable file
when possible, and adds
an unexpected file. The installation is retained for the tool to repair. The
harness does not chmod damaged files or remove extras on the tool's behalf.

| Tool | Recovery command options | Extra files and tested Windows outcome |
|---|---|---|
| Gutch | Existing installation repair | Existing native repair path; independent validation remains required. |
| Restic | `restore --overwrite always --delete --verify` | Native extra deletion. Real small-fixture and Blender recovery passed. Individual restores retain `--include <build>` to protect other builds. |
| Kopia | `snapshot restore --delete-extra` | Native extra deletion requested. Installed 0.23.1 failed replacing a read-only damaged file; atomic writes also failed in a separate probe. |
| Borg | `extract --continue` (Borg 2 only) | No native extra deletion option. Installed Windows Borg 2 failed on the read-only file. Resume skips based on metadata, so it is not a content-integrity guarantee. |
| Plakar | `restore` into the existing destination | No native extra deletion option established. Installed 1.1.5 left an extra file and a content mismatch in the probe. |
| BuildPatchTool | `InstallManifest -PrevManifest=...` | No native extra deletion option advertised. Installed 1.8.8 left the unexpected file. |

The outcomes above are from the earlier probe that also changed read-only
attributes. Current corruption plans no longer change permissions; those results
need a new run before comparison. They are not claims
about every platform. Recovery errors retain successful capture/restore metrics,
mark the run `ERROR`, omit a successful repair timing, and preserve evidence.
No full-rebuild fallback masks a native recovery failure. Independent validation
requires every expected entry, matching content and supported metadata. Extra
files are allowed and recorded in each validation JSON's `extra_files` list;
they do not fail a run. Native deletion flags remain enabled where available.
The older probe outcomes in the table used strict extra-file validation and do
not describe the current pass criterion.

## BuildPatchTool

Download the executable from [Epic](https://launcher-public-service-prod06.ol.epicgames.com/launcher/api/installer/download/BuildPatchTool.zip),
extract it with its accompanying Engine files, and set `executables.buildpatchtool`.
The adapter probes `-mode=ChunkBuildDirectory -help` and
runs only the supported local generation interface. Epic Store upload-only
interfaces are reported as `UNSUPPORTED`; no upload or authentication is attempted.
Each build gets an explicit manifest in a shared cloud directory. The adapter
restores each build with `InstallManifest` into a fresh destination, then checks
its contents against the frozen source inventory. With `corrupt_repair: true`,
it applies the same corruption plan as the other tools and calls `InstallManifest`
with `PrevManifest` against the damaged output. It does not delete the installation.
Only independently validated runs receive `PASS`. BPT 1.8.8 has no advertised
extra-file deletion option: in the tested fixture, content was repaired but the
extra file remained. Current validation records that extra without failing.
Update, rollback and no-op restore remain `NOT_RUN`, as in the other lanes.
BPT must preserve the fixture's files and supported metadata; unsupported content
such as an unpreserved empty directory fails validation rather than being silently
recreated by the harness. No publishing credentials are needed.

Run the suite's own tests with:

```text
python -m unittest discover -s tests
```

CPU and memory columns require `profile_mode: detailed`; otherwise they show `-`.
CPU is the observed CPU-time delta divided by observed sampling time, weighted
across all tool commands (including setup and verification). 100% means one
logical core; parallel execution may exceed 100%. Very short commands may have
no CPU samples. Peak RSS is the largest sampled resident-memory value across
commands. Repeated runs report medians of these per-run values. Sampling can miss
short peaks and process exit tails. Only the launched process is measured, not
its children or helpers. The in-process filesystem baseline is intentionally `-`.

Plakar backup uses its default cache policy; the suite no longer passes `-cache no`.
Caches remain isolated per lane. Earlier Borg Buzhash / cache-disabled Plakar
measurements should not be mixed with these settings.

Borg version validation runs once during runner preflight, before scheduled lanes.
Its command is excluded from benchmark timings, utilization and Perfetto tracks.
