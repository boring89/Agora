# tcc for x86-64 with musl, everything under Data:/Programs/tcc (the
# Linux path /Data/Programs/tcc): bin/tcc, include/ (musl's headers),
# lib/ (crt1.o, crti.o, crtn.o, libc.a), lib/tcc/ (tcc's own headers and
# libtcc1.a). STELA runs static programs only: use `tcc -static`.
#
# tcc 0.9.27 cannot link the libc.a STELA builds (gcc's default PIE
# code: GOTPCRELX relocations, function sections), so a second musl is
# built here for it: no PIC, no relaxed relocations, no CET.
P=/Data/Programs/tcc
./configure --cc="$MUSL_GCC" --prefix=$P --config-musl \
    --sysincludepaths=$P/lib/tcc/include:$P/include \
    --libpaths=$P/lib/tcc:$P/lib --crtprefix=$P/lib \
    --extra-cflags="-O2 -fno-pie -w" \
    --extra-ldflags="-static -no-pie -Wl,-z,max-page-size=4096" >/dev/null
make tcc libtcc1.a
musl_src=$(ls "$STELA_ROOT"/build/downloads/musl-*.tar.gz | head -1)
mkdir -p ../musl-tcc && tar -C ../musl-tcc -xzf "$musl_src"
(
    cd ../musl-tcc/musl-*
    ./configure --prefix="$(pwd)/../install" --target=x86_64 --disable-shared \
        CC=gcc AR=ar RANLIB=ranlib \
        CFLAGS="-O2 -fno-pie -fno-pic -fno-stack-protector -fcf-protection=none -Wa,-mrelax-relocations=no -fno-asynchronous-unwind-tables" >/dev/null
    make -j"$JOBS" >/dev/null
    make install >/dev/null
)
musl=$(cd ../musl-tcc/install && pwd)
mkdir -p "$OUT/bin" "$OUT/lib/tcc/include" "$OUT/include"
cp tcc "$OUT/bin/tcc"
strip "$OUT/bin/tcc"
cp libtcc1.a "$OUT/lib/tcc/"
cp include/*.h "$OUT/lib/tcc/include/"
cp -r "$musl/include/." "$OUT/include/"
cp "$musl/lib/crt1.o" "$musl/lib/crti.o" "$musl/lib/crtn.o" "$musl/lib/libc.a" "$OUT/lib/"
