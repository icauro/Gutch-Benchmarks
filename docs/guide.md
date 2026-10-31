# Benchmark guide

Original project code is [MIT licensed](../LICENSE). External tools, workloads and
dependencies retain their own terms; see [third-party notices](third-party-notices.md).

Compare storage tools using the same builds and independent SHA-256 checks.
This root project works on its own: copy it anywhere, with any folder name. It does not need the Gutch
repository, Rust, Docker, or cloud credentials.

## Manual GitHub Actions runs

Open **Actions > Manual Linux benchmarks > Run workflow**. The default runs all
six Gutch-vs-tool pairs on Ubuntu 24.04, each in a separate job. All selected
pair jobs can run concurrently; tools within a pair run sequentially. Choose a
single pair, a Gutch branch/tag/commit, and measured repetitions if needed.
One warm-up is always included. Nothing runs on pushes, pull requests or a schedule.

The workflow prepares Blender once, then every pair restores the same validated
input cache. The cache key depends on the dataset recipe and preparation code,
not the pair or Gutch revision. Any future test job in this repository that needs
these inputs should reuse `.github/actions/blender-inputs` after installing the
suite. A preparation job uses `populate: 'true'`; consumers restore and validate.
GitHub caches are repository-scoped; a different repository cannot directly
restore this cache. Synthetic unit tests still generate their own tiny inputs.

Gutch is built once from the selected revision with the locked Rust dependencies;
all pairs use that executable. The build artifact includes the source and
dependency notices produced by Gutch's `tools/package_cli.py`. While Gutch is
private, source checkout uses the
read-only deploy key stored as the `GUTCH_DEPLOY_KEY` Actions secret in this
repository. External tools are explicitly downloaded for CI
from `src/comparison_benchmark_suite/resources/tools.json`, with archive and executable checksum verification.
BPT retains its accompanying Engine files. Tools and datasets never enter Git.
Input restoration, validation, downloads and builds are outside benchmark timing.

Every case discards its tool repository, restored output and caches after its
measurements, including failures. The immutable input cache survives. Detailed
reports, logs and traces are Actions artifacts retained for 30 days. The Gutch
build artifact lasts seven days. Nothing uploads repository/output payloads.

Default-branch runs commit compact JSON reports and a Markdown report under
`reports/<UTC-date>/<run-id>-<attempt>/`, then update the latest-results section
above. Each pair has its own table and a Gutch-relative row computed from raw
medians: times show faster/slower factors, and storage shows percentage size differences.
Failed pairs, missing/nonpositive measurements and unequal sample counts receive
no ratio. Failed or missing pairs are shown explicitly. Runs from other branches
retain Actions artifacts without updating the README. Repository rules must
allow the workflow's `contents: write` token to push report commits; otherwise
publication fails and the detailed reports remain downloadable from Actions.

Caches can be evicted: the next preparation job downloads and verifies them
again. Consumer jobs fail clearly if the prepared cache disappears before they
restore it. Each benchmark job has a 330-minute timeout. Hosted-runner CPU/disk
performance and OS caches are uncontrolled; use these results as indicative
comparisons, rather than precise measurements of small changes across runs.
The first real workflow execution is a separate manual action.

## Run

Install Python 3.12 or newer, then run these commands in this folder:

```text
python -m pip install -e .
gutch-bench
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
gutch-bench --fixture gutch_vs_rustic
```

The `--fixture` form runs once and exits. `--no-open-perfetto` suppresses automatic
browser opening; the interactive screen uses this and opens Perfetto only when
requested. Reinstall the package after dependency changes to update the terminal UI.

Selecting a shipped pair explicitly prepares the pinned Blender 5.0.0 and 5.1.0
Windows x64 ZIP inputs in `src/comparison_benchmark_suite/fixtures/blender/dataset.yaml`. Both Linux and Windows
benchmark those same files as data; Blender is never executed. Missing inputs
are downloaded from Blender's official server, SHA-256 checked and extracted
under `.artifacts/`. Existing prepared inputs are inventoried before reuse.
Use local `path` builds in a custom fixture to work without downloading inputs.
Each fixture runs one warm-up and six measured repetitions, rotating tool order.
Preparation and independent output validation are outside tool-command timings.
OS cache state is uncontrolled; these are not cold-cache measurements.

Comparison executables are supplied locally. Install tools on PATH, set their
paths in the fixture, or place them in the ignored `.artifacts/tools/windows-x64/` or
`.artifacts/tools/linux-x64/` folders. Executables and vendor runtime distributions are not
tracked. The local runner never downloads tools automatically; CI provisions
them explicitly. For example:

