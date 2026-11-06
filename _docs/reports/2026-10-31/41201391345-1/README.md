# Gutch vs BuildPatchTool rerun

Verified [CI run 41201391345](https://github.com/icauro/Gutch-Benchmarks/actions/runs/41201391345), attempt 1.

Suite commit: `60918ca03633e6b558aac406e1abf6978d297402`. Gutch commit: `c50285368c91d127e51d52f75aab37603d810682`.

One warm-up and three measured repetitions, with the same pinned Blender inputs and Gutch revision as the original all-pairs run.

The adapter supplies an empty AppLaunch for this data-only workload. This prevents BPT from marking a payload file executable. Independent content and metadata validation remain enabled.

All 16 BPT initial/recovery validation records passed (two builds, warm-up plus three measured repetitions).

### Gutch vs BuildPatchTool (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| buildpatchtool | PASS | 25.488 | 25.503 | 1.198 | 732.343 |
| gutch | PASS | 6.018 | 1.526 | 0.446 | 689.362 |
| **Gutch relative** | - | 4.24x faster | 16.72x faster | 2.69x faster | 0.94x size |

[Machine-readable results and provenance](bpt.json). Detailed logs, raw samples and traces are available in the Actions artifacts.

The other five comparisons remain from [the original all-pairs run](https://github.com/icauro/Gutch-Benchmarks/actions/runs/41200340952).
