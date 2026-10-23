# Agora

Ports and packages for [STELA](https://github.com/boring89/STELA): recipes
that build Linux programs (static musl, or dynamically linked against
STELA's own musl `libc.so`) so that they run on STELA's Linux personality,
and the packages `pkg` (STELA's package tool, `docs/pkg.md` there)
installs from them. *Agora* (ἀγορά) is the marketplace of a Greek city,
next to STELA's Mouseion, Kalamos and Periplus.

> Status (2026-10-23): the recipes (25 ports) still live in
> `~/stela-ports` (the working name, last commit 8d9c3c6) and move here
> next. This repository holds the design: this README, `LICENSE` and
> `docs/`. Nothing is published yet; the signing keys STELA ships are
> test keys.

## Licensing

| What | License |
|---|---|
| Recipes (`ports/*/port.toml`, `build.sh`, `test.sh`, `files/`), `tools/`, `docs/` | **0BSD** (`LICENSE`) |
| Patches (`ports/*/patches/*.patch`) | the license of the program they patch; every patch starts with an `SPDX-License-Identifier:` line |
| Upstream sources and built packages | each program's own license, named in its `port.toml` (`license`, an SPDX identifier) |
| `pkg`, `pkgcore`, Setup.app (the package tool itself) | GPL-3.0-or-later, in the STELA repository, not here |

Rules that follow from the licenses:

- Upstream sources and binaries are never committed (`sources/`, `work/`,
  `dist/` are ignored). A GitHub Release that carries binaries also
  carries a copy of **every** upstream tarball it was built from and a
  `SOURCES.txt` (name, version, URL, SHA-256, license): the source
  obligation of the GPL ports, applied to all ports for simplicity.
- GPL-2.0-only ports (BusyBox, git) are separate programs in their own
  package folders. Nothing of theirs is linked into STELA, and nothing of
  STELA's is linked into them.
- Sources come only from the program's official site (or its official
  GitHub release), with the tarball's SHA-256 in `port.toml`.

## Layout

```
ports/NAME/port.toml   name, version, revision, source + sha256, license,
                       homepage, install (bin|app), depends,
                       build-depends, stela (lowest STELA version),
                       toolchain (musl|rust), description
                                                       (docs/port-toml.md)
ports/NAME/build.sh    builds into $OUT (env: SRC, OUT, MUSL_GCC,
                       STELA_ROOT, JOBS, PORT, DEPS)
ports/NAME/test.sh     what to type in STELA's shell and what must appear
ports/NAME/files/      test files, put in Data:/test/
ports/NAME/patches/    *.patch, applied with patch -p1 before building
tools/portbuild.py     fetch / build / package / test / index / mirror
keys/                  public keys (hex) that signed indexes are checked
                       against                        (docs/signing.md)
docs/                  port.toml spec, index.json spec, signing, releases
STELA_VERSION          the STELA tag the ports are built and tested
                       against                        (docs/release.md)
```

## Use

Needs a STELA checkout (`STELA_ROOT=`, default `../STELA`) with
`make musl esp test-images ehfs-tools` done there, and QEMU + OVMF.

```
python3 tools/portbuild.py list
python3 tools/portbuild.py all lua        # fetch, build, package, test in QEMU
python3 tools/portbuild.py all all
python3 tools/portbuild.py index          # dist/index.json (+ .sig with PKG_SIGNING_KEY)
```

In STELA, `make test-ports` runs all of it (local only, not in STELA's CI).

## Adding a port

1. `ports/NAME/port.toml`: fill in every field of `docs/port-toml.md`.
   `source` is the official URL; `sha256` is the tarball's checksum
   (`sha256sum`), checked on every fetch.
2. `build.sh`: runs with `sh -e` inside the unpacked source. C programs
   are built with `$MUSL_GCC -O2 -static -no-pie -fno-pie
   -Wl,-z,max-page-size=4096`; Rust programs for
   `x86_64-unknown-linux-musl` with `-C relocation-model=static -C
   target-feature=+crt-static`. Put what the package holds in `$OUT`:
   `bin/`, `lib/`, `include/`, `share/`, or `Name.app/`.
3. Patches: as few as possible, one change per file, named
   `NNNN-what-it-does.patch`, first line
   `SPDX-License-Identifier: <the program's license>`, then a sentence on
   why, then the diff (`patch -p1`).
4. `test.sh`: at least one `$` command and one `>` line that proves the
   program ran on STELA (`python3 tools/portbuild.py test NAME` runs it in
   QEMU). A port without a test is not merged.
5. Add the port to the table below, in the same style.

## Contributing

- One port (or one fix) per commit; messages `ports/NAME: ...` or
  `tools: ...`, lowercase, imperative.
- Keep `build.sh` reproducible: no network during the build (everything
  comes from the fetched tarball and `$DEPS`; the exception is a `rust`
  port's `cargo build --locked`, pinned by the crate's `Cargo.lock`), no
  absolute host paths baked in except `/Data/Programs/NAME` where the
  program needs one.
- Patches that would be useful upstream should be sent upstream too;
  note the upstream issue or PR in the patch header.
- Nothing from a non-official mirror, nothing without a license, no
  firmware or other binary blobs.

## Ports

| port | version | license | notes |
|---|---|---|---|
| lua | 5.4.7 | MIT | lua, luac |
| sqlite | 3.54.1 | public domain (blessing) | sqlite3 shell and `libsqlite3.a` |
| kilo | 0.0.1 | BSD-2-Clause | text editor |
| dash | 0.5.12 | BSD-3-Clause | POSIX shell |
| make | 4.4.1 | GPL-3.0-or-later | recipes run with dash |
| tcc | 0.9.27 | LGPL-2.1-or-later | C compiler with musl's headers and libc |
| busybox | 1.36.1 | GPL-2.0-only | a chosen set of applets |
| rust-hello | 0.1.0 | 0BSD | Rust std example |
| zlib | 1.3.1 | Zlib | library (static) and minigzip |
| bzip2 | 1.0.8 | bzip2-1.0.6 | library and bzip2 |
| xz | 5.6.3 | 0BSD | liblzma and xz |
| libffi | 3.4.6 | MIT | library (python3's ctypes) |
| ncurses | 6.5 | X11 | library, wide characters, built-in terminal descriptions |
| readline | 8.2 | GPL-3.0-or-later | libreadline, libhistory |
| mbedtls | 3.6.2 | Apache-2.0 | TLS, X.509 and crypto libraries |
| python3 | 3.12.7 | PSF-2.0 | extension modules built in; no ssl; dynamically linked |
| git | 2.47.0 | GPL-2.0-only | HTTPS through libcurl and Mbed TLS |
| vim | 9.1.0800 | Vim | terminal only, no runtime files |
| nano | 8.2 | GPL-3.0-or-later | |
| curl | 8.10.1 | curl | curl and libcurl (Mbed TLS, zlib) |
| file | 5.45 | BSD-2-Clause | with its magic database |
| less | 668 | GPL-3.0-or-later | |
| ripgrep | 15.2.0 | Unlicense OR MIT | rg; Rust, from crates.io |
| fd | 10.5.0 | MIT OR Apache-2.0 | Rust, from crates.io |
| wpa_supplicant | 2.11 | BSD-3-Clause | compile-only: STELA has no Wi-Fi driver interface yet; wpa_passphrase works |

See `docs/` for the port.toml and index formats, signing and releases;
STELA's `docs/ports.md`, `docs/pkg.md` and `docs/linux.md` for what the
system offers a port.
