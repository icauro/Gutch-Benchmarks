# Gutch benchmarks

![Latest per-pair benchmark comparisons](reports/comparison.svg)

Compare Gutch against Borg, BuildPatchTool, Kopia, Plakar, Restic or Rustic.
Each pair uses the same Blender inputs, pair-specific settings and independent
SHA-256 output validation.

## Latest Linux results

<!-- latest-benchmarks:start -->
[Original all-pairs report](reports/2026-10-31/41200340952-1/README.md) · [Verified BPT rerun](reports/2026-10-31/41201391345-1/README.md)

UTC date: 2026-10-31. Gutch: `c50285368c91d127e51d52f75aab37603d810682`. Results combine the linked runs; suite commits are recorded in each report.

Relative rows compare unrounded medians. Storage is Gutch / other size; '-' means no valid comparison.

### Gutch vs Borg (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| borg | PASS | 8.815 | 7.575 | 2.474 | 918.275 |
| gutch | PASS | 10.708 | 1.945 | 0.514 | 913.570 |
| **Gutch relative** | - | 1.21x slower | 3.89x faster | 4.81x faster | 0.99x size |

### Gutch vs BuildPatchTool (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| buildpatchtool | PASS | 25.488 | 25.503 | 1.198 | 732.343 |
| gutch | PASS | 6.018 | 1.526 | 0.446 | 689.362 |
| **Gutch relative** | - | 4.24x faster | 16.72x faster | 2.69x faster | 0.94x size |

### Gutch vs Kopia (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| gutch | PASS | 5.621 | 1.557 | 0.650 | 1758.175 |
| kopia | PASS | 4.685 | 7.262 | 7.666 | 1754.523 |
| **Gutch relative** | - | 1.20x slower | 4.66x faster | 11.80x faster | 1.00x size |

### Gutch vs Plakar (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| gutch | PASS | 5.988 | 2.034 | 0.419 | 913.907 |
| plakar | PASS | 8.821 | 3.912 | 13.458 | 916.210 |
| **Gutch relative** | - | 1.47x faster | 1.92x faster | 32.09x faster | 1.00x size |

### Gutch vs Restic (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| gutch | PASS | 5.587 | 2.323 | 0.705 | 689.362 |
| restic | PASS | 8.969 | 5.731 | 4.002 | 714.666 |
| **Gutch relative** | - | 1.61x faster | 2.47x faster | 5.68x faster | 0.96x size |

### Gutch vs Rustic (PASS)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| gutch | PASS | 5.687 | 2.353 | 0.726 | 689.362 |
| rustic | PASS | 14.522 | 5.760 | 4.311 | 700.319 |
| **Gutch relative** | - | 2.55x faster | 2.45x faster | 5.93x faster | 0.98x size |

<!-- latest-benchmarks:end -->

## Run on GitHub

Open **Actions > Manual Linux benchmarks > Run workflow**. Choose `all` or one
pair, the Gutch revision, and repetitions. Defaults: Ubuntu 24.04, all six pairs,
one warm-up and three measured repetitions.
All six pairs can run concurrently, each on its own runner.

All jobs share a validated Blender input cache. Repositories and restored outputs
are discarded after each sample. Runs on the default branch save compact reports
in Git and update this page; detailed logs and traces remain Actions artifacts
for 30 days. Hosted-runner timings are indicative; OS caches are uncontrolled.

## Run locally

Requires Python 3.12+ and the selected tool executables on PATH or in the ignored
`.artifacts/tools/<platform>/<tool>/` folders.

```sh
python -m pip install -e .
gutch-bench
# Or select one pair:
gutch-bench --fixture gutch_vs_rustic --no-open-perfetto --discard-outputs
```

Selecting a shipped fixture downloads and checksum-verifies the pinned Blender
5.0.0 and 5.1.0 inputs if missing. Reports are written under `.artifacts/runs/`.
Local runs retain failed outputs unless `--discard-outputs` is selected.

See the [benchmark guide](docs/guide.md) for settings, custom inputs, recovery,
report interpretation and development instructions. Tool versions and checksums
are recorded in the [manifest](src/comparison_benchmark_suite/resources/tools.json).

[MIT licensed](LICENSE). External tools and workloads retain their own licenses;
see [third-party notices](docs/third-party-notices.md).
