# Linux benchmark results

Run: [41218304728, attempt 1](https://github.com/icauro/Gutch-Benchmarks/actions/runs/41218304728) | UTC date: 2026-10-31

Each pair has its own settings. Hosted-runner timings are indicative; OS cache state is uncontrolled.

## Gutch vs restic: PASS

Restic uses native Rabin around 1 MiB, explicit Zstd auto, 8 MiB pack targets and mandatory encryption. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3, 8 MiB compressed bundles and no encryption. Zstd auto is not an exact level-3 match; bounds, codec implementations and compression units differ. Restore retains --verify; recovery verifies existing bytes and deletes extra files. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 1 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `4a514907dd490fd0874f2646414180945f9a784a`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](restic.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.525 | 1.911 | 1.028 | 1.907 | 689.361 | - | 140.684 | 2572.868 |
| [Restic](https://github.com/restic/restic) | PASS | 8.939 | 5.840 | 4.225 | 5.888 | 717.455 | - | 196.926 | 2602.222 |

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



## Gutch vs kopia: PASS

Kopia explicitly uses DYNAMIC-4M-BUZHASH, disabled content compression and AES256-GCM-HMAC-SHA256 encryption. Gutch uses a nominal 4 MiB FastCDC target, no compression, 16 MiB bundles and no encryption. Bounds, metadata, hashes and packing differ. Kopia recovery requests native extra-file deletion. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 1 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `4a514907dd490fd0874f2646414180945f9a784a`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 9V74 80-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](kopia.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 10.462 | 0.963 | 0.628 | 0.934 | 1758.175 | - | 225.055 | 3641.682 |
| [Kopia](https://github.com/kopia/kopia) | PASS | 9.861 | 17.341 | 10.450 | 2.267 | 1754.498 | - | 336.789 | 5392.065 |

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



## Gutch vs borg: PASS

Borg explicitly uses FastCDC fastcdc,19,23,21,2, LZ4, authenticated unencrypted storage and metadata-based resume. Gutch uses a nominal 2 MiB FastCDC target, LZ4 0 and 8 MiB compressed bundles. Bounds, hashes, compression framing and storage layout differ. Borg cannot detect preserved-mtime damage via resume and this adapter has no native extra-file cleanup. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 1 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `4a514907dd490fd0874f2646414180945f9a784a`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](borg.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 7.093 | 1.745 | 0.880 | 1.769 | 913.570 | - | 160.340 | 2797.076 |
| [Borg](https://github.com/borgbackup/borg) | PASS | 11.321 | 9.861 | 3.602 | 9.791 | 916.128 | - | 343.570 | 2836.135 |

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



## Gutch vs rustic: PASS

Rustic explicitly uses Rabin with a 1 MiB average, 512 KiB minimum and 8 MiB maximum, Zstd 3, and 8 MiB data/tree pack targets with growth disabled. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3 and 8 MiB compressed bundles. Chunk boundaries, compression units and hashes differ; Rustic remains encrypted. Recovery verifies existing bytes and deletes extra files. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 1 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `4a514907dd490fd0874f2646414180945f9a784a`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](rustic.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.487 | 1.906 | 1.020 | 1.923 | 689.361 | - | 186.227 | 2572.868 |
| [Rustic](https://github.com/rustic-rs/rustic) | PASS | 14.735 | 5.621 | 4.208 | 5.679 | 701.205 | - | 343.816 | 2583.652 |

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



## Gutch vs plakar: PASS

Plakar uses native FastCDC around 1 MiB and LZ4 stream compression, with plaintext storage. Gutch uses a nominal 1 MiB FastCDC target, LZ4 0 and 8 MiB compressed bundles. Bounds, compression units/framing and packing differ. Plakar restores over existing output; this adapter has no native extra-file deletion. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 1 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `4a514907dd490fd0874f2646414180945f9a784a`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 9V74 80-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](plakar.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 6.921 | 1.398 | 0.735 | 1.373 | 913.907 | - | 148.570 | 2797.414 |
| [Plakar](https://github.com/PlakarKorp/plakar) | PASS | 11.476 | 5.327 | 14.778 | 4.085 | 916.557 | - | 422.230 | 2861.892 |

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



## Gutch vs bpt: PASS

BuildPatchTool uses a 1 MiB chunk window and its internal compression with FeatureLevel=Latest. Local InstallManifest recovery uses PrevManifest. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3 and 8 MiB compressed bundles. Chunk windows are not CDC averages; codecs and formats are unmatched. No native extra-file cleanup or separate repository check is available in this adapter. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 1 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `4a514907dd490fd0874f2646414180945f9a784a`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](bpt.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.487 | 1.914 | 1.008 | 1.916 | 689.361 | - | 142.406 | 2572.868 |
| [BuildPatchTool](https://github.com/EpicGames/UnrealEngine) | PASS | 36.714 | 28.158 | 2.278 | 28.578 | 732.343 | - | 520.008 | 2615.850 |

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
