#!/usr/bin/env python3
# Copyright (C) 2026 YuanChi Hsieh
# SPDX-License-Identifier: 0BSD
"""Build, package and test STELA ports.

    portbuild.py fetch   NAME...   download (or copy) the source, check SHA-256
    portbuild.py build   NAME...   unpack and run ports/NAME/build.sh
    portbuild.py package NAME...   dist/NAME-VERSION-x86_64.tar (ustar)
    portbuild.py test    NAME...   boot STELA in QEMU with the package on a
                                   test Data volume and run ports/NAME/test.sh
    portbuild.py index             dist/index.json (every package in dist/),
                                   signed (index.json.sig) with
                                   PKG_SIGNING_KEY when it is set
    portbuild.py all     NAME...   fetch, build, package, test
    portbuild.py list              the ports and their versions

NAME may be "all". The environment: STELA_ROOT (the STELA checkout,
default ../STELA next to this repository); MUSL_GCC (default
$STELA_ROOT/build/musl/install/bin/musl-gcc, made by `make musl` there).

port.toml (TOML subset: key = "string" | number | [list of strings]):
    name, version, description, license, homepage, stela (lowest STELA
    version), install ("bin" or "app"), depends (list: packages it needs
    installed), build-depends (list: ports whose headers and libraries it
    builds against; P13), and
    source = URL, or copy-from = a path (~ allowed); sha256; file (the
    name to store it as, default the URL's last part).

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
URL_BASE = os.environ.get("PORTS_URL", "https://10.0.2.2:8643/pkg/")


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
    for key in ("name", "version", "license", "description", "install"):
        if key not in meta:
            fail(f"{name}: port.toml lacks {key}")
    if "local" not in meta and "sha256" not in meta:
        fail(f"{name}: port.toml lacks sha256")
    if "local" in meta:
        meta.setdefault("sha256", "")
    elif ("source" in meta) == ("copy-from" in meta):
        fail(f"{name}: give exactly one of source, copy-from and local")
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
    origin = meta.get("source") or meta["copy-from"]
    return os.path.join(SOURCES, os.path.basename(origin))


def fetch(name):
    meta = port(name)
    if "local" in meta:
        # The source is part of the port itself (ports/NAME/LOCAL).
        return os.path.join(PORTS, name, meta["local"])
    os.makedirs(SOURCES, exist_ok=True)
    dest = source_file(meta)
    if not os.path.exists(dest):
        if "copy-from" in meta:
            shutil.copyfile(os.path.expanduser(meta["copy-from"]), dest)
        else:
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
    if src.endswith((".tar.gz", ".tgz", ".tar.bz2", ".tar.xz", ".tar")):
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


def package_path(meta):
    return os.path.join(DIST, f"{meta['name']}-{meta['version']}-x86_64.tar")


def package(name):
    meta = port(name)
    out = os.path.join(WORK, name, "out")
    if not os.path.isdir(out) or not os.listdir(out):
        fail(f"{name}: nothing built (portbuild.py build {name})")
    os.makedirs(DIST, exist_ok=True)
    info = os.path.join(WORK, name, "PKGINFO")
    with open(info, "w", encoding="utf-8") as f:
        for key in ("name", "version", "description", "license", "install"):
            f.write(f"{key} = {meta[key]}\n")
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
    # qemu_test.py keeps its QMP socket in ./build.
    os.makedirs(os.path.join(work, "build"), exist_ok=True)
    r = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=work)
    last = r.stdout.strip().splitlines()[-1:] if r.stdout.strip() else ["(no output)"]
    if r.returncode != 0:
        fail(f"{name}: test failed: {last[0]} (log: work/{name}/test/serial.log)")
    print(f"{name}: test passed")


def index():
    os.makedirs(DIST, exist_ok=True)
    entries = []
    for name in names(["all"]):
        meta = port(name)
        pkg = package_path(meta)
        if not os.path.exists(pkg):
            continue
        entries.append({
            "name": meta["name"],
            "version": meta["version"],
            "description": meta["description"],
            "license": meta["license"],
            "install": meta["install"],
            "depends": meta["depends"],
            "size": os.path.getsize(pkg),
            "sha256": sha256(pkg),
            "file": os.path.basename(pkg),
            "url": URL_BASE + os.path.basename(pkg),
        })
    dest = os.path.join(DIST, "index.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump({"format": 1, "packages": entries}, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"index: {len(entries)} packages in {os.path.relpath(dest, HERE)}")
    # Signed with ed25519 (STELA's tools/pkgsign.py) when PKG_SIGNING_KEY
    # names the key file: dist/index.json.sig, what `pkg update` checks.
    key = os.environ.get("PKG_SIGNING_KEY")
    if key:
        subprocess.run([sys.executable, os.path.join(STELA_ROOT, "tools", "pkgsign.py"),
                        "sign", key, dest], check=True)
        print(f"index: signed with {key}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "index":
        index()
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
