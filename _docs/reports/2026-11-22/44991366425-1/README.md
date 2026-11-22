# Linux benchmark results

Run: [44991366425, attempt 1](https://github.com/icauro/Gutch-Benchmarks/actions/runs/44991366425) | UTC date: 2026-11-22

Each pair has its own settings. Hosted-runner timings are indicative; OS cache state is uncontrolled.

## Gutch vs cavs: PASS

CAVS packs each build with pack-dir (FastCDC 64 KiB / 256 KiB / 1 MiB, Zstd 3 per chunk) into a packfile store, and installs through cavs-client fetch from a local cavs-server serving that store. Gutch uses identical chunk bounds, Zstd 3 and 8 MiB compressed bundles; bundle and pack framing differ. CAVS capture times pack-dir plus store add; the server starts untimed after capture and its own RAM is not sampled. Every restore and repair starts with an empty client cache, so data comes from the store. Repair uses CAVS's SHA-256 no-op detection with --prune; cavs-client skips pruning when every managed file already matches, so extra-file cleanup is unsupported. Fresh repositories and isolated caches. Four workers where exposed; native Borg/BPT scheduling. One warm-up and 6 rotating measured repetitions; profiling off. Measurement contract 2 separates content repair, preserved-mtime damage, extra-file cleanup and full restoration. Strict source-derived SHA-256 validation follows every supported operation; both native and validation-inclusive durations are reported. Unsupported operations receive no timing.

Suite commit: `5c34854b626cb97919dd468e80000e6bd0be3d39`; Gutch release: `0.1.0`; Gutch commit: `c3465e71fd0859c49a40c55f2c0e49212633d8fc`.

Host: `{'cpu_count': 4, 'cpu_model': 'Intel(R) Xeon(R) 6975P-C', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1014-aws-x86_64-with-glibc2.39'}`

[Machine-readable report](cavs.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RAM MiB | Peak disk MiB |
|---|---|---|---|---|---|---|---|---|---|
| [Gutch](https://github.com/icauro/Gutch) | PASS | 3.624 | 1.382 | 0.716 | 1.383 | 679.349 | - | 167.902 | 2562.855 |
| [CAVS](https://github.com/terragov/cavs) | PASS | 10.745 | 6.731 | 5.555 | 6.606 | 712.400 | - | 255.590 | 4442.106 |

Median (minimum–maximum; measured samples). '-' means unavailable or unsupported.

| Measurement | [Gutch](https://github.com/icauro/Gutch) | [CAVS](https://github.com/terragov/cavs) |
|---|---:|---:|
| First capture s | 1.800 (1.789–1.814; n=6) | 5.472 (4.591–5.564; n=6) |
| Later-version capture s | 1.822 (1.806–1.833; n=6) | 5.269 (5.263–5.301; n=6) |
| Later-version stored growth bytes | 314154379.000 (314154379.000–314154379.000; n=6) | 331724047.000 (331724047.000–331724047.000; n=6) |
| Restore + independent validation s | 3.878 (3.865–3.913; n=6) | 9.230 (9.107–9.320; n=6) |
| Content repair + validation s | 3.189 (3.165–3.197; n=6) | 8.046 (7.714–8.436; n=6) |
| Preserved-mtime repair + validation s | 3.182 (3.170–3.221; n=6) | 6.411 (6.382–6.588; n=6) |
| Extra-file cleanup + validation s | 2.823 (2.809–2.848; n=6) | - |
| Full restore recovery + validation s | 3.894 (3.882–3.911; n=6) | 9.095 (8.842–9.385; n=6) |
