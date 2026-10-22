# The python3 port test (P13 K8): the built-in modules and a few of the
# standard library.
import bz2, ctypes, hashlib, json, lzma, sqlite3, sys, zlib

data = b"STELA " * 1000
assert zlib.decompress(zlib.compress(data)) == data
assert bz2.decompress(bz2.compress(data)) == data
assert lzma.decompress(lzma.compress(data)) == data
print("python: compression ok")
db = sqlite3.connect(":memory:")
db.execute("create table t (x)")
db.executemany("insert into t values (?)", [(i,) for i in range(10)])
print("python: sqlite", sqlite3.sqlite_version, "sum", db.execute("select sum(x) from t").fetchone()[0])
libc = ctypes.CDLL(None)
print("python: ctypes strlen", libc.strlen(b"stela"))
print("python: sha256", hashlib.sha256(b"abc").hexdigest()[:8])
print("python: json", json.dumps({"os": "STELA", "version": sys.version_info[:2]}))
print("python: OK")
