# Linux benchmark results

Run: [44132299226, attempt 1](https://github.com/icauro/Gutch-Benchmarks/actions/runs/44132299226) | UTC date: 2026-11-17

Each pair has its own settings. Hosted-runner timings are indicative; OS cache state is uncontrolled.

## Gutch vs restic: PASS

Restic uses native Rabin around 1 MiB, explicit Zstd auto, 8 MiB pack targets and mandatory encryption. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3, 8 MiB compressed bundles and AES-256-GCM repository encryption. Both encrypt, with different schemes. Zstd auto is not an exact level-3 match; bounds, codec implementations and compression units differ. Restore omits --verify, which would re-read restored files that the suite validates anyway; recovery verifies existing bytes and deletes extra files. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 6 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `c47104377233b59edc3723071a5b82da64d9001f`; Gutch release: `0.1.0`; Gutch commit: `c3465e71fd0859c49a40c55f2c0e49212633d8fc`.

Host: `{'cpu_count': 4, 'cpu_model': 'INTEL(R) XEON(R) PLATINUM 8573C', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](restic.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.842 | 1.743 | 0.915 | 1.746 | 688.197 | - | 177.844 | 2571.346 |
| [Restic](https://github.com/restic/restic) | PASS | 8.752 | 4.439 | 3.366 | 4.430 | 714.583 | - | 218.793 | 2601.209 |

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



## Gutch vs kopia: PASS

Kopia explicitly uses DYNAMIC-4M-BUZHASH, disabled content compression and AES256-GCM-HMAC-SHA256 encryption. Gutch uses a nominal 4 MiB FastCDC target, no compression, 16 MiB bundles and AES-256-GCM repository encryption. Bounds, metadata, hashes and packing differ. Kopia recovery requests native extra-file deletion. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 6 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `c47104377233b59edc3723071a5b82da64d9001f`; Gutch release: `0.1.0`; Gutch commit: `c3465e71fd0859c49a40c55f2c0e49212633d8fc`.

Host: `{'cpu_count': 4, 'cpu_model': 'Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](kopia.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 5.460 | 1.540 | 0.904 | 1.545 | 1758.306 | - | 210.461 | 3649.418 |
| [Kopia](https://github.com/kopia/kopia) | PASS | 4.563 | 7.074 | 7.249 | 3.174 | 1754.514 | - | 311.961 | 5392.071 |

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



## Gutch vs borg: PASS

Borg explicitly uses FastCDC fastcdc,19,23,21,2, LZ4, authenticated unencrypted storage and metadata-based resume. Gutch uses the matching 2 MiB FastCDC preset (512 KiB / 2 MiB / 8 MiB), LZ4 0 and 8 MiB compressed bundles. Hashes, compression framing and storage layout differ. Borg cannot detect preserved-mtime damage via resume and this adapter has no native extra-file cleanup. Fresh repositories and isolated caches. Gutch runs one worker to match single-threaded Borg. One warm-up and 6 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `c47104377233b59edc3723071a5b82da64d9001f`; Gutch release: `0.1.0`; Gutch commit: `c3465e71fd0859c49a40c55f2c0e49212633d8fc`.

Host: `{'cpu_count': 4, 'cpu_model': 'Intel(R) Xeon(R) 6975P-C', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1014-aws-x86_64-with-glibc2.39'}`

[Machine-readable report](borg.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 7.965 | 2.894 | 1.087 | 2.901 | 913.570 | - | 90.762 | 2797.077 |
| [Borg](https://github.com/borgbackup/borg) | PASS | 9.833 | 6.330 | 2.556 | 6.268 | 915.932 | - | 364.926 | 2835.665 |

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



## Gutch vs rustic: PASS

Rustic explicitly uses Rabin with a 1 MiB average, 256 KiB minimum and 4 MiB maximum, matching the Gutch 1 MiB preset bounds, Zstd 3, and 8 MiB data/tree pack targets with growth disabled. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3 and 8 MiB compressed bundles. Chunk boundaries (Rabin versus FastCDC), compression units and hashes differ; both repositories are encrypted. Recovery verifies existing bytes and deletes extra files. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 6 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `c47104377233b59edc3723071a5b82da64d9001f`; Gutch release: `0.1.0`; Gutch commit: `c3465e71fd0859c49a40c55f2c0e49212633d8fc`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 9V45 96-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](rustic.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.485 | 1.410 | 0.837 | 1.429 | 688.259 | - | 243.102 | 2570.910 |
| [Rustic](https://github.com/rustic-rs/rustic) | PASS | 10.607 | 4.167 | 3.362 | 4.231 | 701.702 | - | 335.281 | 2586.466 |

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



## Gutch vs plakar: PASS

Plakar uses native FastCDC around 1 MiB and LZ4 stream compression, with plaintext storage. Gutch uses a nominal 1 MiB FastCDC target, LZ4 0 and 8 MiB compressed bundles. Bounds, compression units/framing and packing differ. Plakar restores over existing output; this adapter has no native extra-file deletion. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 6 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `c47104377233b59edc3723071a5b82da64d9001f`; Gutch release: `0.1.0`; Gutch commit: `c3465e71fd0859c49a40c55f2c0e49212633d8fc`.

Host: `{'cpu_count': 4, 'cpu_model': 'Intel(R) Xeon(R) 6975P-C', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1014-aws-x86_64-with-glibc2.39'}`

[Machine-readable report](plakar.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 3.907 | 1.145 | 0.556 | 1.140 | 913.908 | - | 200.352 | 2797.414 |
| [Plakar](https://github.com/PlakarKorp/plakar) | PASS | 8.860 | 3.768 | 15.986 | 3.361 | 916.641 | - | 430.207 | 2842.138 |

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



## Gutch vs bpt: PASS

BuildPatchTool uses a 1 MiB chunk window and its internal compression with FeatureLevel=Latest. Local InstallManifest recovery uses PrevManifest. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3 and 8 MiB compressed bundles. Chunk windows are not CDC averages; codecs and formats are unmatched. No native extra-file cleanup or separate repository check is available in this adapter. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 6 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `c47104377233b59edc3723071a5b82da64d9001f`; Gutch release: `0.1.0`; Gutch commit: `c3465e71fd0859c49a40c55f2c0e49212633d8fc`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 9V45 96-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](bpt.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.212 | 1.057 | 0.558 | 1.057 | 689.362 | - | 153.406 | 2572.868 |
| [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) | PASS | 24.869 | 25.063 | 2.552 | 24.726 | 732.343 | - | 556.742 | 2705.843 |

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



## Gutch vs encrypted: PASS

Measures the cost of Gutch repository encryption. Both cases run the same Gutch release on the same runner with identical settings, a nominal 1 MiB FastCDC target, Zstd 3 and 8 MiB compressed bundles; only the second case encrypts its repository with AES-256-GCM, unlocked by a fixed local test password. Gutch relative compares unencrypted with encrypted Gutch. Fresh repositories and isolated caches. Four workers. One warm-up and 6 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported.

Suite commit: `c47104377233b59edc3723071a5b82da64d9001f`; Gutch release: `0.1.0`; Gutch commit: `c3465e71fd0859c49a40c55f2c0e49212633d8fc`.

Host: `{'cpu_count': 4, 'cpu_model': 'Intel(R) Xeon(R) 6975P-C', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1014-aws-x86_64-with-glibc2.39'}`

[Machine-readable report](encrypted.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 3.535 | 1.313 | 0.636 | 1.357 | 689.362 | - | 183.926 | 2572.868 |
| [Encrypted Gutch](https://github.com/icauro/Gutch) | PASS | 3.749 | 1.602 | 0.858 | 1.613 | 688.366 | - | 162.195 | 2571.602 |

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
