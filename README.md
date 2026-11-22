# Gutch benchmarks

Reproducible benchmarks for [Gutch](https://github.com/icauro/Gutch), a fast
deduplicating store and installer. In the latest run Gutch installs 2.2–4.6×
faster than Restic, Kopia, Borg, Rustic and Plakar, and repairs 2.3–8× faster
than the first four. Against Plakar, whose repair rewrites every file, the
repair is 29× faster, but a fresh Plakar restore takes only 1.6× longer than
Gutch's. Gutch captures faster in four pairs and 1.2× slower than Kopia. It
stores up to 3.7% less, except 0.2% more than Kopia.

Each pair compares Gutch against Borg, BuildPatchTool, CAVS, Kopia, Plakar, Restic
or Rustic using shared Blender inputs, pair-specific settings and SHA-256 output
validation.

![Latest per-pair benchmark comparisons](_docs/reports/comparison.svg?v=b48664a3b31f)

![Peak RAM by operation](_docs/reports/ram.svg?v=20cf3b887bd2)

![Peak disk by operation](_docs/reports/disk.svg?v=562cf1701016)

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
| 5 | [Plakar](https://github.com/PlakarKorp/plakar) | FastCDC 1 MiB / FastCDC ~1 MiB | LZ4 / LZ4 | None / none | 4 / 4 | — |
| 6 | [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) | FastCDC 1 MiB / fixed 1 MiB window | Zstd 3 / built-in | None / none | 4 / native | Extra-file cleanup |
| 7 | [CAVS](https://github.com/terragov/cavs) | FastCDC / FastCDC, both 64 KiB–256 KiB–1 MiB | Zstd 3 / Zstd 3 | None / none | 4 / 4 | Extra-file cleanup |
| 8 | [Encrypted Gutch](https://github.com/icauro/Gutch) | Identical | Identical | None / AES-256 | 4 / 4 | — |

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
5. **Plakar:** Plakar cannot remove files that are not in a snapshot, so its
   recovery deletes the build's folder and restores it whole; the timing includes
   the delete. Gutch repairs only damaged content. Reports up to 2026-11-17 instead
   restored over the existing folder and skipped extra-file cleanup.
6. **BuildPatchTool:** A chunk window is not a content-defined average, and its codec
   and format do not match. Recovery uses a previous installation manifest, so this
   compares two delivery workflows. Its source requires
   [Epic-authorized access](https://dev.epicgames.com/documentation/unreal-engine/downloading-source-code-in-unreal-engine).
7. **CAVS:** A delivery tool like BuildPatchTool, with far fewer users than the other
   peers. Capture packs each build and adds it to a packfile store; installs fetch from
   a local `cavs-server` with an empty client cache. The server's RAM is added to every
   restore and repair command's RAM, since each fetch depends on it. Gutch compresses whole bundles while CAVS compresses each chunk. CAVS
   repairs by checking every file's SHA-256, but skips its `--prune` cleanup when all
   files already match, so extra-file cleanup is marked unsupported.
8. **Encrypted Gutch:** Not a competitor. The same release runs with and without
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
  OS caches are not reset unless a run is marked cold cache, and metadata handling
  and write flushing still differ. Cold-cache runs never replace the latest results.
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
Latest per pair · Linux · Blender 5.0.0 → 5.1.0 · 2026-11-17, 2026-11-22 · measurement contract 2

[This run's report](_docs/reports/2026-11-22/44992971724-1/README.md) · [Actions logs and artifacts](https://github.com/icauro/Gutch-Benchmarks/actions/runs/44992971724)

<details>
<summary>Detailed results and source reports</summary>

[Source: Gutch vs restic](_docs/reports/2026-11-17/44132299226-1/restic.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Restic](https://github.com/restic/restic) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.842 | 1.743 | 0.915 | 688.197 |
| [Restic](https://github.com/restic/restic) | PASS | 8.752 | 4.439 | 3.366 | 714.583 |
| **Gutch relative** | - | 1.81x faster | 2.55x faster | 3.68x faster | 3.7% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 174.4 | 381.5 | 127.6 | 687.8 | 159.0 | 2,571.3 | 152.3 | 2,571.3 |
| [Restic](https://github.com/restic/restic) | 206.7 | 397.8 | 218.8 | 715.8 | 107.5 | 2,599.3 | 67.0 | 2,599.3 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [Restic](https://github.com/restic/restic) |
|---|---:|---:|
| First capture s | 2.484 (2.440–2.664; n=6) | 4.470 (4.358–4.573; n=6) |
| Later-version capture s | 2.387 (2.151–2.475; n=6) | 4.251 (4.220–4.331; n=6) |
| Later-version stored growth bytes | 320125425.000 (318593931.000–321948979.000; n=6) | 332743957.000 (331399629.000–334519180.000; n=6) |
| Restore + independent validation s | 4.469 (4.395–4.526; n=6) | 7.151 (7.123–7.216; n=6) |
| Content repair + validation s | 3.608 (3.561–3.666; n=6) | 6.066 (6.061–6.093; n=6) |
| Preserved-mtime repair + validation s | 3.608 (3.586–3.633; n=6) | 6.214 (6.077–6.331; n=6) |
| Extra-file cleanup + validation s | 3.228 (3.220–3.251; n=6) | 6.009 (5.993–6.063; n=6) |
| Full restore recovery + validation s | 4.474 (4.461–4.485; n=6) | 7.150 (7.116–7.177; n=6) |

[Source: Gutch vs kopia](_docs/reports/2026-11-17/44132299226-1/kopia.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Kopia](https://github.com/kopia/kopia) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 5.460 | 1.540 | 0.904 | 1758.306 |
| [Kopia](https://github.com/kopia/kopia) | PASS | 4.563 | 7.074 | 7.249 | 1754.514 |
| **Gutch relative** | - | 1.20x slower | 4.59x faster | 8.02x faster | 0.2% larger |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 210.5 | 912.0 | 207.6 | 1,765.9 | 92.2 | 3,649.4 | 99.2 | 3,649.4 |
| [Kopia](https://github.com/kopia/kopia) | 193.1 | 912.9 | 170.9 | 1,755.9 | 266.6 | 5,392.1 | 263.2 | 5,392.1 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [Kopia](https://github.com/kopia/kopia) |
|---|---:|---:|
| First capture s | 2.795 (2.774–2.808; n=6) | 2.396 (2.310–2.432; n=6) |
| Later-version capture s | 2.665 (2.657–2.673; n=6) | 2.179 (2.145–2.378; n=6) |
| Later-version stored growth bytes | 887424848.000 (886019060.000–891508268.000; n=6) | 883232134.000 (883228051.000–883236043.000; n=6) |
| Restore + independent validation s | 5.151 (5.117–5.189; n=6) | 10.686 (10.583–13.117; n=6) |
| Content repair + validation s | 4.498 (4.454–4.723; n=6) | 10.880 (8.542–10.974; n=6) |
| Preserved-mtime repair + validation s | 4.452 (4.442–4.474; n=6) | 8.772 (8.698–8.819; n=6) |
| Extra-file cleanup + validation s | 4.237 (4.228–4.254; n=6) | 8.766 (8.573–8.854; n=6) |
| Full restore recovery + validation s | 5.164 (5.149–5.266; n=6) | 6.778 (6.535–6.993; n=6) |

[Source: Gutch vs borg](_docs/reports/2026-11-17/44132299226-1/borg.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Borg](https://github.com/borgbackup/borg) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 7.965 | 2.894 | 1.087 | 913.570 |
| [Borg](https://github.com/borgbackup/borg) | PASS | 9.833 | 6.330 | 2.556 | 915.932 |
| **Gutch relative** | - | 1.23x faster | 2.19x faster | 2.35x faster | 0.3% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 41.1 | 496.0 | 42.5 | 913.6 | 40.0 | 2,797.1 | 87.9 | 2,797.1 |
| [Borg](https://github.com/borgbackup/borg) | 241.6 | 533.5 | 237.4 | 952.2 | 364.9 | 2,800.1 | 266.6 | 2,835.7 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [Borg](https://github.com/borgbackup/borg) |
|---|---:|---:|
| First capture s | 4.020 (2.978–4.106; n=6) | 4.929 (4.312–5.551; n=6) |
| Later-version capture s | 3.945 (2.889–4.103; n=6) | 4.903 (4.286–5.557; n=6) |
| Later-version stored growth bytes | 437891852.000 (437891852.000–437891852.000; n=6) | 438953666.500 (437766235.000–441207482.000; n=6) |
| Restore + independent validation s | 5.385 (5.329–5.409; n=6) | 8.828 (8.507–8.986; n=6) |
| Content repair + validation s | 3.559 (3.544–3.575; n=6) | 5.041 (5.007–5.169; n=6) |
| Preserved-mtime repair + validation s | 3.579 (3.526–3.612; n=6) | - |
| Extra-file cleanup + validation s | 3.066 (3.010–3.086; n=6) | - |
| Full restore recovery + validation s | 5.387 (5.350–5.454; n=6) | 8.756 (8.553–8.953; n=6) |

borg: exact_recovery: UNSUPPORTED: no native extra-file deletion in this adapter; hidden_repair: UNSUPPORTED: native resume trusts size and mtime

[Source: Gutch vs rustic](_docs/reports/2026-11-17/44132299226-1/rustic.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Rustic](https://github.com/rustic-rs/rustic) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.485 | 1.410 | 0.837 | 688.259 |
| [Rustic](https://github.com/rustic-rs/rustic) | PASS | 10.607 | 4.167 | 3.362 | 701.702 |
| **Gutch relative** | - | 2.36x faster | 2.95x faster | 4.02x faster | 1.9% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 116.6 | 382.6 | 243.1 | 687.6 | 208.0 | 2,570.9 | 142.3 | 2,570.9 |
| [Rustic](https://github.com/rustic-rs/rustic) | 136.6 | 390.8 | 136.6 | 703.0 | 322.8 | 2,586.5 | 136.6 | 2,586.5 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [Rustic](https://github.com/rustic-rs/rustic) |
|---|---:|---:|
| First capture s | 2.345 (2.160–2.404; n=6) | 5.671 (5.507–5.693; n=6) |
| Later-version capture s | 2.146 (2.125–2.249; n=6) | 4.936 (4.839–5.045; n=6) |
| Later-version stored growth bytes | 320903590.000 (319985313.000–321897086.000; n=6) | 327079257.000 (325848015.000–329975784.000; n=6) |
| Restore + independent validation s | 3.616 (3.512–3.731; n=6) | 6.426 (6.258–6.601; n=6) |
| Content repair + validation s | 3.024 (2.920–3.049; n=6) | 5.537 (5.265–5.618; n=6) |
| Preserved-mtime repair + validation s | 3.002 (2.911–3.034; n=6) | 5.559 (5.311–5.628; n=6) |
| Extra-file cleanup + validation s | 2.696 (2.583–2.732; n=6) | 5.513 (5.293–5.573; n=6) |
| Full restore recovery + validation s | 3.626 (3.599–3.639; n=6) | 6.495 (6.319–6.614; n=6) |

[Source: Gutch vs plakar](_docs/reports/2026-11-17/44132299226-1/plakar.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Plakar](https://github.com/PlakarKorp/plakar) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 3.907 | 1.145 | 0.556 | 913.908 |
| [Plakar](https://github.com/PlakarKorp/plakar) | PASS | 8.860 | 3.768 | 15.986 | 916.641 |
| **Gutch relative** | - | 2.27x faster | 3.29x faster | 28.78x faster | 0.3% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 81.8 | 496.0 | 72.3 | 913.9 | 51.2 | 2,797.4 | 170.8 | 2,797.4 |
| [Plakar](https://github.com/PlakarKorp/plakar) | 340.8 | 520.9 | 339.0 | 970.8 | 411.7 | 2,818.6 | 399.9 | 2,822.8 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [Plakar](https://github.com/PlakarKorp/plakar) |
|---|---:|---:|
| First capture s | 1.930 (1.436–2.375; n=6) | 5.369 (5.248–5.905; n=6) |
| Later-version capture s | 1.982 (1.968–1.984; n=6) | 3.492 (3.462–3.516; n=6) |
| Later-version stored growth bytes | 438186147.000 (438186147.000–438186147.000; n=6) | 438265579.000 (437656676.000–438943693.000; n=6) |
| Restore + independent validation s | 3.612 (3.600–3.663; n=6) | 6.265 (6.219–6.335; n=6) |
| Content repair + validation s | 2.995 (2.982–3.026; n=6) | 18.454 (16.236–18.549; n=6) |
| Preserved-mtime repair + validation s | 3.002 (2.984–3.024; n=6) | 10.533 (10.524–10.564; n=6) |
| Extra-file cleanup + validation s | 2.787 (2.736–2.796; n=6) | - |
| Full restore recovery + validation s | 3.606 (3.591–3.640; n=6) | 5.838 (5.820–5.877; n=6) |

plakar: exact_recovery: UNSUPPORTED: no native extra-file deletion in this adapter

[Source: Gutch vs bpt](_docs/reports/2026-11-17/44132299226-1/bpt.json)

### [Gutch](https://github.com/icauro/Gutch) vs [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.212 | 1.057 | 0.558 | 689.362 |
| [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) | PASS | 24.869 | 25.063 | 2.552 | 732.343 |
| **Gutch relative** | - | 5.91x faster | 23.71x faster | 4.58x faster | 5.9% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 151.1 | 382.1 | 134.6 | 689.4 | 123.3 | 2,572.9 | 120.1 | 2,572.9 |
| [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) | 385.7 | 403.7 | 556.7 | 732.3 | 228.5 | 2,615.8 | 131.3 | 2,615.8 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) |
|---|---:|---:|
| First capture s | 2.227 (2.189–2.268; n=6) | 8.825 (8.720–9.295; n=6) |
| Later-version capture s | 1.977 (1.950–2.108; n=6) | 15.956 (15.732–16.413; n=6) |
| Later-version stored growth bytes | 322167321.000 (322167321.000–322167321.000; n=6) | 344645877.500 (344645864.000–344645892.000; n=6) |
| Restore + independent validation s | 3.135 (3.093–3.152; n=6) | 27.110 (26.681–28.221; n=6) |
| Content repair + validation s | 2.593 (2.574–2.668; n=6) | 4.600 (4.544–4.695; n=6) |
| Preserved-mtime repair + validation s | 2.583 (2.564–2.652; n=6) | 4.447 (4.202–4.587; n=6) |
| Extra-file cleanup + validation s | 2.341 (2.306–2.389; n=6) | - |
| Full restore recovery + validation s | 3.118 (3.065–3.227; n=6) | 26.769 (26.230–26.969; n=6) |

buildpatchtool: exact_recovery: UNSUPPORTED: no native extra-file deletion in this adapter

[Source: Gutch vs cavs](_docs/reports/2026-11-22/44992971724-1/cavs.json)

### [Gutch](https://github.com/icauro/Gutch) vs [CAVS](https://github.com/terragov/cavs) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.387 | 1.885 | 1.043 | 679.349 |
| [CAVS](https://github.com/terragov/cavs) | PASS | 10.646 | 7.057 | 4.871 | 712.400 |
| **Gutch relative** | - | 2.43x faster | 3.74x faster | 4.67x faster | 4.6% smaller |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 153.0 | 379.7 | 154.4 | 679.3 | 167.5 | 2,562.9 | 176.9 | 2,562.9 |
| [CAVS](https://github.com/terragov/cavs) | 256.4 | 788.5 | 230.1 | 1,107.0 | 102.4 | 4,322.2 | 84.3 | 4,322.2 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [CAVS](https://github.com/terragov/cavs) |
|---|---:|---:|
| First capture s | 2.189 (2.177–2.224; n=6) | 5.363 (5.336–5.384; n=6) |
| Later-version capture s | 2.197 (2.193–2.199; n=6) | 5.294 (5.241–5.301; n=6) |
| Later-version stored growth bytes | 314154379.000 (314154379.000–314154379.000; n=6) | 331724047.000 (331724047.000–331724047.000; n=6) |
| Restore + independent validation s | 5.638 (5.607–5.756; n=6) | 10.784 (10.731–11.292; n=6) |
| Content repair + validation s | 4.720 (4.703–4.757; n=6) | 8.527 (8.332–8.660; n=6) |
| Preserved-mtime repair + validation s | 4.695 (4.687–4.738; n=6) | 8.292 (8.256–8.371; n=6) |
| Extra-file cleanup + validation s | 4.171 (4.164–4.189; n=6) | - |
| Full restore recovery + validation s | 5.644 (5.632–5.663; n=6) | 10.914 (10.813–11.206; n=6) |

cavs: exact_recovery: UNSUPPORTED: cavs-client skips --prune when every managed file already matches

[Source: Gutch vs encrypted](_docs/reports/2026-11-17/44132299226-1/encrypted.json)

### [Gutch](https://github.com/icauro/Gutch) vs [Encrypted Gutch](https://github.com/icauro/Gutch) (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 3.535 | 1.313 | 0.636 | 689.362 |
| [Encrypted Gutch](https://github.com/icauro/Gutch) | PASS | 3.749 | 1.602 | 0.858 | 688.366 |
| **Gutch relative** | - | 1.06x faster | 1.22x faster | 1.35x faster | 0.1% larger |

**Resources by operation (MiB)**

| Tool | First capture RAM | First capture disk | Second capture RAM | Second capture disk | Restore RAM | Restore disk | Repair RAM | Repair disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Gutch](https://github.com/icauro/Gutch) | 134.0 | 382.1 | 136.3 | 689.4 | 123.1 | 2,572.9 | 183.9 | 2,572.9 |
| [Encrypted Gutch](https://github.com/icauro/Gutch) | 113.8 | 383.2 | 162.2 | 688.1 | 146.7 | 2,571.6 | 148.4 | 2,571.6 |

RAM is the largest sampled process-tree RSS across commands in that operation. Restore and repair each cover both versions. `—` means no per-operation measurement was recorded; whole-workflow disk peaks are not reused here.

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [Encrypted Gutch](https://github.com/icauro/Gutch) |
|---|---:|---:|
| First capture s | 1.802 (1.739–1.818; n=6) | 1.864 (1.834–1.944; n=6) |
| Later-version capture s | 1.730 (1.688–1.746; n=6) | 1.853 (1.797–1.901; n=6) |
| Later-version stored growth bytes | 322167321.000 (322167321.000–322167321.000; n=6) | 320748580.500 (319246682.000–322256420.000; n=6) |
| Restore + independent validation s | 3.811 (3.795–3.828; n=6) | 4.074 (4.068–4.103; n=6) |
| Content repair + validation s | 3.100 (3.093–3.114; n=6) | 3.309 (3.283–3.369; n=6) |
| Preserved-mtime repair + validation s | 3.107 (3.094–3.116; n=6) | 3.329 (3.302–3.352; n=6) |
| Extra-file cleanup + validation s | 2.810 (2.785–2.815; n=6) | 3.004 (2.990–3.035; n=6) |
| Full restore recovery + validation s | 3.856 (3.823–3.886; n=6) | 4.118 (4.071–4.136; n=6) |

</details>

<!-- latest-benchmarks:end -->

<details>
<summary>Run on GitHub</summary>

Open **Actions > Manual Linux benchmarks > Run workflow**. Choose `all` or one
pair, a Gutch release, and repetitions. Defaults: Ubuntu 24.04, all eight pairs
(seven tools plus the Gutch encryption-cost pair),
one warm-up and six measured repetitions.
All pairs can run concurrently, each on its own runner.

All jobs share a validated Blender input cache. Repositories and restored outputs
are discarded after each sample. Runs on the default branch save compact reports
in Git and update this page; detailed logs and traces remain Actions artifacts
for 30 days. Hosted-runner timings are indicative; OS caches are uncontrolled
unless you tick **cold_cache**, which drops them before every command.

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
