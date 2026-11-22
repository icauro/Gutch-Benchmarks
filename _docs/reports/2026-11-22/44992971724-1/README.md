# Linux benchmark results

Run: [44992971724, attempt 1](https://github.com/icauro/Gutch-Benchmarks/actions/runs/44992971724) | UTC date: 2026-11-22

Each pair has its own settings. Hosted-runner timings are indicative; OS cache state is uncontrolled.

## Gutch vs cavs: PASS

CAVS packs each build with pack-dir (FastCDC 64 KiB / 256 KiB / 1 MiB, Zstd 3 per chunk) into a packfile store, and installs through cavs-client fetch from a local cavs-server serving that store. Gutch uses identical chunk bounds, Zstd 3 and 8 MiB compressed bundles; bundle and pack framing differ. CAVS capture times pack-dir plus store add; the server starts untimed after capture, and its RAM is added to every fetch's sampled RAM. Every restore and repair starts with an empty client cache, so data comes from the store. Repair uses CAVS's SHA-256 no-op detection with --prune; cavs-client skips pruning when every managed file already matches, so extra-file cleanup is unsupported. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 6 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `67b2ca52dbda1e943c16db5bcfe6f44693b22eba`; Gutch release: `0.1.0`; Gutch commit: `c3465e71fd0859c49a40c55f2c0e49212633d8fc`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](cavs.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 4.387 | 1.885 | 1.043 | 1.901 | 679.349 | - | 185.824 | 2562.855 |
| [CAVS](https://github.com/terragov/cavs) | PASS | 10.646 | 7.057 | 4.871 | 7.192 | 712.400 | - | 256.434 | 4322.165 |

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
