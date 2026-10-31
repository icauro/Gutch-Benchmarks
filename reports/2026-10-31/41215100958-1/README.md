# Linux benchmark results

Run: [41215100958, attempt 1](https://github.com/icauro/Gutch-Benchmarks/actions/runs/41215100958) | UTC date: 2026-10-31

Each pair has its own settings. Hosted-runner timings are indicative; OS cache state is uncontrolled.

## Gutch vs borg: PASS

Borg explicitly uses FastCDC fastcdc,19,23,21,2, LZ4, authenticated unencrypted storage and metadata-based resume. Gutch uses a nominal 2 MiB FastCDC target, LZ4 0 and 8 MiB compressed bundles. Bounds, hashes, compression framing and storage layout differ. Borg cannot detect preserved-mtime damage via resume and this adapter has no native extra-file cleanup. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 1 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `2987627a64436fbebeb745292a323d56e27fb0f9`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](borg.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| borg | PASS | 11.478 | 9.888 | 3.724 | 9.925 | 916.703 | - | 346.496 | 2837.904 |
| gutch | PASS | 7.071 | 1.758 | 0.883 | 1.771 | 913.570 | - | 141.828 | 2797.076 |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | borg | gutch |
|---|---:|---:|
| Initial capture s | 5.781 (5.781–5.781; n=1) | 3.543 (3.543–3.543; n=1) |
| Later-version capture s | 5.697 (5.697–5.697; n=1) | 3.528 (3.528–3.528; n=1) |
| Later-version stored growth bytes | 439779527.000 (439779527.000–439779527.000; n=1) | 437891774.000 (437891774.000–437891774.000; n=1) |
| Restore + independent validation s | 13.511 (13.511–13.511; n=1) | 5.515 (5.515–5.515; n=1) |
| Content repair + validation s | 7.306 (7.306–7.306; n=1) | 4.475 (4.475–4.475; n=1) |
| Preserved-mtime repair + validation s | - | 4.421 (4.421–4.421; n=1) |
| Extra-file cleanup + validation s | - | 4.093 (4.093–4.093; n=1) |
| Full restore recovery + validation s | 13.568 (13.568–13.568; n=1) | 5.426 (5.426–5.426; n=1) |



## Gutch vs bpt: PASS

BuildPatchTool uses a 1 MiB chunk window and its internal compression with FeatureLevel=Latest. Local InstallManifest recovery uses PrevManifest. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3 and 8 MiB compressed bundles. Chunk windows are not CDC averages; codecs and formats are unmatched. No native extra-file cleanup or separate repository check is available in this adapter. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 1 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `2987627a64436fbebeb745292a323d56e27fb0f9`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](bpt.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| buildpatchtool | PASS | 36.828 | 28.176 | 2.237 | 28.228 | 732.343 | - | 520.664 | 2725.630 |
| gutch | PASS | 4.539 | 1.910 | 1.020 | 1.924 | 689.361 | - | 143.281 | 2572.868 |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | buildpatchtool | gutch |
|---|---:|---:|
| Initial capture s | 13.503 (13.503–13.503; n=1) | 2.311 (2.311–2.311; n=1) |
| Later-version capture s | 23.325 (23.325–23.325; n=1) | 2.228 (2.228–2.228; n=1) |
| Later-version stored growth bytes | 344645850.000 (344645850.000–344645850.000; n=1) | 322167243.000 (322167243.000–322167243.000; n=1) |
| Restore + independent validation s | 31.828 (31.828–31.828; n=1) | 5.606 (5.606–5.606; n=1) |
| Content repair + validation s | 5.897 (5.897–5.897; n=1) | 4.669 (4.669–4.669; n=1) |
| Preserved-mtime repair + validation s | 5.890 (5.890–5.890; n=1) | 4.640 (4.640–4.640; n=1) |
| Extra-file cleanup + validation s | - | 4.160 (4.160–4.160; n=1) |
| Full restore recovery + validation s | 31.873 (31.873–31.873; n=1) | 5.620 (5.620–5.620; n=1) |



## Gutch vs kopia: PASS

Kopia explicitly uses DYNAMIC-4M-BUZHASH, disabled content compression and AES256-GCM-HMAC-SHA256 encryption. Gutch uses a nominal 4 MiB FastCDC target, no compression, 16 MiB bundles and no encryption. Bounds, metadata, hashes and packing differ. Kopia recovery requests native extra-file deletion. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 1 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `2987627a64436fbebeb745292a323d56e27fb0f9`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](kopia.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| gutch | PASS | 5.411 | 1.430 | 0.784 | 1.339 | 1758.175 | - | 241.027 | 3641.682 |
| kopia | PASS | 4.642 | 8.080 | 5.120 | 2.924 | 1754.512 | - | 332.266 | 5392.036 |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | gutch | kopia |
|---|---:|---:|
| Initial capture s | 2.734 (2.734–2.734; n=1) | 2.398 (2.398–2.398; n=1) |
| Later-version capture s | 2.677 (2.677–2.677; n=1) | 2.244 (2.244–2.244; n=1) |
| Later-version stored growth bytes | 887308595.000 (887308595.000–887308595.000; n=1) | 883237091.000 (883237091.000–883237091.000; n=1) |
| Restore + independent validation s | 5.175 (5.175–5.175; n=1) | 11.777 (11.777–11.777; n=1) |
| Content repair + validation s | 4.452 (4.452–4.452; n=1) | 8.796 (8.796–8.796; n=1) |
| Preserved-mtime repair + validation s | 4.443 (4.443–4.443; n=1) | 8.809 (8.809–8.809; n=1) |
| Extra-file cleanup + validation s | 4.180 (4.180–4.180; n=1) | 8.998 (8.998–8.998; n=1) |
| Full restore recovery + validation s | 5.038 (5.038–5.038; n=1) | 6.606 (6.606–6.606; n=1) |



## Gutch vs plakar: PASS

Plakar uses native FastCDC around 1 MiB and LZ4 stream compression, with plaintext storage. Gutch uses a nominal 1 MiB FastCDC target, LZ4 0 and 8 MiB compressed bundles. Bounds, compression units/framing and packing differ. Plakar restores over existing output; this adapter has no native extra-file deletion. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 1 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `2987627a64436fbebeb745292a323d56e27fb0f9`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 9V74 80-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](plakar.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| gutch | PASS | 6.653 | 1.377 | 0.716 | 1.374 | 913.907 | - | 182.609 | 2797.413 |
| plakar | PASS | 11.288 | 5.009 | 13.025 | 4.035 | 916.329 | - | 462.074 | 2845.883 |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | gutch | plakar |
|---|---:|---:|
| Initial capture s | 3.406 (3.406–3.406; n=1) | 6.221 (6.221–6.221; n=1) |
| Later-version capture s | 3.247 (3.247–3.247; n=1) | 5.067 (5.067–5.067; n=1) |
| Later-version stored growth bytes | 438186069.000 (438186069.000–438186069.000; n=1) | 438096892.000 (438096892.000–438096892.000; n=1) |
| Restore + independent validation s | 4.055 (4.055–4.055; n=1) | 7.711 (7.711–7.711; n=1) |
| Content repair + validation s | 3.350 (3.350–3.350; n=1) | 15.730 (15.730–15.730; n=1) |
| Preserved-mtime repair + validation s | 3.349 (3.349–3.349; n=1) | 14.098 (14.098–14.098; n=1) |
| Extra-file cleanup + validation s | 3.080 (3.080–3.080; n=1) | - |
| Full restore recovery + validation s | 4.055 (4.055–4.055; n=1) | 6.732 (6.732–6.732; n=1) |



## Gutch vs restic: PASS

Restic uses native Rabin around 1 MiB, explicit Zstd auto, 8 MiB pack targets and mandatory encryption. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3, 8 MiB compressed bundles and no encryption. Zstd auto is not an exact level-3 match; bounds, codec implementations and compression units differ. Restore retains --verify; recovery verifies existing bytes and deletes extra files. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 1 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `2987627a64436fbebeb745292a323d56e27fb0f9`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 9V45 96-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](restic.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| gutch | PASS | 5.263 | 1.156 | 0.605 | 1.185 | 689.361 | - | 144.098 | 2572.868 |
| restic | PASS | 7.144 | 4.255 | 3.167 | 4.227 | 714.022 | - | 207.535 | 2603.034 |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | gutch | restic |
|---|---:|---:|
| Initial capture s | 2.813 (2.813–2.813; n=1) | 3.683 (3.683–3.683; n=1) |
| Later-version capture s | 2.450 (2.450–2.450; n=1) | 3.462 (3.462–3.462; n=1) |
| Later-version stored growth bytes | 322167243.000 (322167243.000–322167243.000; n=1) | 332225646.000 (332225646.000–332225646.000; n=1) |
| Restore + independent validation s | 3.211 (3.211–3.211; n=1) | 6.340 (6.340–6.340; n=1) |
| Content repair + validation s | 2.700 (2.700–2.700; n=1) | 5.228 (5.228–5.228; n=1) |
| Preserved-mtime repair + validation s | 2.800 (2.800–2.800; n=1) | 5.509 (5.509–5.509; n=1) |
| Extra-file cleanup + validation s | 2.414 (2.414–2.414; n=1) | 4.946 (4.946–4.946; n=1) |
| Full restore recovery + validation s | 3.319 (3.319–3.319; n=1) | 6.300 (6.300–6.300; n=1) |



## Gutch vs rustic: PASS

Rustic explicitly uses Rabin with a 1 MiB average, 512 KiB minimum and 8 MiB maximum, Zstd 3, and 8 MiB data/tree pack targets with growth disabled. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3 and 8 MiB compressed bundles. Chunk boundaries, compression units and hashes differ; Rustic remains encrypted. Recovery verifies existing bytes and deletes extra files. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 1 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `2987627a64436fbebeb745292a323d56e27fb0f9`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 9V45 96-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](rustic.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| gutch | PASS | 5.675 | 1.297 | 0.631 | 1.175 | 689.361 | - | 206.625 | 2572.868 |
| rustic | PASS | 10.424 | 4.161 | 3.384 | 4.231 | 700.552 | - | 299.316 | 2584.065 |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | gutch | rustic |
|---|---:|---:|
| Initial capture s | 3.040 (3.040–3.040; n=1) | 5.560 (5.560–5.560; n=1) |
| Later-version capture s | 2.635 (2.635–2.635; n=1) | 4.864 (4.864–4.864; n=1) |
| Later-version stored growth bytes | 322167243.000 (322167243.000–322167243.000; n=1) | 327162415.000 (327162415.000–327162415.000; n=1) |
| Restore + independent validation s | 3.481 (3.481–3.481; n=1) | 6.462 (6.462–6.462; n=1) |
| Content repair + validation s | 2.790 (2.790–2.790; n=1) | 5.589 (5.589–5.589; n=1) |
| Preserved-mtime repair + validation s | 2.805 (2.805–2.805; n=1) | 5.623 (5.623–5.623; n=1) |
| Extra-file cleanup + validation s | 2.472 (2.472–2.472; n=1) | 5.627 (5.627–5.627; n=1) |
| Full restore recovery + validation s | 3.339 (3.339–3.339; n=1) | 6.537 (6.537–6.537; n=1) |
