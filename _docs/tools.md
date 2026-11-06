# Local comparison tools

The [tool manifest](../src/comparison_benchmark_suite/resources/tools.json) records
versions, checksums and upstream sources. It describes a reference toolset;
executables and vendor runtimes are not included in Git or Python packages.

Supply tools through explicit fixture paths, PATH, or these ignored folders in
your working directory:

- `.artifacts/tools/windows-x64/<tool>/`
- `.artifacts/tools/linux-x64/<tool>/`

Gutch uses `gutch/gutch-cli.exe` or `gutch/gutch-cli`. BuildPatchTool keeps its
complete `Engine/Binaries/Win64/` or `Engine/Binaries/Linux/` layout under
`buildpatchtool/`. Keep its support files alongside the executable.

The local runner never downloads executables. Manual CI explicitly provisions
its selected tool and verifies both archive and executable checksums. Borg uses
the latest recorded 2.x prerelease for FastCDC; its recorded Linux asset requires
glibc 2.39 or newer. Other external tools track stable releases.

Keep download archives and validation logs under `.artifacts/`. Preserve each
tool's upstream notices with local distributions; see
[third-party notices](third-party-notices.md).
