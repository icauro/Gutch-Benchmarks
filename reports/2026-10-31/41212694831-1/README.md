# Linux benchmark results

Run: [41212694831, attempt 1](https://github.com/icauro/Gutch-Benchmarks/actions/runs/41212694831) | UTC date: 2026-10-31

Each pair has its own settings. Hosted-runner timings are indicative; OS cache state is uncontrolled.

## Gutch vs borg: PASS

Borg explicitly uses FastCDC fastcdc,19,23,21,2, LZ4, authenticated unencrypted storage and metadata-based resume. Gutch uses a nominal 2 MiB FastCDC target, LZ4 0 and 8 MiB compressed bundles. Bounds, hashes, compression framing and storage layout differ. Borg cannot detect preserved-mtime damage via resume and this adapter has no native extra-file cleanup. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 1 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `069814015a73d0dfed39016acc7ddd20a0eaee96`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'INTEL(R) XEON(R) PLATINUM 8573C', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](borg.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| borg | PASS | 10.875 | 8.048 | 3.194 | 8.111 | 915.635 | - | 366.406 | 2834.950 |
| gutch | PASS | 26.360 | 1.652 | 0.707 | 1.649 | 913.570 | - | 143.543 | 2797.076 |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | borg | gutch |
|---|---:|---:|
| Initial capture s | 5.465 (5.465–5.465; n=1) | 12.923 (12.923–12.923; n=1) |
| Later-version capture s | 5.409 (5.409–5.409; n=1) | 13.437 (13.437–13.437; n=1) |
| Later-version stored growth bytes | 438680720.000 (438680720.000–438680720.000; n=1) | 437891774.000 (437891774.000–437891774.000; n=1) |
| Restore + independent validation s | 11.204 (11.204–11.204; n=1) | 4.720 (4.720–4.720; n=1) |
| Content repair + validation s | 6.305 (6.305–6.305; n=1) | 3.785 (3.785–3.785; n=1) |
| Preserved-mtime repair + validation s | - | 3.798 (3.798–3.798; n=1) |
| Extra-file cleanup + validation s | - | 3.450 (3.450–3.450; n=1) |
| Full restore recovery + validation s | 11.220 (11.220–11.220; n=1) | 4.733 (4.733–4.733; n=1) |



## Gutch vs bpt: PASS

BuildPatchTool uses a 1 MiB chunk window and its internal compression with FeatureLevel=Latest. Local InstallManifest recovery uses PrevManifest. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3 and 8 MiB compressed bundles. Chunk windows are not CDC averages; codecs and formats are unmatched. No native extra-file cleanup or separate repository check is available in this adapter. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 1 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `069814015a73d0dfed39016acc7ddd20a0eaee96`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](bpt.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| buildpatchtool | PASS | 36.512 | 28.114 | 2.261 | 28.056 | 732.343 | - | 520.746 | 2615.850 |
| gutch | PASS | 4.580 | 1.924 | 1.024 | 1.921 | 689.361 | - | 155.387 | 2572.868 |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | buildpatchtool | gutch |
|---|---:|---:|
| Initial capture s | 13.548 (13.548–13.548; n=1) | 2.306 (2.306–2.306; n=1) |
| Later-version capture s | 22.965 (22.965–22.965; n=1) | 2.274 (2.274–2.274; n=1) |
| Later-version stored growth bytes | 344645846.000 (344645846.000–344645846.000; n=1) | 322167243.000 (322167243.000–322167243.000; n=1) |
| Restore + independent validation s | 31.724 (31.724–31.724; n=1) | 5.599 (5.599–5.599; n=1) |
| Content repair + validation s | 5.869 (5.869–5.869; n=1) | 4.660 (4.660–4.660; n=1) |
| Preserved-mtime repair + validation s | 5.807 (5.807–5.807; n=1) | 4.616 (4.616–4.616; n=1) |
| Extra-file cleanup + validation s | - | 4.142 (4.142–4.142; n=1) |
| Full restore recovery + validation s | 31.646 (31.646–31.646; n=1) | 5.587 (5.587–5.587; n=1) |



## Gutch vs kopia: PASS

Kopia explicitly uses DYNAMIC-4M-BUZHASH, disabled content compression and AES256-GCM-HMAC-SHA256 encryption. Gutch uses a nominal 4 MiB FastCDC target, no compression, 16 MiB bundles and no encryption. Bounds, metadata, hashes and packing differ. Kopia recovery requests native extra-file deletion. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 1 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `069814015a73d0dfed39016acc7ddd20a0eaee96`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](kopia.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| gutch | PASS | 5.390 | 1.356 | 0.788 | 1.349 | 1758.175 | - | 228.137 | 3641.682 |
| kopia | PASS | 4.549 | 9.682 | 5.116 | 2.944 | 1754.516 | - | 348.172 | 5392.070 |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | gutch | kopia |
|---|---:|---:|
| Initial capture s | 2.740 (2.740–2.740; n=1) | 2.319 (2.319–2.319; n=1) |
| Later-version capture s | 2.650 (2.650–2.650; n=1) | 2.231 (2.231–2.231; n=1) |
| Later-version stored growth bytes | 887308595.000 (887308595.000–887308595.000; n=1) | 883228376.000 (883228376.000–883228376.000; n=1) |
| Restore + independent validation s | 5.082 (5.082–5.082; n=1) | 13.400 (13.400–13.400; n=1) |
| Content repair + validation s | 4.486 (4.486–4.486; n=1) | 8.806 (8.806–8.806; n=1) |
| Preserved-mtime repair + validation s | 4.416 (4.416–4.416; n=1) | 9.008 (9.008–9.008; n=1) |
| Extra-file cleanup + validation s | 4.171 (4.171–4.171; n=1) | 8.987 (8.987–8.987; n=1) |
| Full restore recovery + validation s | 5.058 (5.058–5.058; n=1) | 6.656 (6.656–6.656; n=1) |



## Gutch vs plakar: PASS

Plakar uses native FastCDC around 1 MiB and LZ4 stream compression, with plaintext storage. Gutch uses a nominal 1 MiB FastCDC target, LZ4 0 and 8 MiB compressed bundles. Bounds, compression units/framing and packing differ. Plakar restores over existing output; this adapter has no native extra-file deletion. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 1 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `069814015a73d0dfed39016acc7ddd20a0eaee96`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](plakar.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| gutch | PASS | 3.218 | 1.757 | 0.941 | 1.768 | 913.907 | - | 141.918 | 2797.413 |
| plakar | PASS | 12.714 | 6.835 | 6.919 | 5.552 | 916.023 | - | 423.410 | 2836.303 |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | gutch | plakar |
|---|---:|---:|
| Initial capture s | 1.655 (1.655–1.655; n=1) | 7.047 (7.047–7.047; n=1) |
| Later-version capture s | 1.563 (1.563–1.563; n=1) | 5.667 (5.667–5.667; n=1) |
| Later-version stored growth bytes | 438186069.000 (438186069.000–438186069.000; n=1) | 437728976.000 (437728976.000–437728976.000; n=1) |
| Restore + independent validation s | 5.473 (5.473–5.473; n=1) | 10.570 (10.570–10.570; n=1) |
| Content repair + validation s | 4.606 (4.606–4.606; n=1) | 10.722 (10.722–10.722; n=1) |
| Preserved-mtime repair + validation s | 4.615 (4.615–4.615; n=1) | 10.839 (10.839–10.839; n=1) |
| Extra-file cleanup + validation s | 4.217 (4.217–4.217; n=1) | - |
| Full restore recovery + validation s | 5.502 (5.502–5.502; n=1) | 9.316 (9.316–9.316; n=1) |



## Gutch vs restic: PASS

Restic uses native Rabin around 1 MiB, explicit Zstd auto, 8 MiB pack targets and mandatory encryption. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3, 8 MiB compressed bundles and no encryption. Zstd auto is not an exact level-3 match; bounds, codec implementations and compression units differ. Restore retains --verify; recovery verifies existing bytes and deletes extra files. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 1 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `069814015a73d0dfed39016acc7ddd20a0eaee96`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 9V45 96-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](restic.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| gutch | PASS | 5.264 | 1.153 | 0.603 | 1.167 | 689.361 | - | 218.379 | 2572.868 |
| restic | PASS | 7.465 | 4.526 | 3.262 | 4.507 | 715.186 | - | 206.648 | 2602.667 |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | gutch | restic |
|---|---:|---:|
| Initial capture s | 2.985 (2.985–2.985; n=1) | 3.863 (3.863–3.863; n=1) |
| Later-version capture s | 2.279 (2.279–2.279; n=1) | 3.603 (3.603–3.603; n=1) |
| Later-version stored growth bytes | 322167243.000 (322167243.000–322167243.000; n=1) | 332910924.000 (332910924.000–332910924.000; n=1) |
| Restore + independent validation s | 3.292 (3.292–3.292; n=1) | 6.631 (6.631–6.631; n=1) |
| Content repair + validation s | 2.681 (2.681–2.681; n=1) | 5.374 (5.374–5.374; n=1) |
| Preserved-mtime repair + validation s | 2.724 (2.724–2.724; n=1) | 5.880 (5.880–5.880; n=1) |
| Extra-file cleanup + validation s | 2.407 (2.407–2.407; n=1) | 5.289 (5.289–5.289; n=1) |
| Full restore recovery + validation s | 3.308 (3.308–3.308; n=1) | 6.576 (6.576–6.576; n=1) |



## Gutch vs rustic: PASS

Rustic explicitly uses Rabin with a 1 MiB average, 512 KiB minimum and 8 MiB maximum, Zstd 3, and 8 MiB data/tree pack targets with growth disabled. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3 and 8 MiB compressed bundles. Chunk boundaries, compression units and hashes differ; Rustic remains encrypted. Recovery verifies existing bytes and deletes extra files. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 1 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `069814015a73d0dfed39016acc7ddd20a0eaee96`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'INTEL(R) XEON(R) PLATINUM 8573C', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](rustic.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| gutch | PASS | 6.625 | 1.736 | 0.817 | 1.714 | 689.361 | - | 169.199 | 2572.868 |
| rustic | PASS | 11.917 | 4.064 | 3.546 | 4.146 | 700.710 | - | 313.664 | 2585.928 |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | gutch | rustic |
|---|---:|---:|
| Initial capture s | 3.480 (3.480–3.480; n=1) | 6.287 (6.287–6.287; n=1) |
| Later-version capture s | 3.145 (3.145–3.145; n=1) | 5.630 (5.630–5.630; n=1) |
| Later-version stored growth bytes | 322167243.000 (322167243.000–322167243.000; n=1) | 327773412.000 (327773412.000–327773412.000; n=1) |
| Restore + independent validation s | 4.759 (4.759–4.759; n=1) | 7.121 (7.121–7.121; n=1) |
| Content repair + validation s | 3.804 (3.804–3.804; n=1) | 6.556 (6.556–6.556; n=1) |
| Preserved-mtime repair + validation s | 3.783 (3.783–3.783; n=1) | 6.544 (6.544–6.544; n=1) |
| Extra-file cleanup + validation s | 3.324 (3.324–3.324; n=1) | 6.434 (6.434–6.434; n=1) |
| Full restore recovery + validation s | 4.714 (4.714–4.714; n=1) | 7.224 (7.224–7.224; n=1) |
