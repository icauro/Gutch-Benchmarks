# Gutch benchmarks

Compare Gutch against Borg, BuildPatchTool, Kopia, Plakar, Restic and Rustic
using shared Blender inputs, pair-specific settings and SHA-256 output validation.

![Latest per-pair benchmark comparisons](_docs/reports/comparison.svg?v=9afc8c21b7b6)

![Peak RAM by operation](_docs/reports/ram.svg?v=54fd10bd137b)

![Peak disk by operation](_docs/reports/disk.svg?v=1cd8c9deff53)

<details>
<summary>Comparison differences and limits</summary>

Each pair matches Gutch's settings to the other tool as closely as that tool allows.
Every pair processes the same files on one runner, and we check every restored file
with SHA-256. Numbers match the chart; cells read **Gutch / other tool**.

| # | Pair | Chunking | Compression | Encryption | Workers | Checks without timing |
|---|---|---|---|---|---|---|
| 1 | [Restic](https://github.com/restic/restic) | FastCDC 1 MiB / Rabin ~1 MiB | Zstd 3 / Zstd auto | AES-256 / AES-256 | 4 / 4 | — |
| 2 | [Kopia](https://github.com/kopia/kopia) | FastCDC 4 MiB / Buzhash 4 MiB | None / none | AES-256 / AES-256 | 4 / 4 | — |
| 3 | [Borg](https://github.com/borgbackup/borg) | FastCDC 2 MiB / FastCDC 2 MiB | LZ4 / LZ4 | None / authenticated only | 1\* / 1 | Extra-file cleanup, unchanged-timestamp repair |
| 4 | [Rustic](https://github.com/rustic-rs/rustic) | FastCDC / Rabin, both 256 KiB–1 MiB–4 MiB | Zstd 3 / Zstd 3 | AES-256 / AES-256 | 4 / 4 | — |
| 5 | [Plakar](https://github.com/PlakarKorp/plakar) | FastCDC 1 MiB / FastCDC ~1 MiB | LZ4 / LZ4 | None / none | 4 / 4 | Extra-file cleanup |
| 6 | [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) | FastCDC 1 MiB / fixed 1 MiB window | Zstd 3 / built-in | None / none | 4 / native | Extra-file cleanup |
| 7 | [Encrypted Gutch](https://github.com/icauro/Gutch) | Identical | Identical | None / AES-256 | 4 / 4 | — |

\* Gutch runs one worker in the Borg pair (marked **Gutch\*** in the charts) to match
single-threaded Borg; every other pair gives Gutch four.

**What the table cannot show**

1. **Restic:** "auto" is close to, but not exactly, Zstd level 3. Restic's chunk
   bounds are fixed at 512 KiB / 8 MiB, while Gutch's 1 MiB preset uses 256 KiB / 4 MiB.
2. **Kopia:** Gutch uses 16 MiB bundles here (8 MiB elsewhere) to suit 4 MiB chunks.
3. **Borg:** Borg 2 (a prerelease) is needed for FastCDC. Its resume trusts file size
   and modification time, so it cannot find damage that keeps both; that check is
   skipped. Borg is single-threaded by design, so Gutch also runs one worker here.
4. **Rustic:** Both use 8 MiB packs, but Gutch compresses whole bundles while Rustic
   compresses each chunk, so compression work still differs.
5. **Plakar:** Restores write over existing files, while Gutch repairs only damaged
   content, so the recovery commands do different work.
6. **BuildPatchTool:** A chunk window is not a content-defined average, and its codec
   and format do not match. Recovery uses a previous installation manifest, so this
   compares two delivery workflows. Its source requires
   [Epic-authorized access](https://dev.epicgames.com/documentation/unreal-engine/downloading-source-code-in-unreal-engine).
7. **Encrypted Gutch:** Not a competitor. The same release runs with and without
   encryption on one runner, so the ratio shows only what encryption costs.

Even with matched targets, different chunking methods split files at different
places, so deduplication and stored size differ. Reports before 2026-11-17 left
Gutch unencrypted in the Restic, Kopia and Rustic pairs, ran Restic restores with
`--verify`, gave Rustic 512 KiB / 8 MiB chunk bounds, and ran Gutch with four workers
against Borg. Pinned tool versions are in
[the tool manifest](src/comparison_benchmark_suite/resources/tools.json).

**How to read the numbers**

- **Timing:** chart times include each tool's own checks. Detailed reports add timings
  with our shared validation and the range across samples.
- **Repetitions:** six measured runs per pair after one warm-up, in alternating order.
  OS caches are not reset, and metadata handling and write flushing still differ.
- **Recovery:** damaged-file repair, damage with unchanged timestamps, extra-file
  cleanup and full restoration are timed separately. Checks a tool cannot do are
  marked unsupported and get no timing.
- **Hardware:** GitHub assigns runners with different CPUs, so compare ratios within a
  pair, not seconds across pairs or runs.
- **RAM and disk charts:** peaks per command, in MiB, from a separate monitored pass.
  Disk includes existing repository, cache and output files, not bytes written. RAM
  includes child processes. Sampling may miss short spikes. Older reports without
  per-command samples show `—`.
- **History:** older reports keep their original settings. A single local smoke run
  checks compatibility only.

</details>

<!-- latest-benchmarks:start -->
Latest per pair · Linux · Blender 5.0.0 → 5.1.0 · 2026-11-17 · measurement contract 2

[This run's report](_docs/reports/2026-11-17/44122579900-1/README.md) · [Actions logs and artifacts](https://github.com/icauro/Gutch-Benchmarks/actions/runs/44122579900)

<details>
<summary>Detailed results and source reports</summary>

[Source: Gutch vs restic](_docs/reports/2026-11-17/44122579900-1/restic.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Restic](https://github.com/restic/restic) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 3.922 | 1.701 | 0.913 | 687.209 |
| [Restic](https://github.com/restic/restic) | PASS | 7.616 | 4.873 | 3.483 | 714.965 |
| **Gutch relative** | - | 1.94x faster | 2.87x faster | 3.82x faster | 3.9% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 113.4 | 383.0 | 167.3 | 686.9 | 162.3 | 2,570.4 | 162.8 | 2,570.4 |
| [Restic](https://github.com/restic/restic) | 198.1 | 398.5 | 198.5 | 720.5 | 114.8 | 2,604.0 | 67.1 | 2,604.0 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [Restic](https://github.com/restic/restic) |
|---|---:|---:|
| First capture s | 1.995 (1.920–2.049; n=6) | 3.876 (3.846–3.905; n=6) |
| Later-version capture s | 1.925 (1.887–2.000; n=6) | 3.745 (3.709–3.801; n=6) |
| Later-version stored growth bytes | 320022514.000 (318702640.000–321288712.000; n=6) | 333116459.500 (330742139.000–335103047.000; n=6) |
| Restore + independent validation s | 4.191 (4.154–4.221; n=6) | 7.338 (7.324–7.395; n=6) |
| Content repair + validation s | 3.381 (3.351–3.443; n=6) | 5.978 (5.963–6.024; n=6) |
| Preserved-mtime repair + validation s | 3.396 (3.363–3.449; n=6) | 5.945 (5.917–5.971; n=6) |
| Extra-file cleanup + validation s | 3.025 (3.014–3.066; n=6) | 5.775 (5.761–5.792; n=6) |
| Full restore recovery + validation s | 4.216 (4.159–4.249; n=6) | 7.364 (7.331–7.398; n=6) |

[Source: Gutch vs kopia](_docs/reports/2026-11-17/44122579900-1/kopia.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Kopia](https://github.com/kopia/kopia) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 5.745 | 1.783 | 1.103 | 1761.518 |
| [Kopia](https://github.com/kopia/kopia) | PASS | 4.607 | 8.640 | 6.206 | 1754.523 |
| **Gutch relative** | - | 1.25x slower | 4.85x faster | 5.63x faster | 0.4% larger |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 211.0 | 912.0 | 198.0 | 1,761.6 | 104.8 | 3,645.1 | 114.5 | 3,645.1 |
| [Kopia](https://github.com/kopia/kopia) | 171.4 | 912.9 | 171.1 | 1,755.9 | 293.2 | 5,392.1 | 289.1 | 5,392.1 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [Kopia](https://github.com/kopia/kopia) |
|---|---:|---:|
| First capture s | 2.926 (2.889–2.967; n=6) | 2.374 (2.349–2.436; n=6) |
| Later-version capture s | 2.808 (2.802–2.860; n=6) | 2.208 (2.164–2.495; n=6) |
| Later-version stored growth bytes | 890793606.000 (887901631.000–895661585.000; n=6) | 883236298.000 (883228132.000–883249192.000; n=6) |
| Restore + independent validation s | 5.607 (5.562–5.767; n=6) | 12.449 (11.121–13.750; n=6) |
| Content repair + validation s | 4.884 (4.829–5.059; n=6) | 10.037 (8.918–11.197; n=6) |
| Preserved-mtime repair + validation s | 4.844 (4.807–4.930; n=6) | 9.211 (9.146–9.447; n=6) |
| Extra-file cleanup + validation s | 4.563 (4.524–4.746; n=6) | 9.185 (9.117–9.336; n=6) |
| Full restore recovery + validation s | 5.636 (5.616–5.962; n=6) | 7.243 (6.943–7.302; n=6) |

[Source: Gutch vs borg](_docs/reports/2026-11-17/44122579900-1/borg.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Borg](https://github.com/borgbackup/borg) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 6.863 | 1.585 | 0.810 | 913.570 |
| [Borg](https://github.com/borgbackup/borg) | PASS | 13.059 | 9.743 | 3.971 | 916.433 |
| **Gutch relative** | - | 1.90x faster | 6.15x faster | 4.90x faster | 0.3% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 108.2 | 496.0 | 117.6 | 913.6 | 68.5 | 2,797.1 | 111.4 | 2,797.1 |
| [Borg](https://github.com/borgbackup/borg) | 243.9 | 533.6 | 236.9 | 953.0 | 342.3 | 2,800.9 | 241.7 | 2,836.5 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [Borg](https://github.com/borgbackup/borg) |
|---|---:|---:|
| First capture s | 3.411 (1.618–3.494; n=6) | 6.520 (5.642–7.363; n=6) |
| Later-version capture s | 3.452 (1.514–3.591; n=6) | 6.540 (5.609–7.412; n=6) |
| Later-version stored growth bytes | 437891852.000 (437891852.000–437891852.000; n=6) | 439504667.000 (439126847.000–440271293.000; n=6) |
| Restore + independent validation s | 5.314 (5.288–5.354; n=6) | 13.450 (13.178–14.623; n=6) |
| Content repair + validation s | 4.501 (4.473–4.521; n=6) | 7.624 (7.246–7.970; n=6) |
| Preserved-mtime repair + validation s | 4.477 (4.422–4.495; n=6) | - |
| Extra-file cleanup + validation s | 4.175 (4.146–4.187; n=6) | - |
| Full restore recovery + validation s | 5.332 (5.283–5.444; n=6) | 13.334 (13.145–13.586; n=6) |

borg: exact_recovery: UNSUPPORTED: no native extra-file deletion in this adapter; hidden_repair: UNSUPPORTED: native resume trusts size and mtime

[Source: Gutch vs rustic](_docs/reports/2026-11-17/44122579900-1/rustic.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Rustic](https://github.com/rustic-rs/rustic) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.875 | 2.299 | 1.359 | 688.435 |
| [Rustic](https://github.com/rustic-rs/rustic) | PASS | 14.610 | 5.594 | 4.475 | 699.401 |
| **Gutch relative** | - | 3.00x faster | 2.43x faster | 3.29x faster | 1.6% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 143.3 | 382.4 | 174.8 | 688.0 | 165.6 | 2,571.5 | 150.5 | 2,571.5 |
| [Rustic](https://github.com/rustic-rs/rustic) | 136.6 | 388.9 | 136.6 | 702.7 | 335.7 | 2,586.2 | 136.6 | 2,586.2 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [Rustic](https://github.com/rustic-rs/rustic) |
|---|---:|---:|
| First capture s | 2.456 (2.366–2.490; n=6) | 7.847 (7.729–7.889; n=6) |
| Later-version capture s | 2.391 (2.371–2.537; n=6) | 6.791 (6.662–6.875; n=6) |
| Later-version stored growth bytes | 321229415.000 (320314929.000–321696751.000; n=6) | 325943576.000 (323597610.000–329084058.000; n=6) |
| Restore + independent validation s | 5.816 (5.811–5.885; n=6) | 9.115 (9.059–9.197; n=6) |
| Content repair + validation s | 4.872 (4.841–4.890; n=6) | 7.978 (7.965–8.013; n=6) |
| Preserved-mtime repair + validation s | 4.829 (4.810–4.884; n=6) | 7.959 (7.922–7.988; n=6) |
| Extra-file cleanup + validation s | 4.319 (4.316–4.337; n=6) | 7.896 (7.877–7.914; n=6) |
| Full restore recovery + validation s | 5.864 (5.816–5.904; n=6) | 9.181 (9.075–9.502; n=6) |

[Source: Gutch vs plakar](_docs/reports/2026-11-17/44122579900-1/plakar.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Plakar](https://github.com/PlakarKorp/plakar) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 5.621 | 1.248 | 0.684 | 913.908 |
| [Plakar](https://github.com/PlakarKorp/plakar) | PASS | 11.479 | 5.062 | 17.346 | 916.405 |
| **Gutch relative** | - | 2.04x faster | 4.06x faster | 25.37x faster | 0.3% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 72.2 | 496.5 | 72.9 | 913.9 | 50.3 | 2,797.4 | 133.2 | 2,797.4 |
| [Plakar](https://github.com/PlakarKorp/plakar) | 343.1 | 534.5 | 337.3 | 1,008.9 | 421.5 | 2,818.0 | 408.4 | 2,818.0 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [Plakar](https://github.com/PlakarKorp/plakar) |
|---|---:|---:|
| First capture s | 2.924 (2.784–3.184; n=6) | 6.402 (5.907–8.707; n=6) |
| Later-version capture s | 2.702 (2.689–2.772; n=6) | 4.970 (4.751–5.147; n=6) |
| Later-version stored growth bytes | 438186147.000 (438186147.000–438186147.000; n=6) | 438000987.000 (437375429.000–439298198.000; n=6) |
| Restore + independent validation s | 4.002 (3.956–4.034; n=6) | 7.855 (7.736–8.115; n=6) |
| Content repair + validation s | 3.391 (3.367–3.444; n=6) | 20.112 (15.157–21.703; n=6) |
| Preserved-mtime repair + validation s | 3.384 (3.365–3.417; n=6) | 13.802 (13.512–14.837; n=6) |
| Extra-file cleanup + validation s | 3.123 (3.105–3.185; n=6) | - |
| Full restore recovery + validation s | 4.000 (3.964–4.053; n=6) | 6.881 (6.764–7.074; n=6) |

plakar: exact_recovery: UNSUPPORTED: no native extra-file deletion in this adapter

[Source: Gutch vs bpt](_docs/reports/2026-11-17/44122579900-1/bpt.json)

### [Gutch](https://github.com/icauro/Gutch) vs [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.688 | 1.877 | 0.993 | 689.362 |
| [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) | PASS | 37.011 | 29.150 | 2.295 | 732.343 |
| **Gutch relative** | - | 7.89x faster | 15.53x faster | 2.31x faster | 5.9% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 134.5 | 382.1 | 131.8 | 689.4 | 131.3 | 2,572.9 | 130.7 | 2,572.9 |
| [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) | 386.1 | 403.7 | 556.8 | 732.3 | 230.0 | 2,615.8 | 130.1 | 2,704.9 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) |
|---|---:|---:|
| First capture s | 2.389 (2.363–2.470; n=6) | 13.610 (13.522–13.724; n=6) |
| Later-version capture s | 2.301 (2.287–2.378; n=6) | 23.362 (23.326–23.425; n=6) |
| Later-version stored growth bytes | 322167321.000 (322167321.000–322167321.000; n=6) | 344645856.000 (344645852.000–344645873.000; n=6) |
| Restore + independent validation s | 5.671 (5.631–5.708; n=6) | 32.876 (32.696–33.208; n=6) |
| Content repair + validation s | 4.764 (4.677–4.782; n=6) | 6.027 (5.965–6.075; n=6) |
| Preserved-mtime repair + validation s | 4.700 (4.652–4.726; n=6) | 6.028 (5.964–6.044; n=6) |
| Extra-file cleanup + validation s | 4.250 (4.195–4.286; n=6) | - |
| Full restore recovery + validation s | 5.704 (5.612–5.721; n=6) | 32.869 (32.752–33.068; n=6) |

buildpatchtool: exact_recovery: UNSUPPORTED: no native extra-file deletion in this adapter

</details>

<!-- latest-benchmarks:end -->

<details>
<summary>Run on GitHub</summary>

Open **Actions > Manual Linux benchmarks > Run workflow**. Choose `all` or one
pair, a Gutch release, and repetitions. Defaults: Ubuntu 24.04, all seven pairs
(six tools plus the Gutch encryption-cost pair),
one warm-up and six measured repetitions.
All pairs can run concurrently, each on its own runner.

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
