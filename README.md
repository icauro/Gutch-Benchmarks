# Gutch benchmarks

Compare Gutch against Borg, BuildPatchTool, Kopia, Plakar, Restic and Rustic
using shared Blender inputs, pair-specific settings and SHA-256 output validation.

![Latest per-pair benchmark comparisons](_docs/reports/comparison.svg?v=4d50ebddfe5e)

![Peak RAM by operation](_docs/reports/ram.svg?v=195728a478f8)

![Peak disk by operation](_docs/reports/disk.svg?v=75c5848052f3)

<details>
<summary>Comparison differences and limits</summary>

The numbers in the chart refer to these notes. Every pair processes the same
files, and we check restored content with SHA-256.

1. **[Restic](https://github.com/restic/restic):** Restic uses Rabin chunking and automatic Zstd compression; Gutch uses FastCDC and Zstd level 3. These settings do not produce identical chunks or compression work.
2. **[Kopia](https://github.com/kopia/kopia):** Compression is disabled on both sides. Kopia uses Buzhash to split files into chunks; Gutch uses FastCDC. Matching the target chunk size does not produce identical chunks.
3. **[Borg](https://github.com/borgbackup/borg):** Both use FastCDC chunking and LZ4 compression, but split and store data differently. Borg's resume command can skip files whose size and modification time match, even if their contents are damaged. We therefore mark that repair scenario as unsupported.
4. **[Rustic](https://github.com/rustic-rs/rustic):** Both select Zstd level 3, but Rustic uses Rabin chunking and Gutch uses FastCDC. Gutch compresses whole bundles, so matching the level and pack size still does not make the compression work identical.
5. **[Plakar](https://github.com/PlakarKorp/plakar):** Both use FastCDC and LZ4, but compress and pack data differently. Plakar restores over existing files, while Gutch selectively repairs damaged content; their recovery commands do different work.
6. **[BuildPatchTool](https://github.com/EpicGames/UnrealEngine):** Its chunk window and internal compression do not match Gutch's FastCDC and Zstd settings. Recovery uses a previous installation manifest, so this compares two artifact-delivery workflows. Its source repository requires [Epic-authorized access](https://dev.epicgames.com/documentation/unreal-engine/downloading-source-code-in-unreal-engine).

Kopia, Restic and Rustic require encryption; Gutch does not encrypt in these tests,
so that extra work remains in their timings. New runs separate damaged-file repair,
damage with unchanged timestamps, extra-file cleanup and full restoration. Borg,
Plakar and BuildPatchTool have no native extra-file cleanup in these adapters;
unsupported checks receive no timing.

Chart times include each tool's own checks. Detailed reports also show timings
with our shared validation added and sample ranges. Metadata handling and when
tools flush writes can still differ. New performance runs default to six measured
repetitions with alternating order; OS caches are not reset. A single local smoke
run checks compatibility only. Older reports retain their original settings.

The second SVG shows peak RAM; the third shows peak disk footprint. Both reuse the
same paired-bar template with first capture, second capture, restore and repair
columns in MiB from a separate monitored pass. Text versions
remain below each pair in the details. New runs record disk peaks per command;
older reports without those samples show `—`. Disk includes existing repository,
cache and output files, rather than growth or bytes written. Whole-workflow peaks
are not substituted for missing command measurements.
Sampling may miss short spikes; RAM includes child processes.

</details>

<!-- latest-benchmarks:start -->
Latest per pair · Linux · Blender 5.0.0 → 5.1.0 · 2026-11-17 · includes earlier measurement protocols

[This run's report](_docs/reports/2026-11-17/44101528054-1/README.md) · [Actions logs and artifacts](https://github.com/icauro/Gutch-Benchmarks/actions/runs/44101528054)

<details>
<summary>Detailed results and source reports</summary>

[Source: Gutch vs restic](_docs/reports/2026-11-17/44101528054-1/restic.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Restic](https://github.com/restic/restic) (ERROR)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | NOT_RUN | - | - | - | - |
| [Restic](https://github.com/restic/restic) | NOT_RUN | - | - | - | - |
| **Gutch relative** | - | - | - | - | - |

[Source: Gutch vs kopia](_docs/reports/2026-11-17/44101528054-1/kopia.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Kopia](https://github.com/kopia/kopia) (ERROR)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | NOT_RUN | - | - | - | - |
| [Kopia](https://github.com/kopia/kopia) | NOT_RUN | - | - | - | - |
| **Gutch relative** | - | - | - | - | - |

[Source: Gutch vs borg](_docs/reports/2026-11-17/44101528054-1/borg.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Borg](https://github.com/borgbackup/borg) (ERROR)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | NOT_RUN | - | - | - | - |
| [Borg](https://github.com/borgbackup/borg) | NOT_RUN | - | - | - | - |
| **Gutch relative** | - | - | - | - | - |

[Source: Gutch vs rustic](_docs/reports/2026-11-17/44101528054-1/rustic.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Rustic](https://github.com/rustic-rs/rustic) (ERROR)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | NOT_RUN | - | - | - | - |
| [Rustic](https://github.com/rustic-rs/rustic) | NOT_RUN | - | - | - | - |
| **Gutch relative** | - | - | - | - | - |

[Source: Gutch vs plakar](_docs/reports/2026-11-17/44101528054-1/plakar.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Plakar](https://github.com/PlakarKorp/plakar) (ERROR)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | NOT_RUN | - | - | - | - |
| [Plakar](https://github.com/PlakarKorp/plakar) | NOT_RUN | - | - | - | - |
| **Gutch relative** | - | - | - | - | - |

[Source: Gutch vs bpt](_docs/reports/2026-11-17/44101528054-1/bpt.json)

### [Gutch](https://github.com/icauro/Gutch) vs [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) (ERROR)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | NOT_RUN | - | - | - | - |
| [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) | NOT_RUN | - | - | - | - |
| **Gutch relative** | - | - | - | - | - |

</details>

<!-- latest-benchmarks:end -->

<details>
<summary>Run on GitHub</summary>

Open **Actions > Manual Linux benchmarks > Run workflow**. Choose `all` or one
pair, a Gutch release, and repetitions. Defaults: Ubuntu 24.04, all six pairs,
one warm-up and six measured repetitions.
All six pairs can run concurrently, each on its own runner.

All jobs share a validated Blender input cache. Repositories and restored outputs
are discarded after each sample. Runs on the default branch save compact reports
in Git and update this page; detailed logs and traces remain Actions artifacts
for 30 days. Hosted-runner timings are indicative; OS caches are uncontrolled.

</details>

<details>
<summary>Run locally</summary>

Requires Python 3.12+ and the selected tool executables on PATH or in the ignored
`.artifacts/tools/<platform>/<tool>/` folders.

```sh
python -m pip install -e .
gutch-bench
# Or select one pair:
gutch-bench --fixture gutch_vs_rustic --no-open-perfetto --discard-outputs
```

Selecting a shipped fixture downloads and checksum-verifies the pinned Blender
5.0.0 and 5.1.0 inputs if missing. Reports are written under `.artifacts/benchmarks/runs/`.
Local runs retain failed outputs unless `--discard-outputs` is selected.

</details>

See the [benchmark guide](_docs/guide.md) for settings, custom inputs, recovery,
report interpretation and development instructions. Tool versions and checksums
are recorded in the [manifest](src/comparison_benchmark_suite/resources/tools.json).

[MIT licensed](LICENSE). External tools and workloads retain their own licenses;
see [third-party notices](_docs/third-party-notices.md).
