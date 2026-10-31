# Third-party notices

Original comparison-suite code, fixtures and documentation are licensed under
the [MIT License](LICENSE), copyright (c) 2026 icauro. External programs,
downloaded datasets, package dependencies and retained upstream notices keep
their own licenses. The project license does not grant rights to those works.

## External comparison programs

The source repository and Python packages do not include comparison executables
or vendor runtime distributions. Users supply them via fixture configuration,
PATH, or ignored local platform folders. This suite invokes their command-line
interfaces; the notice copies below are attribution references, not grants from
this project or a complete set of notices for a particular binary distribution.

| Program | Upstream | Retained notice |
| --- | --- | --- |
| Borg | [borgbackup/borg](https://github.com/borgbackup/borg) | BSD-3-Clause; [notice](bin/licenses/borg.txt). |
| Restic | [restic/restic](https://github.com/restic/restic) | BSD-2-Clause; [notice](bin/licenses/restic.txt). |
| Kopia | [kopia/kopia](https://github.com/kopia/kopia) | Apache-2.0; [license](bin/licenses/kopia.txt). |
| Plakar | [PlakarKorp/plakar](https://github.com/PlakarKorp/plakar) | ISC; [notice](bin/licenses/plakar.txt). |
| BuildPatchTool | Epic Games | Supplied and licensed by Epic Games under its applicable terms; this project supplies no Epic executable, runtime files or redistribution permission. |
| Gutch | User-supplied executable | Original Gutch code is MIT; included third-party code and linked dependencies carry additional terms. Preserve the notices accompanying the executable you use. |

`bin/manifest.json` records a previously tested local toolset, not the contents
of a clone or Python package. These reference notices do not replace the notices
that accompany the actual versions you install. Redistribution of a tool or its
runtime requires checking that distribution's own terms and dependencies.

## Python dependencies and workloads

The suite installs PyYAML (MIT), psutil (BSD-3-Clause) and Textual (MIT) through
the package requirements. Their transitive dependencies retain their own terms;
they are not copied into this source repository or the suite's wheel. Retain
their package license/notice files if bundling a Python environment.

Blender and other workload files are user-supplied and ignored by Git. Their
software and assets keep their original licenses; they are not covered by the
suite's MIT license. The fixture YAML describes inputs and commands without
including those third-party payloads.
