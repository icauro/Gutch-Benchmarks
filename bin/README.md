# Local comparison executables

Executable distributions are not tracked. Install tools on PATH, configure their
paths explicitly, or place local copies under the ignored windows-x64 and
linux-x64 folders. Runtime discovery never downloads tools. manifest.json records
versions, checksums and source provenance for a previously tested local toolset;
it is a reference, not an inventory of files included in a clone.

Keep BuildPatchTool's Engine files beside its binary. On Linux, ensure installed
tools are executable and meet your host's system requirements. The previously
tested Borg 2 build required glibc 2.43 or newer. Platform folders target x86-64.

Upstreams and notices:

- Borg: https://github.com/borgbackup/borg (licenses/borg.txt).
- Restic: https://github.com/restic/restic (licenses/restic.txt).
- Kopia: https://github.com/kopia/kopia (licenses/kopia.txt).
- Plakar: https://github.com/PlakarKorp/plakar (licenses/plakar.txt).
- BuildPatchTool: Epic Games, product version 1.8.8; official package:
  https://launcher-public-service-prod06.ol.epicgames.com/launcher/api/installer/download/BuildPatchTool.zip
- Gutch: built from the source revision recorded in manifest.json.

Archives and smoke-test logs stay in .artifacts/. Retain upstream licenses with
your local distributions. Existing notices under licenses/ remain for attribution.
The repository file index excludes this local tool directory.
