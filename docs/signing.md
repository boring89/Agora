# Signing

Two ed25519 keys, two very different lives:

| Key | Signs | Private half lives | Public half |
|---|---|---|---|
| **package key** | `index.json` of every Agora release | the user's machine (offline copy) **and** a GitHub Actions secret, so the release workflow can sign | `keys/agora-packages.pub`, STELA's `tools/pkg.pub` → `Initrd:/certs/pkg.pub` |
| **system key** | STELA's System images (`stela-update`, STELA P14) | the user's machine only; never in CI | STELA's `tools/system.pub` → `Initrd:/certs/system.pub` (exists since STELA a568631; a test key until replaced) |

Why two: a leaked CI secret must not be able to sign a System image
that the loader boots automatically. Packages are installed on request
and run as sandboxed programs; the System image is the system.

## Making a key

On the user's machine, with Python's `cryptography`:

```bash
python3 tools/portbuild.py keygen agora-packages   # agora-packages.key (hex seed, mode 600) + keys/agora-packages.pub
```

or with OpenSSL (`openssl genpkey -algorithm ed25519`) and a conversion
to the 32-byte raw seed. The `.key` file is listed in `.gitignore`; keep
a copy off the machine (printed or on a stick in a drawer). The public
key is 32 bytes in hex, one line.

STELA's current `tools/pkg.pub` is a **test key** with a fixed seed
(`tools/pkgsign.py keygen`); it is replaced by the package key's public
half before anything is published. STELA's CI keeps signing its own test
packages with the test key, read from `Initrd:/certs/` only in
`make test-pkg`'s image (a STELA-side change: `docs/stela-requests.md`).

## Signing an index

```bash
PKG_SIGNING_KEY=~/agora-packages.key python3 tools/portbuild.py index
python3 tools/portbuild.py verify keys/agora-packages.pub dist/index.json   # what pkg does, plus every listed file
```

In the release workflow the key comes from the secret
`PKG_SIGNING_KEY` (the hex seed; the name STELA's P14 `build.yml` and
`docs/release.md` use), only in the `release` environment, only on
`workflow_dispatch` and `v*` tags (`docs/release.md`). STELA's
`tools/pkgsign.py verify PUB INDEX` checks a signed index against the
`.tar` files next to it; STELA's `make release` reuses a ports index
only when that check passes.

## Rotation

`Initrd:/certs/pkg.pub` holds one key today. The ask to STELA is one
key per line: `pkg` accepts a signature by any of them, so a new key can
ship in a STELA release while indexes are still signed with the old one,
and the old one is dropped a release later. `keys/` here keeps every
key with its dates in `keys/README.md`.
