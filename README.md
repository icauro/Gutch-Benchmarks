# Comparison benchmark suite

Original project code is [MIT licensed](LICENSE). External tools, workloads and
dependencies retain their own terms; see [third-party notices](THIRD_PARTY_NOTICES.md).

Compare storage tools using the same builds and independent SHA-256 checks.
This root project works on its own: copy it anywhere, with any folder name. It does not need the Gutch
repository, Rust, Docker, or cloud credentials.

## Run

Install Python 3.12 or newer, then run these commands in this folder:

```text
python -m pip install -r requirements.txt
python run.py
```

The command opens an interactive terminal screen. Hover or focus a fixture to
read its description, then choose **Run fixture**. Arrow keys or Tab navigate;
Enter activates a button. Mouse hover requires a terminal with mouse support.
The running view shows elapsed time, the current operation, a live log and
completed measured cases; preparation and warm-ups do not claim a completion
percentage. **Stop run** (or Ctrl+C) stops the owned process tree and retains
partial evidence. Afterward, the summary stays open with **Run another**,
**Open Perfetto**, **Show run log**, and **Quit** actions.

For scripts and noninteractive terminals, select a fixture explicitly:

```text
python run.py --fixture gutch_vs_rustic
```

The `--fixture` form runs once and exits. `--no-open-perfetto` suppresses automatic
browser opening; the interactive screen uses this and opens Perfetto only when
requested. Install updated requirements to get the Textual terminal dependency.

The pairwise fixtures read the same local 5.0.0 and 5.1.0 Windows x64 builds from
`fixtures/blender/builds/`; the suite does not download inputs. Both host platforms
benchmark these same files as data. Local build folders stay outside Git history;
include them when copying or distributing the ready-to-run suite folder.
Each fixture runs one warm-up and three measured repetitions, rotating tool order.
Preparation and independent output validation are outside tool-command timings.
OS cache state is uncontrolled; these are not cold-cache measurements.

Comparison executables are supplied locally. Install tools on PATH, set their
paths in the fixture, or place them in the ignored `bin/windows-x64/` or
`bin/linux-x64/` folders. Executables and vendor runtime distributions are not
tracked. The suite never downloads tools automatically. For example:

```yaml
executables:
  gutch: C:/tools/gutch-cli.exe
  restic: C:/tools/restic.exe
  buildpatchtool: C:/tools/BuildPatchTool.exe
```

Local tools are discovered automatically under `bin/windows-x64/`
or `bin/linux-x64/`, before searching PATH. Each tool has its own
folder: `restic/restic.exe` on Windows or `restic/restic` on Linux, likewise for
Borg, Rustic, Kopia and Plakar. Gutch uses `gutch/gutch-cli.exe` or `gutch/gutch-cli`.
BuildPatchTool keeps its Engine layout under `buildpatchtool/Engine/Binaries/`,
with `Win64/BuildPatchTool.exe` or `Linux/BuildPatchTool`. Preserve its accompanying
Engine files. Explicit fixture paths and `GUTCH_EXECUTABLE` still take precedence.
Only x86-64 hosts use these platform folders. Check the system requirements of
the binaries you install. The recorded Linux Borg 2.0.0b25 asset requires
glibc 2.39 or newer. Download archives and smoke-test logs belong under
`.artifacts/`. Refresh your local Gutch executable after rebuilding it; the suite
never reads a sibling project's build directory.

Missing tools are clearly reported as `UNAVAILABLE`; available tools still run.
Paths in a fixture are relative to that fixture's folder. No tool is downloaded
or built automatically. To compare two Gutch binaries, give their lanes distinct
labels and put each executable under its label in `executables`.

## Pairwise comparisons

Run one pair with the same shared Blender inputs:

```text
python run.py --fixture gutch_vs_kopia
python run.py --fixture gutch_vs_restic
python run.py --fixture gutch_vs_rustic
python run.py --fixture gutch_vs_borg
python run.py --fixture gutch_vs_plakar
python run.py --fixture gutch_vs_bpt
```

These fixtures use one warm-up, three measured repetitions, rotating order and
profiling off. Each references `blender/dataset.yaml` for inputs, reusing the
cache rather than duplicating the Blender input definitions. This shared file
defines inputs only; every shipped runnable fixture compares Gutch with one tool.
Set executable paths in the selected fixture as needed. Custom fixtures may use `dataset: file.yaml`
instead of `builds`; build paths are relative to the shared definition file.
Nested dataset references are not supported.

| Pair | Other tool's performance defaults | Gutch profile |
|---|---|---|
| Kopia 0.23.1 | Buzhash 4 MiB target; file compression off | `chunk_4MiB`, compression `none`, `bundle_16MiB` |
| Restic 0.19.1 | Rabin approximately 1 MiB; Zstd `auto` | `chunk_1MiB`, Zstd 3 |
| Rustic 0.11.4 | Rabin approximately 1 MiB; repository Zstd level 3 selected | `chunk_1MiB`, Zstd 3 |
| Borg 2.0.0b25 | FastCDC approximately 2 MiB, normalization 2; LZ4 | `chunk_2MiB`, LZ4 0 |
| Plakar 1.1.8 | FastCDC approximately 1 MiB; default LZ4 stream writer | `chunk_1MiB`, LZ4 0 |
| BPT 1.8.8 | 1 MiB window; internal compression | `chunk_1MiB`, Zstd 3 (codec unmatched) |

