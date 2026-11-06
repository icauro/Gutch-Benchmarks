# Linux benchmark results

Run: [41200340952, attempt 1](https://github.com/icauro/Gutch-Benchmarks/actions/runs/41200340952) | UTC date: 2026-10-31

Each pair has its own settings. Hosted-runner timings are indicative; OS cache state is uncontrolled.

## Gutch vs borg: PASS

Borg 2 keeps default FastCDC (about 2 MiB, normalization 2), LZ4 and cache policy. Repository creation uses --encryption authenticated-sha256: payloads are unencrypted but authenticated, with a fixed local test passphrase protecting the key. Restore and recovery use --continue for the shared output directory; repository check uses --verify-data. Gutch uses unencrypted FastCDC with a 2 MiB target, LZ4 0 and 8 MiB bundles. Normalization, chunk bounds, hash algorithms, LZ4 framing and storage layout differ. Borg resume uses metadata checks; independent validation still checks contents. Fresh local repositories and isolated caches; automatic workers; noninteractive/output flags. One warm-up and 3 rotating measured repetitions, profiling off. Independent validation is outside timings; extra files are allowed.

Suite commit: `aeccad4d48f6caab6650733958cf4f3e4a8dbe57`; Gutch commit: `c50285368c91d127e51d52f75aab37603d810682`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 9V74 80-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](borg.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RSS MiB |
|---|---|---|---|---|---|---|---|---|
| borg | PASS | 8.815 | 7.575 | 2.474 | - | 918.275 | - | - |
| gutch | PASS | 10.708 | 1.945 | 0.514 | - | 913.570 | - | - |


## Gutch vs bpt: ERROR

BuildPatchTool keeps its default 1 MiB chunk window and internal compression. Local ChunkBuildDirectory specifies FeatureLevel=Latest, artifact/version/launch metadata and manifest filenames; no upload, authentication or encryption is enabled. Recovery uses InstallManifest with PrevManifest. Gutch uses unencrypted FastCDC with a 1 MiB target, Zstd 3 and 8 MiB bundles. BPT chunk windows are not CDC averages; compression codec/level and artifact formats are unmatched. There is no separate repository-check phase for BPT. Fresh local repositories and isolated caches; automatic workers; noninteractive/output flags. One warm-up and 3 rotating measured repetitions, profiling off. Independent validation is outside timings; extra files are allowed.

Suite commit: `aeccad4d48f6caab6650733958cf4f3e4a8dbe57`; Gutch commit: `c50285368c91d127e51d52f75aab37603d810682`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](bpt.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RSS MiB |
|---|---|---|---|---|---|---|---|---|
| buildpatchtool | ERROR | - | - | - | - | - | - | - |
| gutch | PASS | 5.668 | 2.333 | 0.721 | - | 689.362 | - | - |

output validation failed; see /home/runner/work/Gutch-Benchmarks/Gutch-Benchmarks/.artifacts/runs/2026.10.31-gutch_vs_bpt-comparison-001/lanes/buildpatchtool-sample-001/stats/validate-restored-v1.json: ['different: blender.exe']
output validation failed; see /home/runner/work/Gutch-Benchmarks/Gutch-Benchmarks/.artifacts/runs/2026.10.31-gutch_vs_bpt-comparison-001/lanes/buildpatchtool-sample-002/stats/validate-restored-v1.json: ['different: blender.exe']
output validation failed; see /home/runner/work/Gutch-Benchmarks/Gutch-Benchmarks/.artifacts/runs/2026.10.31-gutch_vs_bpt-comparison-001/lanes/buildpatchtool-sample-003/stats/validate-restored-v1.json: ['different: blender.exe']

## Gutch vs kopia: PASS

Kopia keeps default 4 MiB Buzhash chunking and disabled file compression. Encryption remains AES256-GCM-HMAC-SHA256: no supported plaintext mode. Recovery adds --delete-extra; repository verification uses --verify-files-percent=100. Gutch uses unencrypted FastCDC with a 4 MiB target, compression off and 16 MiB bundles. Chunk bounds, metadata compression, hashes and storage layout differ. Fresh local repositories and isolated caches; automatic workers; noninteractive/output flags. One warm-up and 3 rotating measured repetitions, profiling off. Independent validation is outside timings; extra files are allowed.

Suite commit: `aeccad4d48f6caab6650733958cf4f3e4a8dbe57`; Gutch commit: `c50285368c91d127e51d52f75aab37603d810682`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](kopia.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RSS MiB |
|---|---|---|---|---|---|---|---|---|
| gutch | PASS | 5.621 | 1.557 | 0.650 | - | 1758.175 | - | - |
| kopia | PASS | 4.685 | 7.262 | 7.666 | - | 1754.523 | - | - |


## Gutch vs plakar: PASS

Plakar keeps default FastCDC (about 1 MiB), LZ4 stream compression and backup-cache policy. Repository creation disables encryption with -plaintext; the adapter uses -stdio, -quiet and -no-progress. Recovery restores over existing output; repository check is separate. Gutch uses unencrypted FastCDC with a 1 MiB target, LZ4 0 and 8 MiB bundles. Chunk bounds, LZ4 implementation/framing, metadata and storage layout differ; stored Plakar level 9 is not passed to its stream writer. Fresh local repositories and isolated caches; automatic workers; noninteractive/output flags. One warm-up and 3 rotating measured repetitions, profiling off. Independent validation is outside timings; extra files are allowed.

Suite commit: `aeccad4d48f6caab6650733958cf4f3e4a8dbe57`; Gutch commit: `c50285368c91d127e51d52f75aab37603d810682`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 9V45 96-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](plakar.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RSS MiB |
|---|---|---|---|---|---|---|---|---|
| gutch | PASS | 5.988 | 2.034 | 0.419 | - | 913.907 | - | - |
| plakar | PASS | 8.821 | 3.912 | 13.458 | - | 916.210 | - | - |


## Gutch vs restic: PASS

Restic keeps default Rabin chunking (about 1 MiB) and Zstd auto. Encryption is mandatory and remains enabled. Restore adds --verify; recovery adds --overwrite always --delete, scoped to the selected build. Repository check uses --read-data. Gutch uses unencrypted FastCDC with a 1 MiB target, Zstd 3 and 8 MiB bundles; chunk bounds, Zstd implementations, hashes and storage layout differ. Fresh local repositories and isolated caches; automatic workers; noninteractive/output flags. One warm-up and 3 rotating measured repetitions, profiling off. Independent validation is outside timings; extra files are allowed.

Suite commit: `aeccad4d48f6caab6650733958cf4f3e4a8dbe57`; Gutch commit: `c50285368c91d127e51d52f75aab37603d810682`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](restic.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RSS MiB |
|---|---|---|---|---|---|---|---|---|
| gutch | PASS | 5.587 | 2.323 | 0.705 | - | 689.362 | - | - |
| restic | PASS | 8.969 | 5.731 | 4.002 | - | 714.666 | - | - |


## Gutch vs rustic: PASS

Rustic uses native Rabin chunking (about 1 MiB, 512 KiB minimum and 8 MiB maximum), default pack sizing, and repository Zstd level 3. Gutch uses FastCDC with a 1 MiB target, Zstd 3 and 8 MiB bundles. Algorithms, chunk bounds, compression implementations and packing differ; Rustic remains encrypted. Backup paths and per-source tags select each version independently. Restore verifies existing bytes; recovery requests deletion only inside the selected version directory. A full repository data check and independent SHA-256 validation are separate from capture and restore timings. Fresh repositories, isolated profiles and caches, automatic workers and noninteractive commands. One warm-up and 3 rotating measured repetitions, profiling off. Extra files are allowed by the shared validator; native deletion is requested for recovery.

Suite commit: `aeccad4d48f6caab6650733958cf4f3e4a8dbe57`; Gutch commit: `c50285368c91d127e51d52f75aab37603d810682`.

Host: `{'cpu_count': 4, 'cpu_model': 'AMD EPYC 7763 64-Core Processor', 'disk_bytes': 154894188544, 'platform': 'Linux-7.0.0-1017-azure-x86_64-with-glibc2.39'}`

[Machine-readable report](rustic.json)

| Tool | Status | Capture s | Restore s | Repair s | Recovery s | Stored MiB | CPU % | Peak RSS MiB |
|---|---|---|---|---|---|---|---|---|
| gutch | PASS | 5.687 | 2.353 | 0.726 | - | 689.362 | - | - |
| rustic | PASS | 14.522 | 5.760 | 4.311 | - | 700.319 | - | - |


