# Linux benchmark results

Run: [44122579900, attempt 1](https://github.com/icauro/Gutch-Benchmarks/actions/runs/44122579900) | UTC date: 2026-11-17

Each pair has its own settings. Hosted-runner timings are indicative; OS cache state is uncontrolled.

## Gutch vs restic: PASS

Restic uses native Rabin around 1 MiB, explicit Zstd auto, 8 MiB pack targets and mandatory encryption. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3, 8 MiB compressed bundles and AES-256-GCM repository encryption. Both encrypt, with different schemes. Zstd auto is not an exact level-3 match; bounds, codec implementations and compression units differ. Restore retains --verify; recovery verifies existing bytes and deletes extra files. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 6 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `9ebdd713383b6bfc834b3a80a51bf14f81ed1d39`; Gutch release: `0.1.0`; Gutch commit: `c3465e71fd0859c49a40c55f2c0e49212633d8fc`.

Host: `{'cpu_count': 4, 'cpu_model': 'Intel(R) Xeon(R) 6975P-C', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1014-aws-x86_64-with-glibc2.39'}`

[Machine-readable report](restic.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 3.922 | 1.701 | 0.913 | 1.701 | 687.209 | - | 167.297 | 2570.429 |
| [Restic](https://github.com/restic/restic) | PASS | 7.616 | 4.873 | 3.483 | 4.898 | 714.965 | - | 198.477 | 2605.894 |

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



## Gutch vs kopia: PASS

Kopia explicitly uses DYNAMIC-4M-BUZHASH, disabled content compression and AES256-GCM-HMAC-SHA256 encryption. Gutch uses a nominal 4 MiB FastCDC target, no compression, 16 MiB bundles and AES-256-GCM repository encryption. Bounds, metadata, hashes and packing differ. Kopia recovery requests native extra-file deletion. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 6 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `9ebdd713383b6bfc834b3a80a51bf14f81ed1d39`; Gutch release: `0.1.0`; Gutch commit: `c3465e71fd0859c49a40c55f2c0e49212633d8fc`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](kopia.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 5.745 | 1.783 | 1.103 | 1.811 | 1761.518 | - | 211.008 | 3645.082 |
| [Kopia](https://github.com/kopia/kopia) | PASS | 4.607 | 8.640 | 6.206 | 3.283 | 1754.523 | - | 328.574 | 5392.077 |

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



## Gutch vs borg: PASS

Borg explicitly uses FastCDC fastcdc,19,23,21,2, LZ4, authenticated unencrypted storage and metadata-based resume. Gutch uses a nominal 2 MiB FastCDC target, LZ4 0 and 8 MiB compressed bundles. Bounds, hashes, compression framing and storage layout differ. Borg cannot detect preserved-mtime damage via resume and this adapter has no native extra-file cleanup. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 6 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `9ebdd713383b6bfc834b3a80a51bf14f81ed1d39`; Gutch release: `0.1.0`; Gutch commit: `c3465e71fd0859c49a40c55f2c0e49212633d8fc`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](borg.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 6.863 | 1.585 | 0.810 | 1.593 | 913.570 | - | 183.750 | 2797.077 |
| [Borg](https://github.com/borgbackup/borg) | PASS | 13.059 | 9.743 | 3.971 | 9.594 | 916.433 | - | 343.367 | 2836.543 |

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



## Gutch vs rustic: PASS

Rustic explicitly uses Rabin with a 1 MiB average, 512 KiB minimum and 8 MiB maximum, Zstd 3, and 8 MiB data/tree pack targets with growth disabled. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3 and 8 MiB compressed bundles. Chunk boundaries, compression units and hashes differ; both repositories are encrypted. Recovery verifies existing bytes and deletes extra files. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 6 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `9ebdd713383b6bfc834b3a80a51bf14f81ed1d39`; Gutch release: `0.1.0`; Gutch commit: `c3465e71fd0859c49a40c55f2c0e49212633d8fc`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 9V74 80-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](rustic.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.875 | 2.299 | 1.359 | 2.317 | 688.435 | - | 174.781 | 2571.469 |
| [Rustic](https://github.com/rustic-rs/rustic) | PASS | 14.610 | 5.594 | 4.475 | 5.634 | 699.401 | - | 335.746 | 2586.191 |

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



## Gutch vs plakar: PASS

Plakar uses native FastCDC around 1 MiB and LZ4 stream compression, with plaintext storage. Gutch uses a nominal 1 MiB FastCDC target, LZ4 0 and 8 MiB compressed bundles. Bounds, compression units/framing and packing differ. Plakar restores over existing output; this adapter has no native extra-file deletion. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 6 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `9ebdd713383b6bfc834b3a80a51bf14f81ed1d39`; Gutch release: `0.1.0`; Gutch commit: `c3465e71fd0859c49a40c55f2c0e49212633d8fc`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 9V74 80-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](plakar.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 5.621 | 1.248 | 0.684 | 1.246 | 913.908 | - | 133.180 | 2797.414 |
| [Plakar](https://github.com/PlakarKorp/plakar) | PASS | 11.479 | 5.062 | 17.346 | 4.099 | 916.405 | - | 421.457 | 2822.015 |

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



## Gutch vs bpt: PASS

BuildPatchTool uses a 1 MiB chunk window and its internal compression with FeatureLevel=Latest. Local InstallManifest recovery uses PrevManifest. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3 and 8 MiB compressed bundles. Chunk windows are not CDC averages; codecs and formats are unmatched. No native extra-file cleanup or separate repository check is available in this adapter. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 6 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `9ebdd713383b6bfc834b3a80a51bf14f81ed1d39`; Gutch release: `0.1.0`; Gutch commit: `c3465e71fd0859c49a40c55f2c0e49212633d8fc`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](bpt.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.688 | 1.877 | 0.993 | 1.893 | 689.362 | - | 134.492 | 2572.868 |
| [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) | PASS | 37.011 | 29.150 | 2.295 | 29.138 | 732.343 | - | 556.832 | 2615.850 |

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
