# Gutch benchmarks

Compare Gutch against Borg, BuildPatchTool, Kopia, Plakar, Restic or Rustic.
Each pair uses the same Blender inputs, pair-specific settings and independent
SHA-256 output validation.

## Latest Linux results

<!-- latest-benchmarks:start -->
No GitHub Actions benchmark reports have been published yet.
<!-- latest-benchmarks:end -->

## Run on GitHub

Open **Actions > Manual Linux benchmarks > Run workflow**. Choose `all` or one
pair, the Gutch revision, and repetitions. Defaults: Ubuntu 24.04, all six pairs,
one warm-up and three measured repetitions.

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
