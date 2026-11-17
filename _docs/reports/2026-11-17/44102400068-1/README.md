# Linux benchmark results

Run: [44102400068, attempt 1](https://github.com/icauro/Gutch-Benchmarks/actions/runs/44102400068) | UTC date: 2026-11-17

Each pair has its own settings. Hosted-runner timings are indicative; OS cache state is uncontrolled.

## Gutch vs restic: PASS

Restic uses native Rabin around 1 MiB, explicit Zstd auto, 8 MiB pack targets and mandatory encryption. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3, 8 MiB compressed bundles and no encryption. Zstd auto is not an exact level-3 match; bounds, codec implementations and compression units differ. Restore retains --verify; recovery verifies existing bytes and deletes extra files. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 6 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `860627cc645db57e9a5fcdb3cffab59c059e5940`; Gutch release: `0.1.0`; Gutch commit: `c3465e71fd0859c49a40c55f2c0e49212633d8fc`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 9V74 80-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](restic.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.640 | 1.371 | 0.759 | 1.388 | 689.362 | - | 134.020 | 2572.868 |
| [Restic](https://github.com/restic/restic) | PASS | 8.500 | 5.036 | 3.783 | 5.085 | 714.621 | - | 234.930 | 2603.864 |

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



## Gutch vs kopia: PASS

Kopia explicitly uses DYNAMIC-4M-BUZHASH, disabled content compression and AES256-GCM-HMAC-SHA256 encryption. Gutch uses a nominal 4 MiB FastCDC target, no compression, 16 MiB bundles and no encryption. Bounds, metadata, hashes and packing differ. Kopia recovery requests native extra-file deletion. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 6 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `860627cc645db57e9a5fcdb3cffab59c059e5940`; Gutch release: `0.1.0`; Gutch commit: `c3465e71fd0859c49a40c55f2c0e49212633d8fc`.

Host: `{'cpu_count': 4, 'cpu_model': 'Intel(R) Xeon(R) 6975P-C', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1014-aws-x86_64-with-glibc2.39'}`

[Machine-readable report](kopia.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 8.445 | 0.770 | 0.466 | 0.780 | 1758.176 | - | 205.070 | 3641.682 |
| [Kopia](https://github.com/kopia/kopia) | PASS | 6.845 | 13.866 | 9.375 | 2.144 | 1754.518 | - | 327.023 | 5392.059 |

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



## Gutch vs borg: PASS

Borg explicitly uses FastCDC fastcdc,19,23,21,2, LZ4, authenticated unencrypted storage and metadata-based resume. Gutch uses a nominal 2 MiB FastCDC target, LZ4 0 and 8 MiB compressed bundles. Bounds, hashes, compression framing and storage layout differ. Borg cannot detect preserved-mtime damage via resume and this adapter has no native extra-file cleanup. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 6 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `860627cc645db57e9a5fcdb3cffab59c059e5940`; Gutch release: `0.1.0`; Gutch commit: `c3465e71fd0859c49a40c55f2c0e49212633d8fc`.

Host: `{'cpu_count': 4, 'cpu_model': 'Intel(R) Xeon(R) 6975P-C', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1014-aws-x86_64-with-glibc2.39'}`

[Machine-readable report](borg.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.545 | 1.164 | 0.545 | 1.180 | 913.570 | - | 133.668 | 2797.077 |
| [Borg](https://github.com/borgbackup/borg) | PASS | 9.681 | 5.974 | 2.564 | 5.937 | 915.832 | - | 348.863 | 2837.652 |

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



## Gutch vs rustic: PASS

Rustic explicitly uses Rabin with a 1 MiB average, 512 KiB minimum and 8 MiB maximum, Zstd 3, and 8 MiB data/tree pack targets with growth disabled. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3 and 8 MiB compressed bundles. Chunk boundaries, compression units and hashes differ; Rustic remains encrypted. Recovery verifies existing bytes and deletes extra files. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 6 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `860627cc645db57e9a5fcdb3cffab59c059e5940`; Gutch release: `0.1.0`; Gutch commit: `c3465e71fd0859c49a40c55f2c0e49212633d8fc`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 9V45 96-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](rustic.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.367 | 1.139 | 0.607 | 1.161 | 689.362 | - | 162.184 | 2572.868 |
| [Rustic](https://github.com/rustic-rs/rustic) | PASS | 10.147 | 4.105 | 3.371 | 4.091 | 699.070 | - | 360.691 | 2584.376 |

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



## Gutch vs plakar: PASS

Plakar uses native FastCDC around 1 MiB and LZ4 stream compression, with plaintext storage. Gutch uses a nominal 1 MiB FastCDC target, LZ4 0 and 8 MiB compressed bundles. Bounds, compression units/framing and packing differ. Plakar restores over existing output; this adapter has no native extra-file deletion. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 6 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `860627cc645db57e9a5fcdb3cffab59c059e5940`; Gutch release: `0.1.0`; Gutch commit: `c3465e71fd0859c49a40c55f2c0e49212633d8fc`.

Host: `{'cpu_count': 4, 'cpu_model': 'Intel(R) Xeon(R) 6975P-C', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1014-aws-x86_64-with-glibc2.39'}`

[Machine-readable report](plakar.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 3.762 | 1.164 | 0.571 | 1.155 | 913.908 | - | 131.598 | 2797.414 |
| [Plakar](https://github.com/PlakarKorp/plakar) | PASS | 9.256 | 3.921 | 15.634 | 3.571 | 915.683 | - | 434.406 | 2842.118 |

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



## Gutch vs bpt: PASS

BuildPatchTool uses a 1 MiB chunk window and its internal compression with FeatureLevel=Latest. Local InstallManifest recovery uses PrevManifest. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3 and 8 MiB compressed bundles. Chunk windows are not CDC averages; codecs and formats are unmatched. No native extra-file cleanup or separate repository check is available in this adapter. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 6 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `860627cc645db57e9a5fcdb3cffab59c059e5940`; Gutch release: `0.1.0`; Gutch commit: `c3465e71fd0859c49a40c55f2c0e49212633d8fc`.

Host: `{'cpu_count': 4, 'cpu_model': 'Intel(R) Xeon(R) 6975P-C', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1014-aws-x86_64-with-glibc2.39'}`

[Machine-readable report](bpt.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 3.705 | 1.377 | 0.660 | 1.404 | 689.362 | - | 148.957 | 2572.868 |
| [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) | PASS | 29.807 | 16.026 | 1.859 | 15.782 | 732.343 | - | 515.004 | 2615.850 |

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
