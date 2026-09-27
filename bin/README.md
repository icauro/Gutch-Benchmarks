# Bundled comparison executables

These files ship with the repository. Runtime discovery selects windows-x64 or
linux-x64 without downloading tools. manifest.json records executable versions,
SHA-256 checksums and the Gutch source revision used for these builds.

Keep BuildPatchTool's Engine files beside each binary. Linux executable modes
are tracked in Git. Linux Borg 2 requires glibc 2.43 or newer; all six Linux tools
were smoke-tested in Debian unstable. Windows tools target x86-64.

Upstreams and notices:

- Borg: https://github.com/borgbackup/borg (licenses/borg.txt).
- Restic: https://github.com/restic/restic (licenses/restic.txt and restic-windows.txt).
- Kopia: https://github.com/kopia/kopia (licenses/kopia.txt).
- Plakar: https://github.com/PlakarKorp/plakar (licenses/plakar.txt and plakar-linux.txt).
- BuildPatchTool: Epic Games, product version 1.8.8; official package:
  https://launcher-public-service-prod06.ol.epicgames.com/launcher/api/installer/download/BuildPatchTool.zip
- Gutch: built from the source revision recorded in manifest.json.

Old versions, archives and smoke-test logs stay in .artifacts/ and do not ship.
After refreshing a binary, update its checksum and version in manifest.json.
