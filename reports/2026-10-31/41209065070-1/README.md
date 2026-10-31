# Linux benchmark results

Run: [41209065070, attempt 1](https://github.com/icauro/Gutch-Benchmarks/actions/runs/41209065070) | UTC date: 2026-10-31

Each pair has its own settings. Hosted-runner timings are indicative; OS cache state is uncontrolled.

## Gutch vs borg: PASS

Borg explicitly uses FastCDC fastcdc,19,23,21,2, LZ4, authenticated unencrypted storage and metadata-based resume. Gutch uses a nominal 2 MiB FastCDC target, LZ4 0 and 8 MiB compressed bundles. Bounds, hashes, compression framing and storage layout differ. Borg cannot detect preserved-mtime damage via resume and this adapter has no native extra-file cleanup. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 2 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `e90490616310f14e2bcc18a62b4070663865d2b6`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](borg.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RSS MiB |
|---|---|---|---|---|---|---|---|---|
| borg | PASS | 12.701 | 10.053 | 3.541 | 9.806 | 915.942 | - | - |
| gutch | PASS | 6.983 | 1.736 | 0.882 | 1.779 | 913.570 | - | - |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | borg | gutch |
|---|---:|---:|
| Initial capture s | 6.379 (5.604–7.154; n=2) | 3.479 (3.412–3.546; n=2) |
| Later-version capture s | 6.322 (5.556–7.088; n=2) | 3.504 (3.471–3.538; n=2) |
| Later-version stored growth bytes | 438987918.500 (438917399.000–439058438.000; n=2) | 437891796.000 (437891796.000–437891796.000; n=2) |
| Restore + independent validation s | 13.673 (13.569–13.776; n=2) | 5.358 (5.356–5.361; n=2) |
| Content repair + validation s | 7.109 (7.099–7.120; n=2) | 4.449 (4.446–4.453; n=2) |
| Preserved-mtime repair + validation s | - | 4.420 (4.416–4.424; n=2) |
| Extra-file cleanup + validation s | - | 4.079 (4.070–4.089; n=2) |
| Full restore recovery + validation s | 13.418 (13.328–13.508; n=2) | 5.408 (5.372–5.445; n=2) |



## Gutch vs bpt: PASS

BuildPatchTool uses a 1 MiB chunk window and its internal compression with FeatureLevel=Latest. Local InstallManifest recovery uses PrevManifest. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3 and 8 MiB compressed bundles. Chunk windows are not CDC averages; codecs and formats are unmatched. No native extra-file cleanup or separate repository check is available in this adapter. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 2 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `e90490616310f14e2bcc18a62b4070663865d2b6`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](bpt.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RSS MiB |
|---|---|---|---|---|---|---|---|---|
| buildpatchtool | PASS | 36.370 | 28.100 | 2.227 | 28.181 | 732.343 | - | - |
| gutch | PASS | 4.414 | 1.900 | 1.005 | 1.901 | 689.362 | - | - |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | buildpatchtool | gutch |
|---|---:|---:|
| Initial capture s | 13.274 (13.260–13.288; n=2) | 2.230 (2.230–2.231; n=2) |
| Later-version capture s | 23.096 (23.045–23.147; n=2) | 2.184 (2.181–2.187; n=2) |
| Later-version stored growth bytes | 344645859.500 (344645851.000–344645868.000; n=2) | 322167265.000 (322167265.000–322167265.000; n=2) |
| Restore + independent validation s | 31.699 (31.654–31.745; n=2) | 5.559 (5.552–5.565; n=2) |
| Content repair + validation s | 5.823 (5.820–5.825; n=2) | 4.616 (4.602–4.630; n=2) |
| Preserved-mtime repair + validation s | 5.844 (5.822–5.866; n=2) | 4.602 (4.602–4.602; n=2) |
| Extra-file cleanup + validation s | - | 4.156 (4.150–4.162; n=2) |
| Full restore recovery + validation s | 31.785 (31.741–31.828; n=2) | 5.571 (5.548–5.595; n=2) |



## Gutch vs kopia: PASS

Kopia explicitly uses DYNAMIC-4M-BUZHASH, disabled content compression and AES256-GCM-HMAC-SHA256 encryption. Gutch uses a nominal 4 MiB FastCDC target, no compression, 16 MiB bundles and no encryption. Bounds, metadata, hashes and packing differ. Kopia recovery requests native extra-file deletion. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 2 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `e90490616310f14e2bcc18a62b4070663865d2b6`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](kopia.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RSS MiB |
|---|---|---|---|---|---|---|---|---|
| gutch | PASS | 5.319 | 1.313 | 1.113 | 1.341 | 1758.175 | - | - |
| kopia | PASS | 4.564 | 7.491 | 6.295 | 2.884 | 1754.510 | - | - |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | gutch | kopia |
|---|---:|---:|
| Initial capture s | 2.707 (2.691–2.724; n=2) | 2.387 (2.372–2.403; n=2) |
| Later-version capture s | 2.612 (2.611–2.612; n=2) | 2.177 (2.159–2.195; n=2) |
| Later-version stored growth bytes | 887308617.000 (887308617.000–887308617.000; n=2) | 883231172.500 (883228604.000–883233741.000; n=2) |
| Restore + independent validation s | 4.999 (4.993–5.005; n=2) | 11.299 (10.967–11.632; n=2) |
| Content repair + validation s | 4.764 (4.421–5.107; n=2) | 9.994 (8.798–11.191; n=2) |
| Preserved-mtime repair + validation s | 4.402 (4.400–4.404; n=2) | 8.881 (8.870–8.893; n=2) |
| Extra-file cleanup + validation s | 4.164 (4.150–4.178; n=2) | 8.869 (8.850–8.889; n=2) |
| Full restore recovery + validation s | 5.040 (4.999–5.080; n=2) | 6.581 (6.578–6.584; n=2) |



## Gutch vs plakar: PASS

Plakar uses native FastCDC around 1 MiB and LZ4 stream compression, with plaintext storage. Gutch uses a nominal 1 MiB FastCDC target, LZ4 0 and 8 MiB compressed bundles. Bounds, compression units/framing and packing differ. Plakar restores over existing output; this adapter has no native extra-file deletion. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 2 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `e90490616310f14e2bcc18a62b4070663865d2b6`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 9V74 80-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](plakar.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RSS MiB |
|---|---|---|---|---|---|---|---|---|
| gutch | PASS | 6.712 | 1.392 | 0.717 | 1.349 | 913.907 | - | - |
| plakar | PASS | 11.128 | 5.351 | 14.614 | 4.239 | 916.463 | - | - |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | gutch | plakar |
|---|---:|---:|
| Initial capture s | 3.332 (3.224–3.439; n=2) | 6.417 (6.254–6.580; n=2) |
| Later-version capture s | 3.381 (3.114–3.647; n=2) | 4.711 (4.568–4.853; n=2) |
| Later-version stored growth bytes | 438186091.000 (438186091.000–438186091.000; n=2) | 438077173.500 (437904486.000–438249861.000; n=2) |
| Restore + independent validation s | 4.089 (4.076–4.102; n=2) | 8.070 (7.932–8.207; n=2) |
| Content repair + validation s | 3.359 (3.346–3.373; n=2) | 17.328 (14.613–20.044; n=2) |
| Preserved-mtime repair + validation s | 3.366 (3.363–3.369; n=2) | 13.583 (13.582–13.583; n=2) |
| Extra-file cleanup + validation s | 3.108 (3.103–3.114; n=2) | - |
| Full restore recovery + validation s | 4.036 (4.030–4.041; n=2) | 6.967 (6.824–7.110; n=2) |



## Gutch vs restic: PASS

Restic uses native Rabin around 1 MiB, explicit Zstd auto, 8 MiB pack targets and mandatory encryption. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3, 8 MiB compressed bundles and no encryption. Zstd auto is not an exact level-3 match; bounds, codec implementations and compression units differ. Restore retains --verify; recovery verifies existing bytes and deletes extra files. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 2 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `e90490616310f14e2bcc18a62b4070663865d2b6`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](restic.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RSS MiB |
|---|---|---|---|---|---|---|---|---|
| gutch | PASS | 4.575 | 1.941 | 1.031 | 1.972 | 689.362 | - | - |
| restic | PASS | 8.963 | 5.888 | 4.290 | 5.893 | 715.621 | - | - |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | gutch | restic |
|---|---:|---:|
| Initial capture s | 2.309 (2.305–2.313; n=2) | 4.547 (4.516–4.578; n=2) |
| Later-version capture s | 2.266 (2.248–2.284; n=2) | 4.416 (4.399–4.434; n=2) |
| Later-version stored growth bytes | 322167265.000 (322167265.000–322167265.000; n=2) | 333781848.500 (332836321.000–334727376.000; n=2) |
| Restore + independent validation s | 5.620 (5.592–5.649; n=2) | 9.516 (9.506–9.526; n=2) |
| Content repair + validation s | 4.670 (4.663–4.677; n=2) | 7.974 (7.932–8.017; n=2) |
| Preserved-mtime repair + validation s | 4.632 (4.624–4.640; n=2) | 7.830 (7.806–7.854; n=2) |
| Extra-file cleanup + validation s | 4.156 (4.155–4.158; n=2) | 7.659 (7.656–7.662; n=2) |
| Full restore recovery + validation s | 5.680 (5.633–5.728; n=2) | 9.519 (9.518–9.521; n=2) |



## Gutch vs rustic: PASS

Rustic explicitly uses Rabin with a 1 MiB average, 512 KiB minimum and 8 MiB maximum, Zstd 3, and 8 MiB data/tree pack targets with growth disabled. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3 and 8 MiB compressed bundles. Chunk boundaries, compression units and hashes differ; Rustic remains encrypted. Recovery verifies existing bytes and deletes extra files. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 2 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `e90490616310f14e2bcc18a62b4070663865d2b6`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 9V74 80-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](rustic.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RSS MiB |
|---|---|---|---|---|---|---|---|---|
| gutch | PASS | 6.185 | 1.404 | 0.800 | 1.489 | 689.362 | - | - |
| rustic | PASS | 11.583 | 4.356 | 3.477 | 4.424 | 699.548 | - | - |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | gutch | rustic |
|---|---:|---:|
| Initial capture s | 3.086 (3.034–3.138; n=2) | 6.194 (6.124–6.264; n=2) |
| Later-version capture s | 3.099 (2.849–3.348; n=2) | 5.389 (5.382–5.396; n=2) |
| Later-version stored growth bytes | 322167265.000 (322167265.000–322167265.000; n=2) | 326163410.000 (325672284.000–326654536.000; n=2) |
| Restore + independent validation s | 4.151 (4.126–4.176; n=2) | 7.124 (7.124–7.124; n=2) |
| Content repair + validation s | 3.474 (3.447–3.502; n=2) | 6.183 (6.137–6.229; n=2) |
| Preserved-mtime repair + validation s | 3.475 (3.463–3.486; n=2) | 6.175 (6.157–6.193; n=2) |
| Extra-file cleanup + validation s | 3.115 (3.114–3.116; n=2) | 6.128 (6.119–6.137; n=2) |
| Full restore recovery + validation s | 4.203 (4.156–4.249; n=2) | 7.155 (7.117–7.193; n=2) |



