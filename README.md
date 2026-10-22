# stela-ports (working name)

Recipes for building Linux programs (static, musl) that run on
[STELA](https://github.com/boring89/STELA)'s Linux personality, and for
packaging them for `pkg` (STELA's package tool, `docs/pkg.md` there).

## Licensing

- The recipes, scripts and tools in this repository: **0BSD** (`LICENSE`).
- Patches (`ports/*/patches/`): the license of the program they patch.
- Upstream sources and built binaries are **not** kept in git (`sources/`,
  `work/`, `dist/` are ignored); every package carries its program's own
  license, given in its `port.toml`.

## Layout

```
ports/NAME/port.toml   name, version, source (url or copy-from) + sha256,
                       license, homepage, install (bin|app), depends,
                       build-depends (ports built against: $DEPS),
                       stela (lowest STELA version), description
ports/NAME/build.sh    builds into $OUT (env: SRC, OUT, MUSL_GCC,
                       STELA_ROOT, JOBS, PORT)
ports/NAME/test.sh     what to type in STELA's shell and what must appear
ports/NAME/files/      test files, put in Data:/test/
ports/NAME/patches/    *.patch, applied with patch -p1 before building
tools/portbuild.py     fetch / build / package / test / index
```

## Use

Needs a STELA checkout next to this repository (or `STELA_ROOT=`) with
`make musl esp test-images ehfs-tools` done there.

```
python3 tools/portbuild.py list
python3 tools/portbuild.py all lua        # build, package, test in QEMU
python3 tools/portbuild.py all all
python3 tools/portbuild.py index          # dist/index.json
```

In STELA, `make test-ports` runs all of it (local only, not in CI).

## Ports

| port | version | license | notes |
|---|---|---|---|
| lua | 5.4.7 | MIT | lua, luac |
| sqlite | 3.54.1 | public domain (blessing) | sqlite3 shell, one thread |
| kilo | 0.0.1 | BSD-2-Clause | text editor |
| dash | 0.5.12 | BSD-3-Clause | POSIX shell |
| make | 4.4.1 | GPL-3.0-or-later | recipes run with dash |
| tcc | 0.9.27 | LGPL-2.1-or-later | C compiler with musl's headers and libc |
| busybox | 1.36.1 | GPL-2.0-only | a chosen set of applets |
| rust-hello | 0.1.0 | 0BSD | Rust std example |
| zlib | 1.3.1 | Zlib | library (static) and minigzip (P13) |
| bzip2 | 1.0.8 | bzip2-1.0.6 | library and bzip2 |
| xz | 5.6.3 | 0BSD | liblzma and xz |
| libffi | 3.4.6 | MIT | library (python3's ctypes) |
| ncurses | 6.5 | X11 | library, wide characters, built-in terminal descriptions |
| readline | 8.2 | GPL-3.0-or-later | library (builds against ncurses) |
| mbedtls | 3.6.2 | Apache-2.0 | TLS library (curl, git) |
| python3 | 3.12.7 | PSF-2.0 | modules built in; dynamically linked to musl's libc.so |
| git | 2.47.0 | GPL-2.0-only | HTTPS through libcurl; dash as its shell |
| vim | 9.1.0800 | Vim | terminal only, no runtime files |
| nano | 8.2 | GPL-3.0-or-later | |
| curl | 8.10.1 | curl | Mbed TLS |
| file | 5.45 | BSD-2-Clause | with its magic database |
| less | 668 | GPL-3.0-or-later | |
| ripgrep | 15.2.0 | MIT OR Unlicense | Rust, from crates.io (P14) |
| fd | 10.5.0 | MIT OR Apache-2.0 | Rust, from crates.io (P14) |
| wpa_supplicant | 2.11 | BSD-3-Clause | compile-only: no Wi-Fi driver interface on STELA yet; wpa_passphrase works (P14) |