```yaml
executables:
  gutch: C:/tools/gutch-cli.exe
  restic: C:/tools/restic.exe
  buildpatchtool: C:/tools/BuildPatchTool.exe
```

Local tools are discovered automatically under `.artifacts/tools/windows-x64/`
or `.artifacts/tools/linux-x64/`, before searching PATH. Each tool has its own
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
or built automatically by the local runner. To compare two Gutch binaries, give
their lanes distinct labels and put each executable under its label in `executables`.

## Pairwise comparisons

Run one pair with the same shared Blender inputs:

```text
gutch-bench --fixture gutch_vs_kopia
gutch-bench --fixture gutch_vs_restic
gutch-bench --fixture gutch_vs_rustic
gutch-bench --fixture gutch_vs_borg
gutch-bench --fixture gutch_vs_plakar
gutch-bench --fixture gutch_vs_bpt
```

These fixtures use one warm-up, six measured repetitions, rotating order and
profiling off. Each references the bundled `blender/dataset.yaml` for inputs, reusing the
cache rather than duplicating the Blender input definitions. This shared file
defines inputs only; every shipped runnable fixture compares Gutch with one tool.
Set executable paths in the selected fixture as needed. Custom fixtures may use `dataset: file.yaml`
instead of `builds`; build paths are relative to the shared definition file.
Nested dataset references are not supported.

| Pair | Other tool's performance defaults | Gutch profile |
|---|---|---|
| Kopia 0.23.1 | Buzhash 4 MiB target; file compression off | `chunk_4MiB`, compression `none`, `bundle_16MiB` |
| Restic 0.19.1 | Rabin approximately 1 MiB; Zstd `auto` | `chunk_1MiB`, Zstd 3 |
| Rustic 0.11.4 | Rabin approximately 1 MiB; Zstd 3; 8 MiB data/tree packs | `chunk_1MiB`, Zstd 3 |
| Borg 2.0.0b25 | FastCDC approximately 2 MiB, normalization 2; LZ4 | `chunk_2MiB`, LZ4 0 |
| Plakar 1.1.8 | FastCDC approximately 1 MiB; default LZ4 stream writer | `chunk_1MiB`, LZ4 0 |
| BPT 1.8.8 | 1 MiB window; internal compression | `chunk_1MiB`, Zstd 3 (codec unmatched) |

Gutch uses four workers and its native FastCDC algorithm. Bundles use the
8 MiB profile except the Kopia pair, which requires the 16 MiB profile because
its 4 MiB chunk profile allows chunks up to 16 MiB.
Chunk bounds, normalization, codec implementations, metadata compression and
storage layouts are not identical. Plakar's stream writer does not apply the
stored compression level; its default LZ4 behavior is matched approximately,
not treated as equivalent to Gutch LZ4 high compression level 9.

Fixture descriptions explain command overrides and differences from Gutch. They
are printed before execution and included in `summary.md` and `run.json`.

External tool versions and checksums are pinned in [the tool manifest](../src/comparison_benchmark_suite/resources/tools.json).
Borg tracks a 2.x prerelease because this pair requires Borg 2 FastCDC.

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
they are not unmodified default invocations. Contract 2 validates supported recovery outcomes strictly.
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
Local compatibility is checked separately from performance runs; smoke-test results do not replace Blender measurements.

## Measurement contract 2

New runs use six measured repetitions plus one warm-up, rotating tool order.
A one-repetition, zero-warm-up local fixture is suitable for compatibility checks.
The existing saved public results use the earlier contract and are not rewritten.

- First capture, later-version capture and later-version repository byte growth are recorded separately.
- Capture and native restore/repair timers retain native integrity checks. Repository creation and the full repository check remain separate.
- Every native adapter uses the same strict output inventory and SHA-256 validator. Validation-inclusive metrics add its duration to native command time; native verification work is not subtracted.
- A source-derived corruption plan flips bytes in the smallest and largest writable nonempty files, and deletes a distinct file when available. The same source paths are selected for every tool.
- Content repair and preserved-mtime repair are separate. The latter keeps file length and mtime unchanged. Borg resume cannot detect that damage and receives an explicit unsupported outcome.
- Extra-file cleanup is a separate exact-directory check. Borg, Plakar and BPT have no native deletion in these adapters and receive unsupported outcomes; the harness does not delete extras on their behalf.
- Full restore recovery removes the owned destination before native restoration. Strict validation follows every supported operation. Wrong bytes or unexpected files fail the case.
- Detailed tables show medians, minimum, maximum and sample counts. These ranges are descriptive, not confidence intervals.

