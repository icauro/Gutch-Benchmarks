# Gutch benchmarks

Compare Gutch against Borg, BuildPatchTool, Kopia, Plakar, Restic and Rustic
using shared Blender inputs, pair-specific settings and SHA-256 output validation.

![Latest per-pair benchmark comparisons](reports/comparison.svg)

<details>
<summary>Comparison differences and limits</summary>

The numbers in the chart refer to these notes. Every pair processes the same
files, and we check restored content with SHA-256.

1. **Borg:** Both use FastCDC chunking and LZ4 compression, but split and store data differently. Borg's resume command can skip files whose size and modification time match, even if their contents are damaged. We therefore mark that repair scenario as unsupported.
2. **Plakar:** Both use FastCDC and LZ4, but compress and pack data differently. Plakar restores over existing files, while Gutch selectively repairs damaged content; their recovery commands do different work.
3. **Kopia:** Compression is disabled on both sides. Kopia uses Buzhash to split files into chunks; Gutch uses FastCDC. Matching the target chunk size does not produce identical chunks.
4. **Restic:** Restic uses Rabin chunking and automatic Zstd compression; Gutch uses FastCDC and Zstd level 3. These settings do not produce identical chunks or compression work.
5. **Rustic:** Both select Zstd level 3, but Rustic uses Rabin chunking and Gutch uses FastCDC. Gutch compresses whole bundles, so matching the level and pack size still does not make the compression work identical.
6. **BuildPatchTool:** Its chunk window and internal compression do not match Gutch's FastCDC and Zstd settings. Recovery uses a previous installation manifest, so this compares two artifact-delivery workflows.

Kopia, Restic and Rustic require encryption; Gutch does not encrypt in these tests,
so that extra work remains in their timings. New runs separate damaged-file repair,
damage with unchanged timestamps, extra-file cleanup and full restoration. Borg,
Plakar and BuildPatchTool have no native extra-file cleanup in these adapters;
unsupported checks receive no timing.

Chart times include each tool's own checks. Detailed reports also show timings
with our shared validation added and sample ranges. Metadata handling and when
tools flush writes can still differ. New performance runs use six measured
repetitions with alternating order; OS caches are not reset. A single local smoke
run checks compatibility only. Older reports retain their original settings.

</details>

<!-- latest-benchmarks:start -->
Latest per pair · Linux · Blender 5.0.0 → 5.1.0 · 2026-10-31 · earlier measurement protocol

[All-pairs report](reports/2026-10-31/41200340952-1/README.md) · [BPT rerun](reports/2026-10-31/41201391345-1/README.md)

Lower values are better. Pair settings differ; bars scale independently within each cell.
Hosted-runner timings are indicative; OS caches are uncontrolled.

<details>
<summary>Detailed results and source reports</summary>

[Source: Gutch vs borg](reports/2026-10-31/41200340952-1/borg.json)

### Gutch vs Borg (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| borg | PASS | 8.815 | 7.575 | 2.474 | 918.275 |
| gutch | PASS | 10.708 | 1.945 | 0.514 | 913.570 |
| **Gutch relative** | - | 1.21x slower | 3.89x faster | 4.81x faster | 0.5% smaller |

[Source: Gutch vs bpt](reports/2026-10-31/41201391345-1/bpt.json)

### Gutch vs BuildPatchTool (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| buildpatchtool | PASS | 25.488 | 25.503 | 1.198 | 732.343 |
| gutch | PASS | 6.018 | 1.526 | 0.446 | 689.362 |
| **Gutch relative** | - | 4.24x faster | 16.72x faster | 2.69x faster | 5.9% smaller |

[Source: Gutch vs kopia](reports/2026-10-31/41200340952-1/kopia.json)

### Gutch vs Kopia (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| gutch | PASS | 5.621 | 1.557 | 0.650 | 1758.175 |
| kopia | PASS | 4.685 | 7.262 | 7.666 | 1754.523 |
| **Gutch relative** | - | 1.20x slower | 4.66x faster | 11.80x faster | 0.2% larger |

[Source: Gutch vs plakar](reports/2026-10-31/41200340952-1/plakar.json)

### Gutch vs Plakar (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| gutch | PASS | 5.988 | 2.034 | 0.419 | 913.907 |
| plakar | PASS | 8.821 | 3.912 | 13.458 | 916.210 |
| **Gutch relative** | - | 1.47x faster | 1.92x faster | 32.09x faster | 0.3% smaller |

[Source: Gutch vs restic](reports/2026-10-31/41200340952-1/restic.json)

### Gutch vs Restic (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| gutch | PASS | 5.587 | 2.323 | 0.705 | 689.362 |
| restic | PASS | 8.969 | 5.731 | 4.002 | 714.666 |
| **Gutch relative** | - | 1.61x faster | 2.47x faster | 5.68x faster | 3.5% smaller |

[Source: Gutch vs rustic](reports/2026-10-31/41200340952-1/rustic.json)

### Gutch vs Rustic (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| gutch | PASS | 5.687 | 2.353 | 0.726 | 689.362 |
| rustic | PASS | 14.522 | 5.760 | 4.311 | 700.319 |
| **Gutch relative** | - | 2.55x faster | 2.45x faster | 5.93x faster | 1.6% smaller |

</details>

<!-- latest-benchmarks:end -->

## Run on GitHub

Open **Actions > Manual Linux benchmarks > Run workflow**. Choose `all` or one
pair, the Gutch revision, and repetitions. Defaults: Ubuntu 24.04, all six pairs,
one warm-up and six measured repetitions.
All six pairs can run concurrently, each on its own runner.

All jobs share a validated Blender input cache. Repositories and restored outputs
are discarded after each sample. Runs on the default branch save compact reports
in Git and update this page; detailed logs and traces remain Actions artifacts
for 30 days. Hosted-runner timings are indicative; OS caches are uncontrolled.

## Run locally

Requires Python 3.12+ and the selected tool executables on PATH or in the ignored
`.artifacts/tools/<platform>/<tool>/` folders.

```sh
python -m pip install -e .
gutch-bench
# Or select one pair:
gutch-bench --fixture gutch_vs_rustic --no-open-perfetto --discard-outputs
```

Selecting a shipped fixture downloads and checksum-verifies the pinned Blender
5.0.0 and 5.1.0 inputs if missing. Reports are written under `.artifacts/runs/`.
Local runs retain failed outputs unless `--discard-outputs` is selected.

See the [benchmark guide](docs/guide.md) for settings, custom inputs, recovery,
report interpretation and development instructions. Tool versions and checksums
are recorded in the [manifest](src/comparison_benchmark_suite/resources/tools.json).

[MIT licensed](LICENSE). External tools and workloads retain their own licenses;
see [third-party notices](docs/third-party-notices.md).
