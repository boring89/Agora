# Building, testing and releasing

## Which STELA

`STELA_VERSION` (one line: a STELA tag, `v0.2.0`) is the STELA the ports
are built and tested against and the `built-for` of the index. An Agora
release is tagged after it: `v0.2.0` here means "the ports for STELA
0.2.0"; a second release for the same STELA is `v0.2.0-2`.

## GitHub Actions

Two workflows:

| Workflow | Trigger | What |
|---|---|---|
| `lint.yml` | every push and pull request | `tools/portbuild.py lint`: every `port.toml` has the required keys, `source` is https on the program's site (no `copy-from`), `sha256` is 64 hex digits, every patch starts with an SPDX line, every tool has the 0BSD header, `README.md`'s table lists every port. Seconds. |
| `build.yml` | `workflow_dispatch` (input: STELA tag, default `STELA_VERSION`) and tags `v*` | checkout Agora and STELA at the tag; apt `qemu-system-x86 ovmf mtools gdisk gcc`; Rust from STELA's `rust-toolchain.toml`; in STELA `make musl esp test-images ehfs-tools`; `portbuild.py fetch all` (sources cached by SHA-256), `build all`, `package all`, `test all` (QEMU, TCG), `index` signed with the `AGORA_PACKAGE_KEY` secret; on a tag, a GitHub Release with the assets below. |

Expected time for 25 ports: the builds about an hour (python3, git and
the two Rust ports dominate; STELA's `make release` measured 15 min for
22 ports locally), the QEMU tests about an hour (each boots STELA, 240 s
limit).
If it grows past the 6 h job limit, the build splits into shards along
`build-depends` (libraries first) with `work/` as an artifact.

STELA's P14 wrote the first `build.yml` (`~/stela-ports` 8d9c3c6, never
run): one job, 180 min limit, `workflow_dispatch` with inputs
`stela_ref` (STELA tag) and `release_tag` (default the same), apt
packages as STELA's CI plus `python3-cryptography`, `sources/` cached by
the hash of every `port.toml`, STELA built with `make musl esp
test-images ehfs-tools`, `portbuild.py all all`, index signed from the
secret `PKG_SIGNING_KEY` (written to `$RUNNER_TEMP` under `umask 077`
and removed), then a **draft** release with the tars, index, `.sig` and
`SHA256SUMS`. Agora keeps all of that and adds: `STELA_VERSION` as the
default of `stela_ref`, the `v*` tag trigger, the `sources/` copies and
`SOURCES.txt` among the assets, the `lint` workflow, and Agora's own
index tool in place of STELA's `pkgsign.py`.

## A release

Assets of the GitHub Release `vX.Y.Z[-N]`:

```
NAME-VERSION-REVISION-x86_64.tar   every package
index.json, index.json.sig         the signed index (urls relative)
SHA256SUMS                         of every asset
sources/NAME-VERSION.tar.*         every upstream tarball, unchanged
SOURCES.txt                        name, version, URL, SHA-256, license per port
```

The patches are in the tagged tree. STELA's own release job (its
`ci.yml`, on a `v*` tag) downloads this release by the same tag name
and bundles it as `stela-X.Y.Z-ports.tar`, so the Agora release is made
first. `pkg.conf` on a STELA then says:

```
server = https://github.com/boring89/Agora/releases/download/v0.2.0/
```

(GitHub redirects asset downloads; STELA's `fetch` follows redirects and
its TLS reaches github.com.) A "current release for STELA 0.2" pointer,
if it is ever needed, is a one-line redirect page, not a moving tag.

## Mirrors and offline installs

- A mirror is a copy of a release's assets at another URL: because the
  index's `url`s are relative, `index.json` and `.sig` are copied
  unchanged and still verify.
- `python3 tools/portbuild.py mirror DIR [URL]` downloads a release
  (default: the one for `STELA_VERSION`) into `DIR`, checking every
  SHA-256 against the index; `DIR` on a USB stick is an offline source.
- On STELA, `pkg install STICK:/python3-3.12.7-1-x86_64.tar` works
  today, one file at a time without dependencies; the ask is
  `pkg install --from STICK:/agora NAME` (reads the index there,
  verifies the signature, resolves dependencies).
