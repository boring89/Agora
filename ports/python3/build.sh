# Python 3.12 (P13 K8). Cross-building needs a Python of the same version
# on the build machine: one is built first (host/). Every extension module
# is built into the program (MODULE_BUILDTYPE=static), but the program
# itself is linked dynamically against musl's libc.so (STELA's
# /lib/ld-musl-x86_64.so.1): ctypes needs dlopen(NULL), which a static
# program does not have. zlib, bz2, lzma, ctypes
# (libffi) and sqlite3 come from the library ports ($DEPS); ssl, hashlib's
# OpenSSL part, curses, readline, dbm, tkinter, uuid are left out.
mkdir -p host && (cd host && ../configure --without-ensurepip >/dev/null && \
    make -j"$JOBS" >/dev/null 2>&1)
export MODULE_BUILDTYPE=static
export ZLIB_CFLAGS="-I$DEPS/include" ZLIB_LIBS="-L$DEPS/lib -lz"
export BZIP2_CFLAGS="-I$DEPS/include" BZIP2_LIBS="-L$DEPS/lib -lbz2"
export LIBLZMA_CFLAGS="-I$DEPS/include" LIBLZMA_LIBS="-L$DEPS/lib -llzma"
export LIBFFI_CFLAGS="-I$DEPS/include" LIBFFI_LIBS="-L$DEPS/lib -lffi"
export LIBSQLITE3_CFLAGS="-I$DEPS/include" LIBSQLITE3_LIBS="-L$DEPS/lib -lsqlite3"
export ac_cv_file__dev_ptmx=yes ac_cv_file__dev_ptc=no ac_cv_buggy_getaddrinfo=no
for m in _tkinter _curses _curses_panel readline _ssl _hashlib _dbm _gdbm _uuid nis \
    _ctypes_test _testcapi _testinternalcapi _testbuffer _testimportmultiple \
    _testmultiphase _testsinglephase _xxtestfuzz xxlimited xxlimited_35 xxsubtype _testclinic; do
    export "py_cv_module_$m=n/a"
done
./configure --host=x86_64-linux-musl --build=x86_64-linux-gnu CC="$MUSL_GCC" \
    CFLAGS="-O2 -fno-pie" LDFLAGS="-no-pie -Wl,-z,max-page-size=4096" \
    --with-build-python="$PWD/host/python" --prefix=/Data/Programs/python3 \
    --disable-shared --disable-ipv6 --without-ensurepip --disable-test-modules \
    --without-static-libpython >/dev/null
make -j"$JOBS" >/dev/null
make install DESTDIR="$PWD/inst" COMPILEALL_OPTS="-j0" >/dev/null 2>&1 || \
    make install DESTDIR="$PWD/inst" >/dev/null
root="$PWD/inst/Data/Programs/python3"
lib="$root/lib/python3.12"
rm -rf "$lib/test" "$lib/idlelib" "$lib/tkinter" "$lib/turtledemo" "$lib/ensurepip" \
    "$lib/lib2to3" "$lib/unittest/test" "$lib"/config-3.12-* "$lib/lib-dynload"
find "$lib" -name __pycache__ -type d -prune -exec rm -rf {} +
mkdir -p "$OUT/bin" "$OUT/lib"
cp "$root/bin/python3.12" "$OUT/bin/python3"
strip "$OUT/bin/python3"
cp -r "$lib" "$OUT/lib/"
# Where getpath looks for the platform libraries (none: all built in).
mkdir -p "$OUT/lib/python3.12/lib-dynload"
touch "$OUT/lib/python3.12/lib-dynload/.keep"
