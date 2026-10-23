# Public keys

The public halves of the keys that sign Agora's indexes (`docs/signing.md`),
32 bytes in hex, one per file. `pkg` on STELA checks `index.json.sig`
against the copy STELA ships (`Initrd:/certs/pkg.pub`); the files here let
anyone check a release on their own machine:

```
python3 tools/portbuild.py verify keys/agora-packages.pub dist/index.json
```

| File | Signs | From | Until |
|---|---|---|---|
| (none yet) | | | |

No real key exists yet: STELA still ships its test key (`tools/pkg.pub`
there, a fixed seed anyone can reproduce). The first real key is made
with `python3 tools/portbuild.py keygen agora-packages` on the releaser's
machine; the `.key` file never enters the repository (`.gitignore`).
