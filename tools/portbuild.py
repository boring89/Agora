#!/usr/bin/env python3
# Copyright (C) 2026 YuanChi Hsieh
# SPDX-License-Identifier: 0BSD
"""Build, package and test Agora's ports for STELA.

    portbuild.py fetch   NAME...   download the source, check its SHA-256
    portbuild.py build   NAME...   unpack and run ports/NAME/build.sh
    portbuild.py package NAME...   dist/NAME-VERSION-REVISION-x86_64.tar (ustar)
    portbuild.py test    NAME...   boot STELA in QEMU with the package on a
                                   test Data volume and run ports/NAME/test.sh
    portbuild.py index             dist/index.json (every package in dist/),
                                   signed (index.json.sig) with
                                   PKG_SIGNING_KEY when it is set
    portbuild.py all     NAME...   fetch, build, package, test
    portbuild.py list              the ports and their versions
    portbuild.py lint              check every port.toml, patch, test and
                                   the README (what CI runs on every push)
    portbuild.py sources DIR       copy every port's upstream source into
                                   DIR with a SOURCES.txt (for a release)
    portbuild.py keygen NAME       a new signing key: NAME.key + keys/NAME.pub
    portbuild.py sign KEY INDEX    INDEX.sig
    portbuild.py verify PUB INDEX  the signature and every listed package

NAME may be "all". The environment: STELA_ROOT (the STELA checkout,
default ../STELA next to this repository); MUSL_GCC (default
$STELA_ROOT/build/musl/install/bin/musl-gcc, made by `make musl` there);
PORTS_URL (a prefix for the index's urls; unset, they are file names
relative to the index). STELA_VERSION (a file here) names the STELA tag
the packages are built for.

port.toml (TOML subset: key = "string" | number | [list of strings];
docs/port-toml.md): name, version (upstream's), revision (this port's,
from 1), description, license (SPDX), homepage, stela (lowest STELA
version), install ("bin" or "app"), depends (list: packages it needs
installed), build-depends (list: ports whose headers and libraries it
builds against), toolchain ("musl", the default, or "rust"), and
source = the official URL; sha256; file (the name to store it as,
default the URL's last part); or local = a folder inside the port.

build.sh runs with SRC (the unpacked source; for a single-file source
the folder holding it), OUT (what the package holds: bin/, lib/, share/
or Name.app/), MUSL_GCC, STELA_ROOT, JOBS, PORT (ports/NAME) and DEPS (P13:
the include/ and lib/ of every build-depends and depends port merged,
built first if they are not).

test.sh is not a shell script but what to do in STELA's shell:
    $ COMMAND      typed at the prompt (after the previous command ended)
    > TEXT         a line the output must contain
    = CODE         the last command's exit code
    ! KEYS         QEMU key names (e.g. ctrl-q), sent once the last
                   expected line (>) appeared
    # ...          a comment
The package is unpacked into Data:/Programs/NAME/ and ports/NAME/files/
(if any) into Data:/test/.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTS = os.path.join(HERE, "ports")
SOURCES = os.path.join(HERE, "sources")
WORK = os.path.join(HERE, "work")
DIST = os.path.join(HERE, "dist")
STELA_ROOT = os.environ.get("STELA_ROOT", os.path.join(os.path.dirname(HERE), "STELA"))
MUSL_GCC = os.environ.get(
    "MUSL_GCC", os.path.join(STELA_ROOT, "build", "musl", "install", "bin", "musl-gcc"))
# Data partition of STELA's build/images/ahci.img (tools/make_test_images.py).
DATA_OFFSET = 83968
URL_BASE = os.environ.get("PORTS_URL", "")
STELA_VERSION_FILE = os.path.join(HERE, "STELA_VERSION")


def fail(msg):
    print(f"portbuild: {msg}", file=sys.stderr)
    sys.exit(1)


def parse_toml(text):
    """The subset port.toml uses: flat `key = value` lines."""
    out = {}
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            fail(f"port.toml line {n}: no '='")
        key, value = (s.strip() for s in line.split("=", 1))
        if value.startswith('"') and value.endswith('"'):
            out[key] = value[1:-1]
        elif value.startswith("[") and value.endswith("]"):
            items = [v.strip() for v in value[1:-1].split(",") if v.strip()]
            out[key] = [v.strip('"') for v in items]
        else:
            try:
                out[key] = int(value)
            except ValueError:
                fail(f"port.toml line {n}: cannot read {value!r}")
    return out


def port(name):
    path = os.path.join(PORTS, name, "port.toml")
    if not os.path.exists(path):
        fail(f"no port {name}")
    with open(path, encoding="utf-8") as f:
        meta = parse_toml(f.read())
    for key in ("name", "version", "revision", "license", "description", "install", "stela"):
        if key not in meta:
            fail(f"{name}: port.toml lacks {key}")
    if not isinstance(meta["revision"], int) or meta["revision"] < 1:
        fail(f"{name}: revision must be a whole number from 1")
    if "copy-from" in meta:
        fail(f"{name}: copy-from is gone; name the official URL in source (docs/port-toml.md)")
    if ("source" in meta) == ("local" in meta):
        fail(f"{name}: give exactly one of source and local")
    if "local" in meta:
        meta.setdefault("sha256", "")
    elif "sha256" not in meta:
        fail(f"{name}: port.toml lacks sha256")
    meta.setdefault("depends", [])
    meta.setdefault("build-depends", [])
    return meta


def names(args):
    if args == ["all"] or not args:
        return sorted(d for d in os.listdir(PORTS) if os.path.isdir(os.path.join(PORTS, d)))
    return args


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def source_file(meta):
    if "file" in meta:
        return os.path.join(SOURCES, meta["file"])
    return os.path.join(SOURCES, os.path.basename(meta["source"]))


def fetch(name):
    meta = port(name)
    if "local" in meta:
        # The source is part of the port itself (ports/NAME/LOCAL).
        return os.path.join(PORTS, name, meta["local"])
    os.makedirs(SOURCES, exist_ok=True)
    dest = source_file(meta)
    if not os.path.exists(dest):
        print(f"{name}: downloading {meta['source']}")
        tmp = dest + ".part"
        urllib.request.urlretrieve(meta["source"], tmp)
        os.replace(tmp, dest)
    got = sha256(dest)
    if got != meta["sha256"]:
        fail(f"{name}: {os.path.basename(dest)} has SHA-256 {got}, expected {meta['sha256']}")
    print(f"{name}: source {os.path.basename(dest)} ok")
    return dest


def unpack(src, into):
    if os.path.isdir(src):
        shutil.copytree(src, into)
        return into
    os.makedirs(into, exist_ok=True)
    if src.endswith((".tar.gz", ".tgz", ".tar.bz2", ".tar.xz", ".tar", ".crate")):
        with tarfile.open(src) as t:
            t.extractall(into, filter="data")
        entries = os.listdir(into)
        if len(entries) == 1 and os.path.isdir(os.path.join(into, entries[0])):
            return os.path.join(into, entries[0])
        return into
    if src.endswith(".zip"):
        import zipfile
        with zipfile.ZipFile(src) as z:
            z.extractall(into)
        entries = os.listdir(into)
        if len(entries) == 1 and os.path.isdir(os.path.join(into, entries[0])):
            return os.path.join(into, entries[0])
        return into
    shutil.copy(src, into)
    return into


def built(name):
    out = os.path.join(WORK, name, "out")
    return os.path.isdir(out) and bool(os.listdir(out))


def deps_root(name, meta, seen=None):
    """work/NAME/deps: the include/ and lib/ of the ports NAME builds
    against (and theirs), each built first if it is not."""
    seen = set() if seen is None else seen
    root = os.path.join(WORK, name, "deps")
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(os.path.join(root, "include"))
    os.makedirs(os.path.join(root, "lib"))

    def add(dep):
        if dep in seen:
            return
        seen.add(dep)
        dmeta = port(dep)
        for sub in dmeta["build-depends"] + dmeta["depends"]:
            add(sub)
        if not built(dep):
            build(dep)
        out = os.path.join(WORK, dep, "out")
        for part in ("include", "lib"):
            src = os.path.join(out, part)
            if os.path.isdir(src):
                shutil.copytree(src, os.path.join(root, part), dirs_exist_ok=True)

    for dep in meta["build-depends"] + meta["depends"]:
        add(dep)
    return root


def build(name):
    meta = port(name)
    deps = deps_root(name, meta) if meta["build-depends"] or meta["depends"] else ""
    src = fetch(name)
    work = os.path.join(WORK, name)
    for sub in ("src", "out", "test"):
        shutil.rmtree(os.path.join(work, sub), ignore_errors=True)
    srcdir = unpack(src, os.path.join(work, "src"))
    out = os.path.join(work, "out")
    os.makedirs(out)
    patches = os.path.join(PORTS, name, "patches")
    if os.path.isdir(patches):
        for p in sorted(os.listdir(patches)):
            if p.endswith(".patch"):
                subprocess.run(["patch", "-p1", "-s", "-i", os.path.join(patches, p)],
                               cwd=srcdir, check=True)
    if not os.path.exists(MUSL_GCC) and meta.get("toolchain", "musl") == "musl":
        fail(f"no {MUSL_GCC} (run `make musl` in STELA)")
    env = dict(os.environ, SRC=srcdir, OUT=out, MUSL_GCC=MUSL_GCC, STELA_ROOT=STELA_ROOT, DEPS=deps,
               JOBS=os.environ.get("JOBS") or str(os.cpu_count() or 2), PORT=os.path.join(PORTS, name))
    log = os.path.join(work, "build.log")
    with open(log, "w") as f:
        r = subprocess.run(["sh", "-e", os.path.join(PORTS, name, "build.sh")],
                           cwd=srcdir, env=env, stdout=f, stderr=subprocess.STDOUT)
    if r.returncode != 0:
        with open(log) as f:
            tail = f.read()[-3000:]
        fail(f"{name}: build failed (work/{name}/build.log):\n{tail}")
    print(f"{name}: built")


def package_version(meta):
    """What pkg shows and compares: upstream's version, then the port's
    revision (5.4.7-1)."""
    return f"{meta['version']}-{meta['revision']}"


def package_path(meta):
    return os.path.join(DIST, f"{meta['name']}-{package_version(meta)}-x86_64.tar")


def built_for():
    """The STELA release the packages are for: STELA_VERSION without
    its leading v."""
    try:
        with open(STELA_VERSION_FILE, encoding="utf-8") as f:
            tag = f.read().strip()
    except OSError:
        fail("no STELA_VERSION file (the STELA tag the ports are built for)")
    return tag[1:] if tag.startswith("v") else tag


def package(name):
    meta = port(name)
    out = os.path.join(WORK, name, "out")
    if not os.path.isdir(out) or not os.listdir(out):
        fail(f"{name}: nothing built (portbuild.py build {name})")
    os.makedirs(DIST, exist_ok=True)
    info = os.path.join(WORK, name, "PKGINFO")
    with open(info, "w", encoding="utf-8") as f:
        f.write(f"name = {meta['name']}\n")
        f.write(f"version = {package_version(meta)}\n")
        f.write(f"upstream = {meta['version']}\n")
        f.write(f"revision = {meta['revision']}\n")
        for key in ("description", "license", "homepage", "install", "stela"):
            f.write(f"{key} = {meta.get(key, '')}\n")
        f.write(f"depends = {' '.join(meta['depends'])}\n")
    dest = package_path(meta)

    def clean(t):
        t.uid = t.gid = 0
        t.uname = t.gname = ""
        t.mtime = 0
        return t

    with tarfile.open(dest, "w", format=tarfile.USTAR_FORMAT) as t:
        t.add(info, "PKGINFO", filter=clean)
        for entry in sorted(os.listdir(out)):
            t.add(os.path.join(out, entry), entry, filter=clean)
    print(f"{name}: {os.path.relpath(dest, HERE)} ({os.path.getsize(dest)} bytes)")
    return dest


def ehfs(image, *args):
    tool = os.path.join(STELA_ROOT, "build", "host", "ehfs", "ehfs-cp")
    if not os.path.exists(tool):
        fail(f"no {tool} (run `make ehfs-tools` in STELA)")
    r = subprocess.run([tool, "--offset", str(DATA_OFFSET), image] + list(args),
                       capture_output=True, text=True)
    if r.returncode != 0 and args[0] != "mkdir":
        fail(f"ehfs-cp {' '.join(args)}: {r.stderr.strip()}")


def copy_tree(image, host, dest):
    ehfs(image, "mkdir", dest)
    for entry in sorted(os.listdir(host)):
        path = os.path.join(host, entry)
        if os.path.isdir(path):
            copy_tree(image, path, f"{dest}/{entry}")
        else:
            ehfs(image, "in", path, f"{dest}/{entry}")


def parse_test(name):
    path = os.path.join(PORTS, name, "test.sh")
    steps = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            kind, _, text = line.partition(" ")
            if kind not in ("$", ">", "=", "!"):
                fail(f"{name}: test.sh: cannot read {line!r}")
            steps.append((kind, text))
    return steps


def test(name):
    meta = port(name)
    pkg = package_path(meta)
    if not os.path.exists(pkg):
        fail(f"{name}: no package (portbuild.py package {name})")
    work = os.path.join(WORK, name, "test")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    base_img = os.path.join(STELA_ROOT, "build", "images", "ahci.img")
    esp = os.path.join(STELA_ROOT, "build", "esp")
    if not os.path.exists(base_img) or not os.path.isdir(esp):
        fail("no STELA build (make esp test-images ehfs-tools in STELA)")
    image = os.path.join(work, "data.img")
    shutil.copyfile(base_img, image)
    root = os.path.join(work, "root")
    with tarfile.open(pkg) as t:
        t.extractall(root, filter="data")
    ehfs(image, "mkdir", "/Programs")
    for dep in meta["depends"]:
        dmeta = port(dep)
        droot = os.path.join(work, "dep-" + dep)
        with tarfile.open(package_path(dmeta)) as t:
            t.extractall(droot, filter="data")
        copy_tree(image, droot, f"/Programs/{dep}")
    copy_tree(image, root, f"/Programs/{name}")
    files = os.path.join(PORTS, name, "files")
    if os.path.isdir(files):
        copy_tree(image, files, "/test")
    vars_fd = os.path.join(work, "OVMF_VARS.fd")
    shutil.copyfile("/usr/share/OVMF/OVMF_VARS_4M.fd", vars_fd)
    args = [sys.executable, os.path.join(STELA_ROOT, "tools", "qemu_test.py"),
            "--timeout", "240", "--log", os.path.join(work, "serial.log")]
    trigger = "STELA shell"
    program = None
    last_expect = None
    for kind, text in parse_test(name):
        if kind == "$":
            args += ["--type", trigger, text + "\\n"]
            words = text.split()
            if words and words[0] == "run" and len(words) > 1:
                program = words[1].rstrip("/").split("/")[-1].split(":")[-1]
                trigger = f"{program} exited with code"
            else:
                trigger = "> " + text
        elif kind == ">":
            args += ["--expect", text]
            last_expect = text
        elif kind == "!":
            if not last_expect:
                fail(f"{name}: '!' before any '>'")
            args += ["--send-keys", last_expect, text]
        elif kind == "=":
            if not program:
                fail(f"{name}: '=' before any run")
            args += ["--expect", f"{program} exited with code {text}"]
    args += ["--", "qemu-system-x86_64", "-machine", "q35", "-m", "512M", "-no-reboot",
             "-rtc", "base=utc",
             "-drive", "if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd",
             "-drive", f"if=pflash,format=raw,file={vars_fd}",
             "-drive", f"format=raw,file=fat:rw:{esp}", "-display", "none", "-serial", "stdio",
             "-drive", f"if=none,id=sata1,format=raw,file={image}",
             "-device", "ide-hd,drive=sata1,bus=ide.1"]
    # STELA P14: the System volume (fonts, the IME's dictionary, the
    # tools), read only and never written (snapshot).
    system = os.path.join(STELA_ROOT, "build", "system.img")
    if os.path.exists(system):
        args += ["-drive", f"if=none,id=sysdisk,format=raw,file={system},snapshot=on",
                 "-device", "ide-hd,drive=sysdisk,bus=ide.2"]
    # qemu_test.py keeps its QMP socket in ./build.
    os.makedirs(os.path.join(work, "build"), exist_ok=True)
    r = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=work)
    last = r.stdout.strip().splitlines()[-1:] if r.stdout.strip() else ["(no output)"]
    if r.returncode != 0:
        fail(f"{name}: test failed: {last[0]} (log: work/{name}/test/serial.log)")
    print(f"{name}: test passed")


def index():
    """dist/index.json (docs/index.md): format 1 with the fields STELA's
    pkg knows plus built-for, serial, generated and, per package, stela,
    revision and upstream (pkg ignores what it does not know)."""
    import time
    os.makedirs(DIST, exist_ok=True)
    release = built_for()
    stela_version = os.path.join(STELA_ROOT, "VERSION")
    if os.path.exists(stela_version):
        with open(stela_version, encoding="utf-8") as f:
            have = f.read().strip()
        if have != release:
            print(f"index: warning: STELA_VERSION says {release}, {STELA_ROOT} is {have}")
    entries = []
    for name in names(["all"]):
        meta = port(name)
        pkg = package_path(meta)
        if not os.path.exists(pkg):
            continue
        entries.append({
            "name": meta["name"],
            "version": package_version(meta),
            "upstream": meta["version"],
            "revision": meta["revision"],
            "description": meta["description"],
            "license": meta["license"],
            "homepage": meta.get("homepage", ""),
            "install": meta["install"],
            "depends": meta["depends"],
            "stela": meta["stela"],
            "size": os.path.getsize(pkg),
            "sha256": sha256(pkg),
            "file": os.path.basename(pkg),
            "url": URL_BASE + os.path.basename(pkg),
        })
    now = int(time.time())
    doc = {
        "format": 1,
        "built-for": release,
        # Every published index has a larger serial than the one before
        # it; the time it was made does that without any state to keep.
        "serial": now,
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "packages": entries,
    }
    dest = os.path.join(DIST, "index.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"index: {len(entries)} packages for STELA {release} in {os.path.relpath(dest, HERE)}")
    # Signed with ed25519 when PKG_SIGNING_KEY names the key file:
    # dist/index.json.sig, what `pkg update` checks (docs/signing.md).
    key = os.environ.get("PKG_SIGNING_KEY")
    if key:
        sign(key, dest)
        print(f"index: signed with {key}")


# --- signing (docs/signing.md) -------------------------------------------
#
# Keys are ed25519 (RFC 8032). A private key file holds the 32-byte seed
# in hex; a public key file the 32-byte public key in hex: the formats
# STELA's Initrd:/certs/pkg.pub and `pkg` use. index.json.sig is the hex
# signature of the exact bytes of index.json.


def _crypto():
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519
    except ImportError:
        fail("signing needs Python's cryptography module (python3-cryptography)")
    return ed25519, serialization


def keygen(name):
    """A new random key: NAME.key (the seed, mode 600, never committed)
    and keys/NAME.pub."""
    ed25519, serialization = _crypto()
    key = ed25519.Ed25519PrivateKey.generate()
    seed = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                             serialization.NoEncryption())
    pub = key.public_key().public_bytes(serialization.Encoding.Raw,
                                        serialization.PublicFormat.Raw)
    keyfile = f"{name}.key"
    if os.path.exists(keyfile):
        fail(f"{keyfile} exists; not overwriting a key")
    fd = os.open(keyfile, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(seed.hex() + "\n")
    os.makedirs(os.path.join(HERE, "keys"), exist_ok=True)
    pubfile = os.path.join(HERE, "keys", f"{name}.pub")
    with open(pubfile, "w") as f:
        f.write(pub.hex() + "\n")
    print(f"keygen: {keyfile} (keep it off the repository) and {os.path.relpath(pubfile, HERE)}")


def sign(keyfile, index_path):
    ed25519, _ = _crypto()
    with open(keyfile) as f:
        key = ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex(f.read().strip()))
    with open(index_path, "rb") as f:
        sig = key.sign(f.read())
    with open(index_path + ".sig", "w") as f:
        f.write(sig.hex() + "\n")


def verify(pubfile, index_path):
    """What pkg does: the signature is PUBFILE's, and every package the
    index lists is next to it with the recorded SHA-256 and size."""
    ed25519, _ = _crypto()
    from cryptography.exceptions import InvalidSignature
    try:
        with open(pubfile) as f:
            key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(f.read().strip()))
        with open(index_path + ".sig") as f:
            sig = bytes.fromhex(f.read().strip())
        with open(index_path, "rb") as f:
            data = f.read()
        key.verify(sig, data)
    except (OSError, ValueError, InvalidSignature) as e:
        fail(f"verify: the signature is not {pubfile}'s ({e.__class__.__name__})")
    doc = json.loads(data)
    if doc.get("format") != 1:
        fail("verify: not a format 1 index")
    folder = os.path.dirname(os.path.abspath(index_path))
    for p in doc["packages"]:
        path = os.path.join(folder, p["file"])
        if not os.path.exists(path):
            fail(f"verify: {p['file']} is listed but not here")
        if os.path.getsize(path) != p["size"] or sha256(path) != p["sha256"]:
            fail(f"verify: {p['file']} does not match the index")
    print(f"verify: index for STELA {doc.get('built-for', '?')}, serial {doc.get('serial', '?')}, "
          f"{len(doc['packages'])} packages, signature ok")


def sources(folder):
    """A release carries every upstream source it was built from (the
    GPL ports' source obligation, applied to all): copies of the fetched
    files and SOURCES.txt (name, version, license, SHA-256, URL, file)."""
    os.makedirs(folder, exist_ok=True)
    lines = []
    for name in names(["all"]):
        meta = port(name)
        if "local" in meta:
            lines.append(f"{meta['name']} {meta['version']} {meta['license']} - - "
                         f"(in ports/{name}/{meta['local']})")
            continue
        src = fetch(name)
        shutil.copyfile(src, os.path.join(folder, os.path.basename(src)))
        lines.append(f"{meta['name']} {meta['version']} {meta['license']} {meta['sha256']} "
                     f"{meta['source']} {os.path.basename(src)}")
    with open(os.path.join(folder, "SOURCES.txt"), "w", encoding="utf-8") as f:
        f.write("# name version license sha256 url file\n")
        f.write("\n".join(lines) + "\n")
    print(f"sources: {len(lines)} ports in {folder}")


# --- lint (what CI runs on every push) -------------------------------------

NAME_OK = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
VERSION_OK = re.compile(r"^\d+\.\d+\.\d+$")


def lint():
    problems = []

    def bad(msg):
        problems.append(msg)

    with open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
        readme = f.read()
    for name in names(["all"]):
        folder = os.path.join(PORTS, name)
        meta = port(name)  # the required keys, revision, source/local
        if meta["name"] != name or not NAME_OK.match(name) or name in (".", ".."):
            bad(f"{name}: name must equal the folder name and be [A-Za-z0-9._-]")
        if not VERSION_OK.match(str(meta["stela"])):
            bad(f"{name}: stela must be major.minor.patch, not {meta['stela']!r}")
        if meta["install"] not in ("bin", "app"):
            bad(f"{name}: install must be bin or app")
        for key in ("license", "description", "homepage"):
            if not str(meta.get(key, "")).strip():
                bad(f"{name}: {key} is empty")
        if meta.get("toolchain", "musl") not in ("musl", "rust"):
            bad(f"{name}: toolchain must be musl or rust")
        if "source" in meta:
            src = meta["source"]
            with open(os.path.join(folder, "port.toml"), encoding="utf-8") as f:
                toml_text = f.read()
            if src.startswith("http://") and "no HTTPS" not in toml_text:
                bad(f"{name}: source is http://; say '# ... no HTTPS' in port.toml if the site has none")
            elif not src.startswith(("https://", "http://")):
                bad(f"{name}: source must be an https:// URL")
            if not re.fullmatch(r"[0-9a-f]{64}", str(meta["sha256"])):
                bad(f"{name}: sha256 must be 64 hex digits")
        for dep in meta["depends"] + meta["build-depends"]:
            if not os.path.isdir(os.path.join(PORTS, dep)):
                bad(f"{name}: depends on {dep}, which is not a port")
        if not os.path.exists(os.path.join(folder, "build.sh")):
            bad(f"{name}: no build.sh")
        if not os.path.exists(os.path.join(folder, "test.sh")):
            bad(f"{name}: no test.sh")
        else:
            kinds = [k for k, _ in parse_test(name)]
            if "$" not in kinds or ">" not in kinds:
                bad(f"{name}: test.sh needs at least one $ command and one > line")
        patches = os.path.join(folder, "patches")
        if os.path.isdir(patches):
            for pname in sorted(os.listdir(patches)):
                if not pname.endswith(".patch"):
                    continue
                with open(os.path.join(patches, pname), encoding="utf-8", errors="replace") as f:
                    first = f.readline().strip()
                if not first.startswith("SPDX-License-Identifier: "):
                    bad(f"{name}: patches/{pname} must start with SPDX-License-Identifier:")
        if f"| {name} |" not in readme:
            bad(f"{name}: not in README.md's table")
    tools = os.path.join(HERE, "tools")
    for tname in sorted(os.listdir(tools)):
        if tname.endswith(".py"):
            with open(os.path.join(tools, tname), encoding="utf-8") as f:
                head = f.read(400)
            if "SPDX-License-Identifier: 0BSD" not in head:
                bad(f"tools/{tname}: no 0BSD SPDX header")
    built_for()  # STELA_VERSION exists
    for msg in problems:
        print(f"lint: {msg}")
    if problems:
        fail(f"{len(problems)} problem(s)")
    print(f"lint: {len(names(['all']))} ports ok")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "index":
        index()
        return
    if cmd == "lint":
        lint()
        return
    if cmd == "sources" and len(rest) == 1:
        sources(rest[0])
        return
    if cmd == "keygen" and len(rest) == 1:
        keygen(rest[0])
        return
    if cmd == "sign" and len(rest) == 2:
        sign(rest[0], rest[1])
        print(f"sign: {rest[1]}.sig")
        return
    if cmd == "verify" and len(rest) == 2:
        verify(rest[0], rest[1])
        return
    if cmd == "list":
        for n in names(["all"]):
            m = port(n)
            print(f"{m['name']:12} {m['version']:12} {m['license']:20} {m['description']}")
        return
    steps = {
        "fetch": [fetch], "build": [build], "package": [package], "test": [test],
        "all": [build, package, test],
    }.get(cmd)
    if steps is None:
        fail(f"unknown command {cmd}")
    for n in names(rest):
        for step in steps:
            step(n)


if __name__ == "__main__":
    main()
