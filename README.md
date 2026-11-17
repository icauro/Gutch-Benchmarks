# Gutch benchmarks

Compare Gutch against Borg, BuildPatchTool, Kopia, Plakar, Restic and Rustic
using shared Blender inputs, pair-specific settings and SHA-256 output validation.

![Latest per-pair benchmark comparisons](_docs/reports/comparison.svg?v=7c7132392672)

![Peak RAM by operation](_docs/reports/ram.svg?v=5d572c1400c0)

![Peak disk by operation](_docs/reports/disk.svg?v=f387322e60ed)

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

Kopia, Restic and Rustic require encryption, so Gutch also encrypts its repository
in those pairs. Earlier recorded runs left Gutch unencrypted. New runs separate damaged-file repair,
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
Latest per pair · Linux · Blender 5.0.0 → 5.1.0 · 2026-11-17 · measurement contract 2

[This run's report](_docs/reports/2026-11-17/44102400068-1/README.md) · [Actions logs and artifacts](https://github.com/icauro/Gutch-Benchmarks/actions/runs/44102400068)

<details>
<summary>Detailed results and source reports</summary>

[Source: Gutch vs restic](_docs/reports/2026-11-17/44102400068-1/restic.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Restic](https://github.com/restic/restic) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.640 | 1.371 | 0.759 | 689.362 |
| [Restic](https://github.com/restic/restic) | PASS | 8.500 | 5.036 | 3.783 | 714.621 |
| **Gutch relative** | - | 1.83x faster | 3.67x faster | 4.98x faster | 3.5% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 132.1 | 382.1 | 124.7 | 689.4 | 123.1 | 2,572.9 | 134.0 | 2,572.9 |
| [Restic](https://github.com/restic/restic) | 234.9 | 398.3 | 196.9 | 718.5 | 111.2 | 2,602.0 | 66.2 | 2,602.0 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [Restic](https://github.com/restic/restic) |
|---|---:|---:|
| First capture s | 2.346 (2.193–2.597; n=6) | 4.247 (4.164–5.119; n=6) |
| Later-version capture s | 2.200 (2.047–2.520; n=6) | 4.173 (3.957–4.362; n=6) |
| Later-version stored growth bytes | 322167321.000 (322167321.000–322167321.000; n=6) | 332748894.500 (331165047.000–333271878.000; n=6) |
| Restore + independent validation s | 4.148 (4.121–4.297; n=6) | 7.794 (7.721–7.829; n=6) |
| Content repair + validation s | 3.479 (3.451–3.517; n=6) | 6.534 (6.502–6.687; n=6) |
| Preserved-mtime repair + validation s | 3.483 (3.461–3.510; n=6) | 6.691 (6.568–6.769; n=6) |
| Extra-file cleanup + validation s | 3.151 (3.132–3.173; n=6) | 6.367 (6.317–6.415; n=6) |
| Full restore recovery + validation s | 4.158 (4.144–4.253; n=6) | 7.830 (7.728–7.878; n=6) |

[Source: Gutch vs kopia](_docs/reports/2026-11-17/44102400068-1/kopia.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Kopia](https://github.com/kopia/kopia) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 8.445 | 0.770 | 0.466 | 1758.176 |
| [Kopia](https://github.com/kopia/kopia) | PASS | 6.845 | 13.866 | 9.375 | 1754.518 |
| **Gutch relative** | - | 1.23x slower | 18.02x faster | 20.12x faster | 0.2% larger |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 196.2 | 912.0 | 205.1 | 1,758.2 | 86.9 | 3,641.7 | 110.7 | 3,641.7 |
| [Kopia](https://github.com/kopia/kopia) | 214.5 | 912.9 | 170.3 | 1,755.9 | 262.7 | 5,392.1 | 268.3 | 5,392.1 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [Kopia](https://github.com/kopia/kopia) |
|---|---:|---:|
| First capture s | 3.738 (2.985–4.146; n=6) | 2.907 (2.784–3.433; n=6) |
| Later-version capture s | 4.734 (3.954–5.002; n=6) | 3.955 (3.926–3.959; n=6) |
| Later-version stored growth bytes | 887308673.000 (887308673.000–887308673.000; n=6) | 883233865.000 (883223438.000–883239604.000; n=6) |
| Restore + independent validation s | 3.262 (3.253–3.268; n=6) | 16.382 (14.843–18.681; n=6) |
| Content repair + validation s | 2.943 (2.911–2.976; n=6) | 11.865 (10.622–13.163; n=6) |
| Preserved-mtime repair + validation s | 2.928 (2.898–2.948; n=6) | 10.630 (10.558–10.639; n=6) |
| Extra-file cleanup + validation s | 2.800 (2.768–2.829; n=6) | 10.604 (9.953–10.691; n=6) |
| Full restore recovery + validation s | 3.272 (3.217–3.291; n=6) | 4.705 (4.626–4.739; n=6) |

[Source: Gutch vs borg](_docs/reports/2026-11-17/44102400068-1/borg.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Borg](https://github.com/borgbackup/borg) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.545 | 1.164 | 0.545 | 913.570 |
| [Borg](https://github.com/borgbackup/borg) | PASS | 9.681 | 5.974 | 2.564 | 915.832 |
| **Gutch relative** | - | 2.13x faster | 5.13x faster | 4.70x faster | 0.2% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 108.4 | 496.0 | 121.4 | 913.6 | 68.3 | 2,797.1 | 133.7 | 2,797.1 |
| [Borg](https://github.com/borgbackup/borg) | 239.4 | 533.5 | 237.2 | 954.1 | 348.9 | 2,802.1 | 284.0 | 2,837.6 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [Borg](https://github.com/borgbackup/borg) |
|---|---:|---:|
| First capture s | 2.330 (1.392–2.337; n=6) | 4.840 (4.319–5.575; n=6) |
| Later-version capture s | 2.215 (1.979–2.262; n=6) | 4.842 (4.267–5.484; n=6) |
| Later-version stored growth bytes | 437891852.000 (437891852.000–437891852.000; n=6) | 438877551.500 (437630391.000–439549059.000; n=6) |
| Restore + independent validation s | 3.652 (3.635–3.693; n=6) | 8.437 (8.352–8.639; n=6) |
| Content repair + validation s | 2.996 (2.968–3.024; n=6) | 5.028 (4.974–5.151; n=6) |
| Preserved-mtime repair + validation s | 2.997 (2.974–3.025; n=6) | - |
| Extra-file cleanup + validation s | 2.810 (2.787–2.817; n=6) | - |
| Full restore recovery + validation s | 3.680 (3.627–3.748; n=6) | 8.402 (8.331–8.666; n=6) |

borg: exact_recovery: UNSUPPORTED: no native extra-file deletion in this adapter; hidden_repair: UNSUPPORTED: native resume trusts size and mtime

[Source: Gutch vs rustic](_docs/reports/2026-11-17/44102400068-1/rustic.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Rustic](https://github.com/rustic-rs/rustic) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.367 | 1.139 | 0.607 | 689.362 |
| [Rustic](https://github.com/rustic-rs/rustic) | PASS | 10.147 | 4.105 | 3.371 | 699.070 |
| **Gutch relative** | - | 2.32x faster | 3.60x faster | 5.55x faster | 1.4% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 130.6 | 382.1 | 131.6 | 689.4 | 122.3 | 2,572.9 | 162.2 | 2,572.9 |
| [Rustic](https://github.com/rustic-rs/rustic) | 136.6 | 388.9 | 136.6 | 700.9 | 318.7 | 2,584.4 | 136.6 | 2,584.4 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [Rustic](https://github.com/rustic-rs/rustic) |
|---|---:|---:|
| First capture s | 2.293 (2.065–2.391; n=6) | 5.440 (5.270–5.609; n=6) |
| Later-version capture s | 2.079 (2.052–2.183; n=6) | 4.689 (4.572–4.835; n=6) |
| Later-version stored growth bytes | 322167321.000 (322167321.000–322167321.000; n=6) | 326499429.000 (324300577.000–327692740.000; n=6) |
| Restore + independent validation s | 3.298 (3.223–3.330; n=6) | 6.289 (6.124–6.622; n=6) |
| Content repair + validation s | 2.737 (2.670–2.795; n=6) | 5.521 (5.384–5.626; n=6) |
| Preserved-mtime repair + validation s | 2.726 (2.689–2.785; n=6) | 5.523 (5.409–5.585; n=6) |
| Extra-file cleanup + validation s | 2.431 (2.399–2.514; n=6) | 5.406 (5.321–5.532; n=6) |
| Full restore recovery + validation s | 3.331 (3.306–3.371; n=6) | 6.312 (6.283–6.407; n=6) |

[Source: Gutch vs plakar](_docs/reports/2026-11-17/44102400068-1/plakar.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Plakar](https://github.com/PlakarKorp/plakar) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 3.762 | 1.164 | 0.571 | 913.908 |
| [Plakar](https://github.com/PlakarKorp/plakar) | PASS | 9.256 | 3.921 | 15.634 | 915.683 |
| **Gutch relative** | - | 2.46x faster | 3.37x faster | 27.38x faster | 0.2% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 67.6 | 496.0 | 87.2 | 913.9 | 49.4 | 2,797.4 | 117.9 | 2,797.4 |
| [Plakar](https://github.com/PlakarKorp/plakar) | 344.0 | 520.4 | 333.4 | 982.2 | 416.0 | 2,819.8 | 434.4 | 2,921.5 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [Plakar](https://github.com/PlakarKorp/plakar) |
|---|---:|---:|
| First capture s | 1.782 (1.143–2.376; n=6) | 5.665 (5.507–5.834; n=6) |
| Later-version capture s | 1.981 (1.914–1.983; n=6) | 3.583 (3.569–3.617; n=6) |
| Later-version stored growth bytes | 438186147.000 (438186147.000–438186147.000; n=6) | 438109563.500 (436344036.000–438614916.000; n=6) |
| Restore + independent validation s | 3.656 (3.627–3.675; n=6) | 6.427 (6.356–6.453; n=6) |
| Content repair + validation s | 3.031 (3.013–3.072; n=6) | 18.110 (13.634–18.464; n=6) |
| Preserved-mtime repair + validation s | 3.049 (3.029–3.059; n=6) | 10.553 (10.519–10.566; n=6) |
| Extra-file cleanup + validation s | 2.820 (2.765–2.825; n=6) | - |
| Full restore recovery + validation s | 3.647 (3.616–3.684; n=6) | 6.067 (5.992–6.141; n=6) |

plakar: exact_recovery: UNSUPPORTED: no native extra-file deletion in this adapter

[Source: Gutch vs bpt](_docs/reports/2026-11-17/44102400068-1/bpt.json)

### [Gutch](https://github.com/icauro/Gutch) vs [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 3.705 | 1.377 | 0.660 | 689.362 |
| [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) | PASS | 29.807 | 16.026 | 1.859 | 732.343 |
| **Gutch relative** | - | 8.05x faster | 11.63x faster | 2.82x faster | 5.9% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 137.6 | 382.1 | 134.8 | 689.4 | 125.1 | 2,572.9 | 149.0 | 2,572.9 |
| [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) | 387.1 | 403.7 | 515.0 | 732.3 | 228.2 | 2,615.8 | 130.5 | 2,615.8 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) |
|---|---:|---:|
| First capture s | 1.879 (1.788–1.917; n=6) | 10.912 (10.800–10.996; n=6) |
| Later-version capture s | 1.812 (1.720–1.948; n=6) | 18.898 (18.776–19.043; n=6) |
| Later-version stored growth bytes | 322167321.000 (322167321.000–322167321.000; n=6) | 344645859.500 (344645843.000–344645879.000; n=6) |
| Restore + independent validation s | 3.878 (3.771–3.932; n=6) | 18.468 (18.287–18.800; n=6) |
| Content repair + validation s | 3.137 (3.082–3.154; n=6) | 4.324 (4.261–4.354; n=6) |
| Preserved-mtime repair + validation s | 3.147 (3.090–3.198; n=6) | 4.243 (4.217–4.358; n=6) |
| Extra-file cleanup + validation s | 2.835 (2.762–2.866; n=6) | - |
| Full restore recovery + validation s | 3.914 (3.785–3.986; n=6) | 18.246 (18.103–18.397; n=6) |

buildpatchtool: exact_recovery: UNSUPPORTED: no native extra-file deletion in this adapter

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