Gutch keeps automatic workers and its native FastCDC algorithm. Bundles use the
8 MiB profile except the Kopia pair, which requires the 16 MiB profile because
its 4 MiB chunk profile allows chunks up to 16 MiB.
Chunk bounds, normalization, codec implementations, metadata compression and
storage layouts are not identical. Plakar's stream writer does not apply the
stored compression level; its default LZ4 behavior is matched approximately,
not treated as equivalent to Gutch LZ4 high compression level 9.

Fixture descriptions explain command overrides and differences from Gutch. They
are printed before execution and included in `summary.md` and `run.json`.

External tool releases were verified on 2026-10-31; URLs and archive SHA-256
values are recorded in [the local tool manifest](bin/manifest.json). Borg tracks
the latest 2.x prerelease because the fixtures require Borg 2 FastCDC; other
external tools track stable releases. The five pre-existing Windows adapters were
checked with two small deterministic builds. Rustic command construction is covered by mocked tests only; its capture,
restore, verification and recovery have not been executed. Linux assets were
checksum-verified but not executed during this refresh.

Borg 2.0.0b25 removed `none-sha256`. The suite uses `authenticated-sha256`, with
unencrypted authenticated payloads and a fixed local test passphrase protecting
the repository key. Initial restore and recovery both use `--continue` because
multiple versions share the output root. Independent content validation still
checks every restored build. Earlier `none-sha256` measurements are not directly
comparable with this authenticated mode.
Encryption is disabled wherever supported; an empty password is not treated as
plaintext. Kopia, Restic and Rustic remain encrypted because they have no supported
plaintext mode.

Existing operational choices remain: isolated repositories/caches, no encryption
for Borg/Plakar, encryption for Kopia/Restic/Rustic, independent validation, and native
recovery options. Thus these preserve performance defaults where practical;
they are not unmodified default invocations. Extra files remain nonfatal.
Use detailed profiling only in a separate diagnostic run.
Each pair selects its own approximate match. There is no all-tools preset:
chunking algorithms, bounds, compression work, encryption and packing differ.
Interpret results as complete tool workflows, not isolated codec benchmarks.
Chunk targets are nominal parameters, not measured means.

Rustic's `arguments` apply to repository initialization; the shipped pair selects
`--set-compression 3`. Backup uses a stable relative path and unique per-build tag.
Restore selects that tagged snapshot's build subtree, verifies existing bytes,
and disables ownership restoration. Recovery adds `--delete` only within that
build's destination. The adapter uses an explicit empty profile and run-owned
cache, then checks all repository data separately from backup/restore timings.
These commands target [Rustic 0.11.4](https://github.com/rustic-rs/rustic/releases/tag/v0.11.4).
Actual runtime compatibility and performance still need a user-selected run.

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
| Rustic | `restore --verify-existing --no-ownership --delete` | Native deletion requested within one build directory. Command construction is mock-tested; runtime recovery is unverified. |
| Kopia | `snapshot restore --delete-extra` | Native extra deletion requested. Installed 0.23.1 failed replacing a read-only damaged file; atomic writes also failed in a separate probe. |
| Borg | `extract --continue` (Borg 2 only) | No native extra deletion option. An earlier Windows Borg 2 probe failed on the read-only file. Resume skips based on metadata, so it is not a content-integrity guarantee. |
| Plakar | `restore` into the existing destination | No native extra deletion option established. The earlier 1.1.5 probe left an extra file and a content mismatch. |
| BuildPatchTool | `InstallManifest -PrevManifest=...` | No native extra deletion option advertised. Installed 1.8.8 left the unexpected file. |

The historical outcomes above (excluding the unexecuted Rustic adapter) are
from the earlier probe that also changed read-only attributes. Current corruption
plans no longer change permissions; those results need a new run before comparison. They are not claims
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

## Use as a Python dependency

Other benchmark harnesses can install this checkout with
`python -m pip install -e <suite-checkout>` and import
`comparison_benchmark_suite`. This is optional for `python run.py`. The package
contains the same runtime and bundled fixtures; it has no parent-repository
imports, build steps, or configuration. Tool binaries remain explicit inputs or
are resolved from PATH. Downloads, fixtures, and reports belong to this project.

## Maintaining the suite

Start at `run.py` for CLI and terminal selection, and `benchmark.py` for a single
comparison run. `interactive.py` launches the same CLI and displays its progress.
`tools/report.py` owns the shared summary cells and report presentation.

Tool workflows live in `tools/`; scheduling and aggregate measurements live in
`scheduling/`; process execution, validation, and traces live in `support/`.
The suite compares individual snapshots through capture, clean restore, and
optional repair. Batch/whole-product Gutch workflows, diagnostic reports, and
the internal fixture catalog belong to the Gutch harness, which imports shared
measurement and validation helpers from this package.

Install the checkout as a package before running development tests. This keeps
imports independent of the checkout folder name:

```text
python -m pip install -e .
python -m unittest discover -s tests
```

The tests cover portable execution, failure isolation, output validation,
archive path boundaries, the interactive run flow, and cancellation.
Rustic adapter tests use mocked commands and block subprocess creation. The
fixture catalog checks keep shipped comparisons pairwise.

Fixtures use a `lanes` list with explicit labels and a `profile` mapping for
Gutch options. `profile.chunker` accepts `fastcdc` (default), `jc` for
Plakar-compatible jump chunking, or `vram256` for RAM with AVX2/scalar dispatch; `profile.chunk` selects the size target.
Alternate lane mappings, string profiles, and external bulk
workloads are not supported. Plain-terminal progress uses start/completion
lines; the interactive screen owns live progress. Borg commands use Borg 2
syntax directly. Executables resolve only from explicit paths or PATH.
