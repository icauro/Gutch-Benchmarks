# Gutch benchmarks

Compare Gutch against Borg, BuildPatchTool, Kopia, Plakar, Restic and Rustic
using shared Blender inputs, pair-specific settings and SHA-256 output validation.

![Latest per-pair benchmark comparisons](reports/comparison.svg)

![Peak resources by operation](reports/resources.svg)

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

The second SVG uses the same paired bars and comparison rows, with eight
RAM/disk columns in MiB from a separate monitored pass. Text versions
remain below each pair in the details. The latest saved run has command-level RAM samples
but only a whole-workflow disk peak, so per-operation disk cells show `—`.
Whole-workflow peaks are not substituted for missing command measurements.
Sampling may miss short spikes; RAM includes child processes.

</details>

<!-- latest-benchmarks:start -->
Latest per pair · Linux · Blender 5.0.0 → 5.1.0 · 2026-10-31 · measurement contract 2

[This run's report](reports/2026-10-31/41215100958-1/README.md) · [Actions logs and artifacts](https://github.com/icauro/Gutch-Benchmarks/actions/runs/41215100958)

Lower values are better. Pair settings differ; bars scale independently within each cell.
Hosted-runner timings are indicative; OS caches are uncontrolled.

<details>
<summary>Detailed results and source reports</summary>

[Source: Gutch vs borg](reports/2026-10-31/41215100958-1/borg.json)

### Gutch vs Borg (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| borg | PASS | 11.478 | 9.888 | 3.724 | 916.703 |
| gutch | PASS | 7.071 | 1.758 | 0.883 | 913.570 |
| **Gutch relative** | - | 1.62x faster | 5.62x faster | 4.22x faster | 0.3% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gutch | 103.5 | — | 96.7 | — | 69.9 | — | 127.4 | — |
| borg | 251.9 | — | 245.2 | — | 346.5 | — | 282.3 | — |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | borg | gutch |
|---|---:|---:|
| First capture s | 5.781 (5.781–5.781; n=1) | 3.543 (3.543–3.543; n=1) |
| Later-version capture s | 5.697 (5.697–5.697; n=1) | 3.528 (3.528–3.528; n=1) |
| Later-version stored growth bytes | 439779527.000 (439779527.000–439779527.000; n=1) | 437891774.000 (437891774.000–437891774.000; n=1) |
| Restore + independent validation s | 13.511 (13.511–13.511; n=1) | 5.515 (5.515–5.515; n=1) |
| Content repair + validation s | 7.306 (7.306–7.306; n=1) | 4.475 (4.475–4.475; n=1) |
| Preserved-mtime repair + validation s | - | 4.421 (4.421–4.421; n=1) |
| Extra-file cleanup + validation s | - | 4.093 (4.093–4.093; n=1) |
| Full restore recovery + validation s | 13.568 (13.568–13.568; n=1) | 5.426 (5.426–5.426; n=1) |

borg: exact_recovery: UNSUPPORTED: no native extra-file deletion in this adapter; hidden_repair: UNSUPPORTED: native resume trusts size and mtime

[Source: Gutch vs bpt](reports/2026-10-31/41215100958-1/bpt.json)

### Gutch vs BuildPatchTool (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| buildpatchtool | PASS | 36.828 | 28.176 | 2.237 | 732.343 |
| gutch | PASS | 4.539 | 1.910 | 1.020 | 689.361 |
| **Gutch relative** | - | 8.11x faster | 14.75x faster | 2.19x faster | 5.9% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gutch | 140.2 | — | 132.9 | — | 124.4 | — | 140.3 | — |
| buildpatchtool | 383.0 | — | 520.7 | — | 228.9 | — | 131.5 | — |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | buildpatchtool | gutch |
|---|---:|---:|
| First capture s | 13.503 (13.503–13.503; n=1) | 2.311 (2.311–2.311; n=1) |
| Later-version capture s | 23.325 (23.325–23.325; n=1) | 2.228 (2.228–2.228; n=1) |
| Later-version stored growth bytes | 344645850.000 (344645850.000–344645850.000; n=1) | 322167243.000 (322167243.000–322167243.000; n=1) |
| Restore + independent validation s | 31.828 (31.828–31.828; n=1) | 5.606 (5.606–5.606; n=1) |
| Content repair + validation s | 5.897 (5.897–5.897; n=1) | 4.669 (4.669–4.669; n=1) |
| Preserved-mtime repair + validation s | 5.890 (5.890–5.890; n=1) | 4.640 (4.640–4.640; n=1) |
| Extra-file cleanup + validation s | - | 4.160 (4.160–4.160; n=1) |
| Full restore recovery + validation s | 31.873 (31.873–31.873; n=1) | 5.620 (5.620–5.620; n=1) |

buildpatchtool: exact_recovery: UNSUPPORTED: no native extra-file deletion in this adapter

[Source: Gutch vs kopia](reports/2026-10-31/41215100958-1/kopia.json)

### Gutch vs Kopia (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| gutch | PASS | 5.411 | 1.430 | 0.784 | 1758.175 |
| kopia | PASS | 4.642 | 8.080 | 5.120 | 1754.512 |
| **Gutch relative** | - | 1.17x slower | 5.65x faster | 6.53x faster | 0.2% larger |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gutch | 223.9 | — | 241.0 | — | 110.3 | — | 153.7 | — |
| kopia | 186.6 | — | 172.3 | — | 251.8 | — | 295.8 | — |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | gutch | kopia |
|---|---:|---:|
| First capture s | 2.734 (2.734–2.734; n=1) | 2.398 (2.398–2.398; n=1) |
| Later-version capture s | 2.677 (2.677–2.677; n=1) | 2.244 (2.244–2.244; n=1) |
| Later-version stored growth bytes | 887308595.000 (887308595.000–887308595.000; n=1) | 883237091.000 (883237091.000–883237091.000; n=1) |
| Restore + independent validation s | 5.175 (5.175–5.175; n=1) | 11.777 (11.777–11.777; n=1) |
| Content repair + validation s | 4.452 (4.452–4.452; n=1) | 8.796 (8.796–8.796; n=1) |
| Preserved-mtime repair + validation s | 4.443 (4.443–4.443; n=1) | 8.809 (8.809–8.809; n=1) |
| Extra-file cleanup + validation s | 4.180 (4.180–4.180; n=1) | 8.998 (8.998–8.998; n=1) |
| Full restore recovery + validation s | 5.038 (5.038–5.038; n=1) | 6.606 (6.606–6.606; n=1) |

[Source: Gutch vs plakar](reports/2026-10-31/41215100958-1/plakar.json)

### Gutch vs Plakar (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| gutch | PASS | 6.653 | 1.377 | 0.716 | 913.907 |
| plakar | PASS | 11.288 | 5.009 | 13.025 | 916.329 |
| **Gutch relative** | - | 1.70x faster | 3.64x faster | 18.19x faster | 0.3% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gutch | 72.4 | — | 70.3 | — | 48.5 | — | 182.6 | — |
| plakar | 334.2 | — | 338.7 | — | 416.3 | — | 392.1 | — |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | gutch | plakar |
|---|---:|---:|
| First capture s | 3.406 (3.406–3.406; n=1) | 6.221 (6.221–6.221; n=1) |
| Later-version capture s | 3.247 (3.247–3.247; n=1) | 5.067 (5.067–5.067; n=1) |
| Later-version stored growth bytes | 438186069.000 (438186069.000–438186069.000; n=1) | 438096892.000 (438096892.000–438096892.000; n=1) |
| Restore + independent validation s | 4.055 (4.055–4.055; n=1) | 7.711 (7.711–7.711; n=1) |
| Content repair + validation s | 3.350 (3.350–3.350; n=1) | 15.730 (15.730–15.730; n=1) |
| Preserved-mtime repair + validation s | 3.349 (3.349–3.349; n=1) | 14.098 (14.098–14.098; n=1) |
| Extra-file cleanup + validation s | 3.080 (3.080–3.080; n=1) | - |
| Full restore recovery + validation s | 4.055 (4.055–4.055; n=1) | 6.732 (6.732–6.732; n=1) |

plakar: exact_recovery: UNSUPPORTED: no native extra-file deletion in this adapter

[Source: Gutch vs restic](reports/2026-10-31/41215100958-1/restic.json)

### Gutch vs Restic (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| gutch | PASS | 5.263 | 1.156 | 0.605 | 689.361 |
| restic | PASS | 7.144 | 4.255 | 3.167 | 714.022 |
| **Gutch relative** | - | 1.36x faster | 3.68x faster | 5.24x faster | 3.5% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gutch | 144.1 | — | 133.8 | — | 129.4 | — | 127.3 | — |
| restic | 204.0 | — | 207.5 | — | 120.3 | — | 66.8 | — |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | gutch | restic |
|---|---:|---:|
| First capture s | 2.813 (2.813–2.813; n=1) | 3.683 (3.683–3.683; n=1) |
| Later-version capture s | 2.450 (2.450–2.450; n=1) | 3.462 (3.462–3.462; n=1) |
| Later-version stored growth bytes | 322167243.000 (322167243.000–322167243.000; n=1) | 332225646.000 (332225646.000–332225646.000; n=1) |
| Restore + independent validation s | 3.211 (3.211–3.211; n=1) | 6.340 (6.340–6.340; n=1) |
| Content repair + validation s | 2.700 (2.700–2.700; n=1) | 5.228 (5.228–5.228; n=1) |
| Preserved-mtime repair + validation s | 2.800 (2.800–2.800; n=1) | 5.509 (5.509–5.509; n=1) |
| Extra-file cleanup + validation s | 2.414 (2.414–2.414; n=1) | 4.946 (4.946–4.946; n=1) |
| Full restore recovery + validation s | 3.319 (3.319–3.319; n=1) | 6.300 (6.300–6.300; n=1) |

[Source: Gutch vs rustic](reports/2026-10-31/41215100958-1/rustic.json)

### Gutch vs Rustic (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| gutch | PASS | 5.675 | 1.297 | 0.631 | 689.361 |
| rustic | PASS | 10.424 | 4.161 | 3.384 | 700.552 |
| **Gutch relative** | - | 1.84x faster | 3.21x faster | 5.36x faster | 1.6% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gutch | 137.4 | — | 131.1 | — | 136.6 | — | 196.7 | — |
| rustic | 136.6 | — | 136.6 | — | 299.3 | — | 136.6 | — |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | gutch | rustic |
|---|---:|---:|
| First capture s | 3.040 (3.040–3.040; n=1) | 5.560 (5.560–5.560; n=1) |
| Later-version capture s | 2.635 (2.635–2.635; n=1) | 4.864 (4.864–4.864; n=1) |
| Later-version stored growth bytes | 322167243.000 (322167243.000–322167243.000; n=1) | 327162415.000 (327162415.000–327162415.000; n=1) |
| Restore + independent validation s | 3.481 (3.481–3.481; n=1) | 6.462 (6.462–6.462; n=1) |
| Content repair + validation s | 2.790 (2.790–2.790; n=1) | 5.589 (5.589–5.589; n=1) |
| Preserved-mtime repair + validation s | 2.805 (2.805–2.805; n=1) | 5.623 (5.623–5.623; n=1) |
| Extra-file cleanup + validation s | 2.472 (2.472–2.472; n=1) | 5.627 (5.627–5.627; n=1) |
| Full restore recovery + validation s | 3.339 (3.339–3.339; n=1) | 6.537 (6.537–6.537; n=1) |

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
