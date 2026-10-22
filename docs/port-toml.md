# port.toml

One flat TOML file per port, the subset `tools/portbuild.py` reads:
`key = "string"`, `key = number`, `key = ["a", "b"]`, `#` comments. No
tables, no multi-line values.

```toml
name = "lua"                      # the package name: letters, digits, - _ .
version = "5.4.7"                 # the upstream version, as upstream writes it
revision = 1                      # this port's packaging revision (≥ 1)
description = "The Lua scripting language: lua and luac"
license = "MIT"                   # SPDX identifier of the program
homepage = "https://www.lua.org/"
source = "https://www.lua.org/ftp/lua-5.4.7.tar.gz"   # the official site
sha256 = "9fbf5e28ef86c69858f6d3d34eccc32e911c1a28b4120ff3e84aaa70cfbf1e30"
install = "bin"                   # "bin": bin/, lib/, include/, share/
                                  # "app": Name.app/
depends = []                      # packages needed at run time
build-depends = []                # ports whose include/ and lib/ it builds against
stela = "0.2.0"                   # the lowest STELA version it runs on
```

| Key | Required | Meaning |
|---|---|---|
| `name` | yes | Package and folder name (`Data:/Programs/NAME`); only `[A-Za-z0-9._-]`, not `.` or `..`. Equals the folder name under `ports/`. |
| `version` | yes | Upstream's version string. Compared as text by `pkg upgrade`. |
| `revision` | yes | Packaging revision, starts at 1; bump it when the package changes without an upstream change (a patch, a build flag, a dependency). The package version is `VERSION-REVISION` (`5.4.7-1`). |
| `description` | yes | One line, shown by `pkg search` and Setup. |
| `license` | yes | SPDX identifier (or `LicenseRef-…` for the few without one: sqlite's blessing is `blessing`). |
| `homepage` | yes | The program's site. |
| `source` | one of these | HTTPS URL of the tarball or single file on the program's official site or official GitHub release. Downloaded to `sources/` under its last path part (or `file`). |
| `local` | | A folder inside the port (`local = "crate"`) for sources that are part of Agora itself. |
| `file` | no | Name to store the download as (when the URL's last part is unhelpful, e.g. `v9.1.0800.tar.gz` → `vim-9.1.0800.tar.gz`). |
| `sha256` | yes with `source` | SHA-256 of the downloaded file, checked on every fetch. |
| `install` | yes | `bin` or `app`. |
| `depends` | no | Run-time dependencies (installed first by `pkg`, put on the test volume by `portbuild.py test`). |
| `build-depends` | no | Ports built first; their `include/` and `lib/` are merged into `$DEPS`. |
| `stela` | yes | Lowest STELA version (major.minor.patch) the package needs; goes into `PKGINFO` and the index (`docs/index.md`). |

Changes from the `stela-ports` format (applied when the ports move
here, after 2026-10-23 12:00): `revision` and `stela` become required
and reach the package; `copy-from` is removed (every source is an
official URL); `file` is documented.

## build.sh

Run with `sh -e` in the unpacked source, with these variables:

| Variable | |
|---|---|
| `SRC` | the unpacked source (for a single-file source, the folder holding it) |
| `OUT` | where to put the package's content |
| `MUSL_GCC` | STELA's `build/musl/install/bin/musl-gcc` |
| `STELA_ROOT` | the STELA checkout |
| `DEPS` | `include/` and `lib/` of `build-depends` and `depends`, merged |
| `JOBS` | parallelism for `make -j` |
| `PORT` | `ports/NAME` (for files the build needs besides patches) |

The program must be static and non-PIE (STELA loads ET_EXEC; PIE and
dynamic linking exist since STELA P13 but only for programs that need
`dlopen`, such as python3), built for x86-64 baseline (no SSSE3/SSE4/AVX:
STELA's "Pentium 4 class" rule). Paths the program needs at run time are
`/Data/Programs/NAME/...`.

## test.sh

Not a shell script: lines `portbuild.py test` turns into keystrokes and
expectations for STELA's shell in QEMU.

```
$ COMMAND      typed at the prompt, after the previous command ended
> TEXT         a line the output must contain
= CODE         the previous program's exit code
! KEYS         QEMU key names (ctrl-q) sent after the last > line appeared
# comment
```

The package is unpacked into `Data:/Programs/NAME/` (dependencies too)
and `files/` into `Data:/test/`. STELA's terminal only understands SGR
colours, so tests avoid cursor addressing (full-screen programs are
tested in their batch or ex modes).

## patches

`ports/NAME/patches/NNNN-what.patch`, applied in name order with
`patch -p1`. The first lines, before the diff, are:

```
SPDX-License-Identifier: <the program's license>
Why this change is needed on STELA, and the upstream issue if one exists.
```

`patch` ignores text before the first `---` header, so the lines cost
nothing.
