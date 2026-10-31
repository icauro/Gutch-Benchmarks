# Gutch benchmarks

Compare Gutch against Borg, BuildPatchTool, Kopia, Plakar, Restic and Rustic
using shared Blender inputs, pair-specific settings and SHA-256 output validation.

![Latest per-pair benchmark comparisons](reports/comparison.svg?v=4768eb0be20c)

![Peak RAM by operation](reports/ram.svg?v=177867000b57)

![Peak disk by operation](reports/disk.svg?v=920140d60f8e)

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
Latest per pair · Linux · Blender 5.0.0 → 5.1.0 · 2026-10-31 · measurement contract 2

[This run's report](reports/2026-10-31/41218304728-1/README.md) · [Actions logs and artifacts](https://github.com/icauro/Gutch-Benchmarks/actions/runs/41218304728)

<details>
<summary>Detailed results and source reports</summary>

[Source: Gutch vs restic](reports/2026-10-31/41218304728-1/restic.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Restic](https://github.com/restic/restic) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.525 | 1.911 | 1.028 | 689.361 |
| [Restic](https://github.com/restic/restic) | PASS | 8.939 | 5.840 | 4.225 | 717.455 |
| **Gutch relative** | - | 1.98x faster | 3.06x faster | 4.11x faster | 3.9% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 140.7 | 382.1 | 131.2 | 689.4 | 131.2 | 2,572.9 | 116.0 | 2,572.9 |
| [Restic](https://github.com/restic/restic) | 196.9 | 398.1 | 193.0 | 716.9 | 110.7 | 2,600.4 | 63.0 | 2,600.4 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [Restic](https://github.com/restic/restic) |
|---|---:|---:|
| First capture s | 2.289 (2.289–2.289; n=1) | 4.540 (4.540–4.540; n=1) |
| Later-version capture s | 2.236 (2.236–2.236; n=1) | 4.399 (4.399–4.399; n=1) |
| Later-version stored growth bytes | 322167243.000 (322167243.000–322167243.000; n=1) | 335731784.000 (335731784.000–335731784.000; n=1) |
| Restore + independent validation s | 5.604 (5.604–5.604; n=1) | 9.474 (9.474–9.474; n=1) |
| Content repair + validation s | 4.671 (4.671–4.671; n=1) | 7.903 (7.903–7.903; n=1) |
| Preserved-mtime repair + validation s | 4.626 (4.626–4.626; n=1) | 7.804 (7.804–7.804; n=1) |
| Extra-file cleanup + validation s | 4.144 (4.144–4.144; n=1) | 7.628 (7.628–7.628; n=1) |
| Full restore recovery + validation s | 5.611 (5.611–5.611; n=1) | 9.526 (9.526–9.526; n=1) |

[Source: Gutch vs kopia](reports/2026-10-31/41218304728-1/kopia.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Kopia](https://github.com/kopia/kopia) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 10.462 | 0.963 | 0.628 | 1758.175 |
| [Kopia](https://github.com/kopia/kopia) | PASS | 9.861 | 17.341 | 10.450 | 1754.498 |
| **Gutch relative** | - | 1.06x slower | 18.02x faster | 16.64x faster | 0.2% larger |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 208.7 | 912.0 | 225.1 | 1,758.2 | 108.6 | 3,641.7 | 109.0 | 3,641.7 |
| [Kopia](https://github.com/kopia/kopia) | 241.7 | 912.9 | 219.2 | 1,755.9 | 240.5 | 5,392.1 | 227.6 | 5,392.1 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [Kopia](https://github.com/kopia/kopia) |
|---|---:|---:|
| First capture s | 5.301 (5.301–5.301; n=1) | 5.106 (5.106–5.106; n=1) |
| Later-version capture s | 5.161 (5.161–5.161; n=1) | 4.755 (4.755–4.755; n=1) |
| Later-version stored growth bytes | 887308595.000 (887308595.000–887308595.000; n=1) | 883223714.000 (883223714.000–883223714.000; n=1) |
| Restore + independent validation s | 3.623 (3.623–3.623; n=1) | 20.006 (20.006–20.006; n=1) |
| Content repair + validation s | 3.253 (3.253–3.253; n=1) | 13.135 (13.135–13.135; n=1) |
| Preserved-mtime repair + validation s | 3.216 (3.216–3.216; n=1) | 13.013 (13.013–13.013; n=1) |
| Extra-file cleanup + validation s | 3.041 (3.041–3.041; n=1) | 14.291 (14.291–14.291; n=1) |
| Full restore recovery + validation s | 3.625 (3.625–3.625; n=1) | 5.074 (5.074–5.074; n=1) |

[Source: Gutch vs borg](reports/2026-10-31/41218304728-1/borg.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Borg](https://github.com/borgbackup/borg) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 7.093 | 1.745 | 0.880 | 913.570 |
| [Borg](https://github.com/borgbackup/borg) | PASS | 11.321 | 9.861 | 3.602 | 916.128 |
| **Gutch relative** | - | 1.60x faster | 5.65x faster | 4.09x faster | 0.3% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 117.5 | 496.0 | 97.2 | 913.6 | 66.8 | 2,797.1 | 134.3 | 2,797.1 |
| [Borg](https://github.com/borgbackup/borg) | 253.1 | 533.2 | 242.5 | 952.5 | 343.6 | 2,800.5 | 290.4 | 2,836.1 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [Borg](https://github.com/borgbackup/borg) |
|---|---:|---:|
| First capture s | 3.528 (3.528–3.528; n=1) | 5.715 (5.715–5.715; n=1) |
| Later-version capture s | 3.565 (3.565–3.565; n=1) | 5.606 (5.606–5.606; n=1) |
| Later-version stored growth bytes | 437891774.000 (437891774.000–437891774.000; n=1) | 439122352.000 (439122352.000–439122352.000; n=1) |
| Restore + independent validation s | 5.432 (5.432–5.432; n=1) | 13.468 (13.468–13.468; n=1) |
| Content repair + validation s | 4.481 (4.481–4.481; n=1) | 7.186 (7.186–7.186; n=1) |
| Preserved-mtime repair + validation s | 4.416 (4.416–4.416; n=1) | - |
| Extra-file cleanup + validation s | 4.084 (4.084–4.084; n=1) | - |
| Full restore recovery + validation s | 5.418 (5.418–5.418; n=1) | 13.415 (13.415–13.415; n=1) |

borg: exact_recovery: UNSUPPORTED: no native extra-file deletion in this adapter; hidden_repair: UNSUPPORTED: native resume trusts size and mtime

[Source: Gutch vs rustic](reports/2026-10-31/41218304728-1/rustic.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Rustic](https://github.com/rustic-rs/rustic) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.487 | 1.906 | 1.020 | 689.361 |
| [Rustic](https://github.com/rustic-rs/rustic) | PASS | 14.735 | 5.621 | 4.208 | 701.205 |
| **Gutch relative** | - | 3.28x faster | 2.95x faster | 4.13x faster | 1.7% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 142.0 | 382.1 | 135.5 | 689.4 | 121.3 | 2,572.9 | 186.2 | 2,572.9 |
| [Rustic](https://github.com/rustic-rs/rustic) | 136.6 | 389.3 | 136.6 | 700.1 | 337.9 | 2,583.7 | 136.6 | 2,583.7 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [Rustic](https://github.com/rustic-rs/rustic) |
|---|---:|---:|
| First capture s | 2.275 (2.275–2.275; n=1) | 7.819 (7.819–7.819; n=1) |
| Later-version capture s | 2.213 (2.213–2.213; n=1) | 6.916 (6.916–6.916; n=1) |
| Later-version stored growth bytes | 322167243.000 (322167243.000–322167243.000; n=1) | 327885067.000 (327885067.000–327885067.000; n=1) |
| Restore + independent validation s | 5.576 (5.576–5.576; n=1) | 9.286 (9.286–9.286; n=1) |
| Content repair + validation s | 4.640 (4.640–4.640; n=1) | 7.872 (7.872–7.872; n=1) |
| Preserved-mtime repair + validation s | 4.598 (4.598–4.598; n=1) | 7.862 (7.862–7.862; n=1) |
| Extra-file cleanup + validation s | 4.120 (4.120–4.120; n=1) | 7.807 (7.807–7.807; n=1) |
| Full restore recovery + validation s | 5.582 (5.582–5.582; n=1) | 9.351 (9.351–9.351; n=1) |

[Source: Gutch vs plakar](reports/2026-10-31/41218304728-1/plakar.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Plakar](https://github.com/PlakarKorp/plakar) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 6.921 | 1.398 | 0.735 | 913.907 |
| [Plakar](https://github.com/PlakarKorp/plakar) | PASS | 11.476 | 5.327 | 14.778 | 916.557 |
| **Gutch relative** | - | 1.66x faster | 3.81x faster | 20.12x faster | 0.3% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 67.3 | 496.0 | 70.9 | 913.9 | 48.3 | 2,797.4 | 148.6 | 2,797.4 |
| [Plakar](https://github.com/PlakarKorp/plakar) | 336.7 | 678.0 | 330.1 | 1,076.2 | 417.3 | 2,818.9 | 422.2 | 2,952.2 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [Plakar](https://github.com/PlakarKorp/plakar) |
|---|---:|---:|
| First capture s | 3.599 (3.599–3.599; n=1) | 6.332 (6.332–6.332; n=1) |
| Later-version capture s | 3.323 (3.323–3.323; n=1) | 5.144 (5.144–5.144; n=1) |
| Later-version stored growth bytes | 438186069.000 (438186069.000–438186069.000; n=1) | 438225230.000 (438225230.000–438225230.000; n=1) |
| Restore + independent validation s | 4.091 (4.091–4.091; n=1) | 8.034 (8.034–8.034; n=1) |
| Content repair + validation s | 3.378 (3.378–3.378; n=1) | 17.492 (17.492–17.492; n=1) |
| Preserved-mtime repair + validation s | 3.396 (3.396–3.396; n=1) | 13.848 (13.848–13.848; n=1) |
| Extra-file cleanup + validation s | 3.148 (3.148–3.148; n=1) | - |
| Full restore recovery + validation s | 4.070 (4.070–4.070; n=1) | 6.799 (6.799–6.799; n=1) |

plakar: exact_recovery: UNSUPPORTED: no native extra-file deletion in this adapter

[Source: Gutch vs bpt](reports/2026-10-31/41218304728-1/bpt.json)

### [Gutch](https://github.com/icauro/Gutch) vs [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.487 | 1.914 | 1.008 | 689.361 |
| [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) | PASS | 36.714 | 28.158 | 2.278 | 732.343 |
| **Gutch relative** | - | 8.18x faster | 14.71x faster | 2.26x faster | 5.9% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 142.4 | 382.1 | 133.1 | 689.4 | 126.7 | 2,572.9 | 112.4 | 2,572.9 |
| [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) | 386.4 | 403.7 | 520.0 | 732.3 | 232.8 | 2,615.8 | 129.8 | 2,719.3 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) |
|---|---:|---:|
| First capture s | 2.256 (2.256–2.256; n=1) | 13.658 (13.658–13.658; n=1) |
| Later-version capture s | 2.231 (2.231–2.231; n=1) | 23.057 (23.057–23.057; n=1) |
| Later-version stored growth bytes | 322167243.000 (322167243.000–322167243.000; n=1) | 344645885.000 (344645885.000–344645885.000; n=1) |
| Restore + independent validation s | 5.621 (5.621–5.621; n=1) | 31.839 (31.839–31.839; n=1) |
| Content repair + validation s | 4.646 (4.646–4.646; n=1) | 5.886 (5.886–5.886; n=1) |
| Preserved-mtime repair + validation s | 4.605 (4.605–4.605; n=1) | 5.838 (5.838–5.838; n=1) |
| Extra-file cleanup + validation s | 4.146 (4.146–4.146; n=1) | - |
| Full restore recovery + validation s | 5.647 (5.647–5.647; n=1) | 32.226 (32.226–32.226; n=1) |

buildpatchtool: exact_recovery: UNSUPPORTED: no native extra-file deletion in this adapter

</details>

<!-- latest-benchmarks:end -->

<details>
<summary>Run on GitHub</summary>

Open **Actions > Manual Linux benchmarks > Run workflow**. Choose `all` or one
pair, the Gutch revision, and repetitions. Defaults: Ubuntu 24.04, all six pairs,
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
5.0.0 and 5.1.0 inputs if missing. Reports are written under `.artifacts/runs/`.
Local runs retain failed outputs unless `--discard-outputs` is selected.

</details>

See the [benchmark guide](docs/guide.md) for settings, custom inputs, recovery,
report interpretation and development instructions. Tool versions and checksums
are recorded in the [manifest](src/comparison_benchmark_suite/resources/tools.json).

[MIT licensed](LICENSE). External tools and workloads retain their own licenses;
see [third-party notices](docs/third-party-notices.md).