Gutch uses four workers. Go tools use `GOMAXPROCS=4`; Rustic uses
`RAYON_NUM_THREADS=4`; Kopia file/restore parallelism and Plakar concurrency are
explicitly four. Borg/BPT keep native scheduling; these controls are not identical
CPU or memory limits. Encryption remains disabled where supported.

Borg explicitly selects `fastcdc,19,23,21,2` and LZ4. Kopia explicitly selects
`DYNAMIC-4M-BUZHASH`, no content compression and AES256-GCM-HMAC-SHA256.
Restic selects Zstd auto and an 8 MiB pack target. Rustic selects Rabin with a
1 MiB average, 512 KiB minimum and 8 MiB maximum, Zstd 3, and 8 MiB data/tree
pack targets with growth disabled. BPT explicitly selects a 1 MiB chunk window.
Gutch bundle compression and native peer compression units still differ.
Actual commands, binary checksums and fixture settings are recorded with each run.

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
gutch-bench --fixture fixtures/my_product
```

You can also pass a fixture directory or YAML path. List at least two builds,
oldest first. Their directory names do not determine ordering. Inputs are copied
into an owned cache and independently inventoried; originals are not mutated.
The cache is checked before reuse. Custom local builds also work on platforms
without a built-in Blender download.

## Results

The final CI publishing step generates a paired-bar `comparison.svg` from the
latest saved result for each pair, and updates `reports/comparison.svg` shown
near the top of the README. Detailed tables are collapsed and link to each
pair’s source report, including older runs when only one pair was rerun.
The chart uses a black background. Each cell has
its own linear scale; blue is Gutch and orange is the paired tool. Values and
relative factors use the same source medians as the Markdown tables. Storage
differences show percentages relative to the paired tool; timing ratios below
1.005× show `~same`. These are display rounding rules, not significance tests. Failed
pairs stay visible without blocking other rows. The SVG needs no plotting or
image-generation dependency.

Generate a local image from saved reports without running benchmarks:

```sh
python -m comparison_benchmark_suite.tools.chart --reports reports --output .artifacts/charts/latest.svg
```

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
By default, failed local runs retain payloads and command evidence. Pass
`--discard-outputs` with `--fixture` to delete payloads and tool caches after each
case, including failures; CI always selects this option. Reports and command
evidence survive. Other candidates continue after a failed case.
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

## Peak RAM and disk

Shipped fixtures enable `resource_sampling: true`. After speed repetitions, one
additional fresh workflow per tool collects resource measurements. These commands
never contribute speed samples, medians or speed traces. `resources.json` records
raw monitored results; `summary.json` labels these peaks as `separate_resource_pass`.
CI retains both evidence and compact resource results. The main chart shows speed
and stored size; each pair’s resource table immediately follows its speed table.
Rows are programs; the eight columns are initial-capture RAM/disk, next-capture
RAM/disk, restore RAM/disk and content-repair RAM/disk. Operation RAM is the maximum
across its commands; restore and repair cover both versions. Per-command disk
values remain unavailable until recorded. The latest run’s RAM breakdown is
derived from its saved command artifacts in `<pair>-resources.json`; its original
report JSON and whole-workflow disk peaks remain unchanged.

Peak RAM is the largest sampled sum of RSS across a command and its descendants,
then the maximum across commands in that resource workflow. Shared pages can be
counted in more than one process. The target polling interval is 2 ms; sampling
can miss short-lived descendants or brief spikes. CPU remains direct-process CPU.

Peak disk is the maximum sampled apparent file size across the lane's repository,
restored output, temporary files and caches (including Plakar's external cache).
During resource passes, `TMPDIR`, `TMP` and `TEMP` point into the monitored lane.
Tools that ignore these variables and write elsewhere are outside this scope.
Inputs, executables and benchmark logs/stats/traces are excluded. Hard-linked
files are counted once per scan. This is working-file space, not physical block
allocation or disk I/O volume. Directory scans target 100 ms intervals and can
miss transient files. Monitoring overhead is confined to the resource pass.
Missing or failed samples remain unavailable rather than becoming zero.

## Native recovery and extra files

Contract 2 changes file content without changing permissions. Content damage,
preserved-mtime damage, unexpected files, and full restoration are separate
checks. The harness does not identify damaged files for the tool or remove extras
on its behalf. Strict validation follows every supported check.

| Tool | Native recovery | Preserved-mtime damage | Extra-file cleanup |
|---|---|---|---|
| Gutch | Installation repair | Supported | Supported |
| Restic | `restore --overwrite always --delete --verify` | Supported | Supported, scoped to selected build |
| Rustic | `restore --verify-existing --no-ownership --delete` | Supported | Supported, scoped to selected build |
| Kopia | `snapshot restore --delete-extra` | Supported | Supported |
| Borg | `extract --continue` | Unsupported: trusts matching size/mtime | Unsupported in adapter |
| Plakar | Restore over existing destination | Supported | Unsupported in adapter |
| BuildPatchTool | `InstallManifest -PrevManifest=...` | Supported | Unsupported in adapter |

All six pairs passed a Windows functional smoke test on 2026-10-31 using two
small deterministic synthetic builds, one measured repetition and no warm-up.
These checks validate command compatibility and supported outcomes, not Blender
performance, Linux behavior, read-only-file recovery or statistical significance.
The older public Blender results retain their original measurement protocol.
Unexpected command failures or incorrect output fail the case; no fallback masks
a native repair failure. Other scheduled lanes can still run.

## BuildPatchTool

Download the executable from [Epic](https://launcher-public-service-prod06.ol.epicgames.com/launcher/api/installer/download/BuildPatchTool.zip),
extract it with its accompanying Engine files, and set `executables.buildpatchtool`.
The adapter probes `-mode=ChunkBuildDirectory -help` and
runs only the supported local generation interface. Epic Store upload-only
interfaces are reported as `UNSUPPORTED`; no upload or authentication is attempted.
Each build gets an explicit manifest in a shared cloud directory. The adapter
passes an empty `AppLaunch` for these data-only workloads: BPT otherwise marks
the chosen launch file executable, changing metadata on Windows ZIP inputs
when restored on Linux. Independent validation still checks executable bits.
The adapter
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
`comparison_benchmark_suite`. This is optional for `gutch-bench`. The package
contains the same runtime and bundled fixtures; it has no parent-repository
imports, build steps, or configuration. Tool binaries remain explicit inputs or
are resolved from PATH. Downloads, fixtures, and reports belong to this project.

## Maintaining the suite

Python code lives under `src/comparison_benchmark_suite/`. `cli.py` owns command
entry, `benchmark.py` owns a comparison run, and `interactive.py` launches that
same installed module. `tools/report.py` owns summary cells and presentation.
Presets live in the package's `fixtures/`; the tool manifest and upstream notices
live in `resources/`. `.github/scripts/benchmarks.py` owns CI preparation and
publication. Tests, documentation and published reports have their own root
folders. Dependencies and the `gutch-bench` entrypoint are in `pyproject.toml`.

Tool workflows live in `tools/`; scheduling and aggregate measurements live in
`scheduling/`; process execution, validation, and traces live in `support/`.
The suite compares individual snapshots through capture, clean restore, and
optional repair. Batch/whole-product Gutch workflows, diagnostic reports, and
the internal fixture catalog belong to the Gutch harness, which imports shared
measurement and validation helpers from this package.

Install the checkout as a package before running development tests. This keeps
imports independent of the checkout folder name. Installed runs write caches,
tools and reports under `.artifacts/` in the current working directory. Use
`python -m comparison_benchmark_suite` as an alternative to `gutch-bench`:

```text
python -m pip install -e .
python -m unittest discover -s tests
```

The tests cover portable execution, failure isolation, output validation,
archive path boundaries, the interactive run flow, and cancellation.
Rustic adapter tests use mocked commands and block subprocess creation. The
fixture catalog checks keep shipped comparisons pairwise. CI tests use tiny
synthetic archives and mocked cases to check input-cache reuse, checksum failures,
output disposal and report publishing without running comparison tools.

Fixtures use a `lanes` list with explicit labels and a `profile` mapping for
Gutch options. `profile.chunker` accepts `fastcdc` (default), `jc` for
Plakar-compatible jump chunking, or `vram256` for RAM with AVX2/scalar dispatch; `profile.chunk` selects the size target.
Alternate lane mappings, string profiles, and external bulk
workloads are not supported. Plain-terminal progress uses start/completion
lines; the interactive screen owns live progress. Borg commands use Borg 2
syntax directly. Executables resolve from explicit paths, the working directory's
`.artifacts/tools/` folders, or PATH.
