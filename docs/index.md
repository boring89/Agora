# index.json

What `pkg update` downloads, verifies and keeps in `Data:/.pkg/index.json`.
`format` stays **1**: `pkgcore` ignores fields it does not know, so the
fields below are added without breaking the `pkg` of STELA 0.1.0; `pkg`
gains checks for them one by one (`docs/stela-requests.md`).

```json
{
 "format": 1,
 "built-for": "0.2.0",
 "serial": 3,
 "generated": "2026-11-01T10:00:00Z",
 "packages": [
  {
   "name": "lua",
   "version": "5.4.7-1",
   "upstream": "5.4.7",
   "revision": 1,
   "description": "The Lua scripting language: lua and luac",
   "license": "MIT",
   "homepage": "https://www.lua.org/",
   "install": "bin",
   "depends": [],
   "stela": "0.2.0",
   "size": 345600,
   "sha256": "…",
   "file": "lua-5.4.7-1-x86_64.tar",
   "url": "lua-5.4.7-1-x86_64.tar"
  }
 ]
}
```

| Field | Since | Meaning |
|---|---|---|
| `format` | 0.1.0 | Always 1. |
| `built-for` | Agora 1 | The STELA release these packages were built and tested on (`STELA_VERSION`). `pkg` compares major.minor with the running system and refuses an index for a newer one; a release of Agora exists per STELA release (`docs/release.md`). |
| `serial` | Agora 1 | Increases with every published index. `pkg update` refuses a `serial` lower than the one it already has, so a signed but old index cannot be replayed to hide an update. |
| `generated` | Agora 1 | When the index was made (UTC, RFC 3339); informational. |
| `system` | STELA P14 | Reserved for `stela-update` (the System image: version, file, size, SHA-256); its shape is defined by STELA's `docs/system.md` and copied here when it exists. |
| `packages[].version` | 0.1.0 | `UPSTREAM-REVISION`; what `pkg list` shows and `pkg upgrade` compares as text. |
| `packages[].upstream`, `revision` | Agora 1 | The two parts, for tools. |
| `packages[].stela` | Agora 1 | Lowest STELA version the package needs; `pkg install` refuses on an older system. |
| `packages[].url` | 0.1.0 | Was absolute. Becomes **relative to the index's own location** (a bare file name), so one index serves from GitHub Releases, a mirror or a folder unchanged. Absolute URLs stay allowed. |
| the rest | 0.1.0 | As in STELA's `docs/pkg.md` §3. |

## Signature

`index.json.sig`: the hex ed25519 signature of the exact bytes of
`index.json`, by the **package key** (`docs/signing.md`). `pkg` checks
it against `Initrd:/certs/pkg.pub`.

## Package files

`NAME-VERSION-REVISION-x86_64.tar`: ustar, owner 0, mtime 0, top-level
`PKGINFO` then `bin/`, `lib/`, `include/`, `share/` or `Name.app/`.
`PKGINFO` gains `revision = ` and `stela = ` lines; `version = ` holds
`UPSTREAM-REVISION`.

## Compatibility rules

1. A package built for STELA `X.Y.*` is offered only to STELA `X.Y.*`
   (same major.minor); the index's `built-for` says which.
2. Within a release, a package's `stela` may be higher than `built-for`'s
   patch level when it needs a fix from a later patch release.
3. A new `format` only when a field changes meaning or is removed; adding
   fields never bumps it.
