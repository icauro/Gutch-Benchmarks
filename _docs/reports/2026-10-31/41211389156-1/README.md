# Linux benchmark results

Run: [41211389156, attempt 1](https://github.com/icauro/Gutch-Benchmarks/actions/runs/41211389156) | UTC date: 2026-10-31

Each pair has its own settings. Hosted-runner timings are indicative; OS cache state is uncontrolled.

## Gutch vs rustic: PASS

Rustic explicitly uses Rabin with a 1 MiB average, 512 KiB minimum and 8 MiB maximum, Zstd 3, and 8 MiB data/tree pack targets with growth disabled. Gutch uses a nominal 1 MiB FastCDC target, Zstd 3 and 8 MiB compressed bundles. Chunk boundaries, compression units and hashes differ; Rustic remains encrypted. Recovery verifies existing bytes and deletes extra files. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 1 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `e0b66b88c3e56e7eeaa11d69ab5b58d7c7c28a43`; Gutch commit: `c0892bd236f83ad6b4973968beacba72d28d2f4b`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 9V45 96-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](rustic.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| gutch | PASS | 5.290 | 1.114 | 0.610 | 1.132 | 689.361 | - | 217.605 | 2572.626 |
| rustic | PASS | 9.856 | 3.920 | 3.313 | 4.029 | 694.532 | - | 321.691 | 2583.575 |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | gutch | rustic |
|---|---:|---:|
| Initial capture s | 2.714 (2.714–2.714; n=1) | 5.264 (5.264–5.264; n=1) |
| Later-version capture s | 2.576 (2.576–2.576; n=1) | 4.593 (4.593–4.593; n=1) |
| Later-version stored growth bytes | 322167243.000 (322167243.000–322167243.000; n=1) | 322367611.000 (322367611.000–322367611.000; n=1) |
| Restore + independent validation s | 3.304 (3.304–3.304; n=1) | 6.065 (6.065–6.065; n=1) |
| Content repair + validation s | 2.639 (2.639–2.639; n=1) | 5.407 (5.407–5.407; n=1) |
| Preserved-mtime repair + validation s | 2.633 (2.633–2.633; n=1) | 5.383 (5.383–5.383; n=1) |
| Extra-file cleanup + validation s | 2.330 (2.330–2.330; n=1) | 5.266 (5.266–5.266; n=1) |
| Full restore recovery + validation s | 3.301 (3.301–3.301; n=1) | 6.216 (6.216–6.216; n=1) |
