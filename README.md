# Gutch benchmarks

Compare Gutch against Borg, BuildPatchTool, Kopia, Plakar, Restic or Rustic.
Each pair uses the same Blender inputs, pair-specific settings and independent
SHA-256 output validation.

## Latest Linux results

<!-- latest-benchmarks:start -->
[Full report](reports/2026-10-31/41198638034-1/README.md) · [Actions logs and artifacts](https://github.com/icauro/Gutch-Benchmarks/actions/runs/41198638034)

UTC date: 2026-10-31. Suite: `add9a9e17089ac8ab5dec875784888b5d15117a7`. Gutch: `unknown`.

Relative rows compare unrounded medians. Storage is Gutch / other size; '-' means no valid comparison.

### Gutch vs Borg (ERROR)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| gutch | NOT_RUN | - | - | - | - |
| borg | NOT_RUN | - | - | - | - |
| **Gutch relative** | - | - | - | - | - |

### Gutch vs BuildPatchTool (ERROR)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| gutch | NOT_RUN | - | - | - | - |
| buildpatchtool | NOT_RUN | - | - | - | - |
| **Gutch relative** | - | - | - | - | - |

### Gutch vs Kopia (ERROR)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| gutch | NOT_RUN | - | - | - | - |
| kopia | NOT_RUN | - | - | - | - |
| **Gutch relative** | - | - | - | - | - |

### Gutch vs Plakar (ERROR)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| gutch | NOT_RUN | - | - | - | - |
| plakar | NOT_RUN | - | - | - | - |
| **Gutch relative** | - | - | - | - | - |

### Gutch vs Restic (ERROR)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| gutch | NOT_RUN | - | - | - | - |
| restic | NOT_RUN | - | - | - | - |
| **Gutch relative** | - | - | - | - | - |

### Gutch vs Rustic (ERROR)

| Tool | Status | Capture s | Restore s | Repair s | Stored MiB |
|---|---|---:|---:|---:|---:|
| gutch | NOT_RUN | - | - | - | - |
| rustic | NOT_RUN | - | - | - | - |
| **Gutch relative** | - | - | - | - | - |

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
`bin/<platform>/<tool>/` folders.

```sh
python -m pip install -e .
python run.py
# Or select one pair:
python run.py --fixture gutch_vs_rustic --no-open-perfetto --discard-outputs
```

Selecting a shipped fixture downloads and checksum-verifies the pinned Blender
5.0.0 and 5.1.0 inputs if missing. Reports are written under `.artifacts/runs/`.
Local runs retain failed outputs unless `--discard-outputs` is selected.

See the [benchmark guide](docs/guide.md) for settings, custom inputs, recovery,
report interpretation and development instructions. Tool versions and checksums
are recorded in the [manifest](bin/manifest.json).

[MIT licensed](LICENSE). External tools and workloads retain their own licenses;
see [third-party notices](THIRD_PARTY_NOTICES.md).
