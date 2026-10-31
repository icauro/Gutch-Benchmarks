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
tools flush writes can still differ. New performance runs default to six measured
repetitions with alternating order; OS caches are not reset. A single local smoke
run checks compatibility only. Older reports retain their original settings.

Peak RAM and peak disk come from one separate monitored pass per tool, so monitoring
does not affect the chart's speed measurements. RAM includes child processes;
disk counts tool-owned working files, including caches and restored output, but
excludes shared inputs, executables and benchmark logs. Peaks are sampled and may
miss short spikes; older results show `—` until measured.

</details>

<!-- latest-benchmarks:start -->
Latest per pair · Linux · Blender 5.0.0 → 5.1.0 · 2026-10-31 · measurement contract 2

[This run's report](reports/2026-10-31/41212694831-1/README.md) · [Actions logs and artifacts](https://github.com/icauro/Gutch-Benchmarks/actions/runs/41212694831)

Lower values are better. Pair settings differ; bars scale independently within each cell.
Hosted-runner timings are indicative; OS caches are uncontrolled.

<details>
<summary>Detailed results and source reports</summary>

[Source: Gutch vs borg](reports/2026-10-31/41212694831-1/borg.json)

### Gutch vs Borg (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB | Peak RAM MiB | Peak disk MiB |
|---|---|---:|---:|---:|---:|---:|---:|
| borg | PASS | 10.875 | 8.048 | 3.194 | 915.635 | 366.4 | 2835.0 |
| gutch | PASS | 26.360 | 1.652 | 0.707 | 913.570 | 143.5 | 2797.1 |
| **Gutch relative** | - | 2.42x slower | 4.87x faster | 4.52x faster | 0.2% smaller | 60.8% smaller | 1.3% smaller |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | borg | gutch |
|---|---:|---:|
| Initial capture s | 5.465 (5.465–5.465; n=1) | 12.923 (12.923–12.923; n=1) |
| Later-version capture s | 5.409 (5.409–5.409; n=1) | 13.437 (13.437–13.437; n=1) |
| Later-version stored growth bytes | 438680720.000 (438680720.000–438680720.000; n=1) | 437891774.000 (437891774.000–437891774.000; n=1) |
| Restore + independent validation s | 11.204 (11.204–11.204; n=1) | 4.720 (4.720–4.720; n=1) |
| Content repair + validation s | 6.305 (6.305–6.305; n=1) | 3.785 (3.785–3.785; n=1) |
| Preserved-mtime repair + validation s | - | 3.798 (3.798–3.798; n=1) |
| Extra-file cleanup + validation s | - | 3.450 (3.450–3.450; n=1) |
| Full restore recovery + validation s | 11.220 (11.220–11.220; n=1) | 4.733 (4.733–4.733; n=1) |

borg: exact_recovery: UNSUPPORTED: no native extra-file deletion in this adapter; hidden_repair: UNSUPPORTED: native resume trusts size and mtime

[Source: Gutch vs bpt](reports/2026-10-31/41212694831-1/bpt.json)

### Gutch vs BuildPatchTool (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB | Peak RAM MiB | Peak disk MiB |
|---|---|---:|---:|---:|---:|---:|---:|
| buildpatchtool | PASS | 36.512 | 28.114 | 2.261 | 732.343 | 520.7 | 2615.8 |
| gutch | PASS | 4.580 | 1.924 | 1.024 | 689.361 | 155.4 | 2572.9 |
| **Gutch relative** | - | 7.97x faster | 14.61x faster | 2.21x faster | 5.9% smaller | 70.2% smaller | 1.6% smaller |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | buildpatchtool | gutch |
|---|---:|---:|
| Initial capture s | 13.548 (13.548–13.548; n=1) | 2.306 (2.306–2.306; n=1) |
| Later-version capture s | 22.965 (22.965–22.965; n=1) | 2.274 (2.274–2.274; n=1) |
| Later-version stored growth bytes | 344645846.000 (344645846.000–344645846.000; n=1) | 322167243.000 (322167243.000–322167243.000; n=1) |
| Restore + independent validation s | 31.724 (31.724–31.724; n=1) | 5.599 (5.599–5.599; n=1) |
| Content repair + validation s | 5.869 (5.869–5.869; n=1) | 4.660 (4.660–4.660; n=1) |
| Preserved-mtime repair + validation s | 5.807 (5.807–5.807; n=1) | 4.616 (4.616–4.616; n=1) |
| Extra-file cleanup + validation s | - | 4.142 (4.142–4.142; n=1) |
| Full restore recovery + validation s | 31.646 (31.646–31.646; n=1) | 5.587 (5.587–5.587; n=1) |

buildpatchtool: exact_recovery: UNSUPPORTED: no native extra-file deletion in this adapter

[Source: Gutch vs kopia](reports/2026-10-31/41212694831-1/kopia.json)

### Gutch vs Kopia (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB | Peak RAM MiB | Peak disk MiB |
|---|---|---:|---:|---:|---:|---:|---:|
| gutch | PASS | 5.390 | 1.356 | 0.788 | 1758.175 | 228.1 | 3641.7 |
| kopia | PASS | 4.549 | 9.682 | 5.116 | 1754.516 | 348.2 | 5392.1 |
| **Gutch relative** | - | 1.18x slower | 7.14x faster | 6.49x faster | 0.2% larger | 34.5% smaller | 32.5% smaller |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | gutch | kopia |
|---|---:|---:|
| Initial capture s | 2.740 (2.740–2.740; n=1) | 2.319 (2.319–2.319; n=1) |
| Later-version capture s | 2.650 (2.650–2.650; n=1) | 2.231 (2.231–2.231; n=1) |
| Later-version stored growth bytes | 887308595.000 (887308595.000–887308595.000; n=1) | 883228376.000 (883228376.000–883228376.000; n=1) |
| Restore + independent validation s | 5.082 (5.082–5.082; n=1) | 13.400 (13.400–13.400; n=1) |
| Content repair + validation s | 4.486 (4.486–4.486; n=1) | 8.806 (8.806–8.806; n=1) |
| Preserved-mtime repair + validation s | 4.416 (4.416–4.416; n=1) | 9.008 (9.008–9.008; n=1) |
| Extra-file cleanup + validation s | 4.171 (4.171–4.171; n=1) | 8.987 (8.987–8.987; n=1) |
| Full restore recovery + validation s | 5.058 (5.058–5.058; n=1) | 6.656 (6.656–6.656; n=1) |

[Source: Gutch vs plakar](reports/2026-10-31/41212694831-1/plakar.json)

### Gutch vs Plakar (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB | Peak RAM MiB | Peak disk MiB |
|---|---|---:|---:|---:|---:|---:|---:|
| gutch | PASS | 3.218 | 1.757 | 0.941 | 913.907 | 141.9 | 2797.4 |
| plakar | PASS | 12.714 | 6.835 | 6.919 | 916.023 | 423.4 | 2836.3 |
| **Gutch relative** | - | 3.95x faster | 3.89x faster | 7.35x faster | 0.2% smaller | 66.5% smaller | 1.4% smaller |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | gutch | plakar |
|---|---:|---:|
| Initial capture s | 1.655 (1.655–1.655; n=1) | 7.047 (7.047–7.047; n=1) |
| Later-version capture s | 1.563 (1.563–1.563; n=1) | 5.667 (5.667–5.667; n=1) |
| Later-version stored growth bytes | 438186069.000 (438186069.000–438186069.000; n=1) | 437728976.000 (437728976.000–437728976.000; n=1) |
| Restore + independent validation s | 5.473 (5.473–5.473; n=1) | 10.570 (10.570–10.570; n=1) |
| Content repair + validation s | 4.606 (4.606–4.606; n=1) | 10.722 (10.722–10.722; n=1) |
| Preserved-mtime repair + validation s | 4.615 (4.615–4.615; n=1) | 10.839 (10.839–10.839; n=1) |
| Extra-file cleanup + validation s | 4.217 (4.217–4.217; n=1) | - |
| Full restore recovery + validation s | 5.502 (5.502–5.502; n=1) | 9.316 (9.316–9.316; n=1) |

plakar: exact_recovery: UNSUPPORTED: no native extra-file deletion in this adapter

[Source: Gutch vs restic](reports/2026-10-31/41212694831-1/restic.json)

### Gutch vs Restic (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB | Peak RAM MiB | Peak disk MiB |
|---|---|---:|---:|---:|---:|---:|---:|
| gutch | PASS | 5.264 | 1.153 | 0.603 | 689.361 | 218.4 | 2572.9 |
| restic | PASS | 7.465 | 4.526 | 3.262 | 715.186 | 206.6 | 2602.7 |
| **Gutch relative** | - | 1.42x faster | 3.93x faster | 5.41x faster | 3.6% smaller | 5.7% larger | 1.1% smaller |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | gutch | restic |
|---|---:|---:|
| Initial capture s | 2.985 (2.985–2.985; n=1) | 3.863 (3.863–3.863; n=1) |
| Later-version capture s | 2.279 (2.279–2.279; n=1) | 3.603 (3.603–3.603; n=1) |
| Later-version stored growth bytes | 322167243.000 (322167243.000–322167243.000; n=1) | 332910924.000 (332910924.000–332910924.000; n=1) |
| Restore + independent validation s | 3.292 (3.292–3.292; n=1) | 6.631 (6.631–6.631; n=1) |
| Content repair + validation s | 2.681 (2.681–2.681; n=1) | 5.374 (5.374–5.374; n=1) |
| Preserved-mtime repair + validation s | 2.724 (2.724–2.724; n=1) | 5.880 (5.880–5.880; n=1) |
| Extra-file cleanup + validation s | 2.407 (2.407–2.407; n=1) | 5.289 (5.289–5.289; n=1) |
| Full restore recovery + validation s | 3.308 (3.308–3.308; n=1) | 6.576 (6.576–6.576; n=1) |

[Source: Gutch vs rustic](reports/2026-10-31/41212694831-1/rustic.json)

### Gutch vs Rustic (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB | Peak RAM MiB | Peak disk MiB |
|---|---|---:|---:|---:|---:|---:|---:|
| gutch | PASS | 6.625 | 1.736 | 0.817 | 689.361 | 169.2 | 2572.9 |
| rustic | PASS | 11.917 | 4.064 | 3.546 | 700.710 | 313.7 | 2585.9 |
| **Gutch relative** | - | 1.80x faster | 2.34x faster | 4.34x faster | 1.6% smaller | 46.1% smaller | 0.5% smaller |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | gutch | rustic |
|---|---:|---:|
| Initial capture s | 3.480 (3.480–3.480; n=1) | 6.287 (6.287–6.287; n=1) |
| Later-version capture s | 3.145 (3.145–3.145; n=1) | 5.630 (5.630–5.630; n=1) |
| Later-version stored growth bytes | 322167243.000 (322167243.000–322167243.000; n=1) | 327773412.000 (327773412.000–327773412.000; n=1) |
| Restore + independent validation s | 4.759 (4.759–4.759; n=1) | 7.121 (7.121–7.121; n=1) |
| Content repair + validation s | 3.804 (3.804–3.804; n=1) | 6.556 (6.556–6.556; n=1) |
| Preserved-mtime repair + validation s | 3.783 (3.783–3.783; n=1) | 6.544 (6.544–6.544; n=1) |
| Extra-file cleanup + validation s | 3.324 (3.324–3.324; n=1) | 6.434 (6.434–6.434; n=1) |
| Full restore recovery + validation s | 4.714 (4.714–4.714; n=1) | 7.224 (7.224–7.224; n=1) |

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
