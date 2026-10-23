# A library port (P13 K7): lib/libz.a and include/ for the ports that
# build against it, minigzip and a test program in bin/.
CC="$MUSL_GCC" CFLAGS="-O2 -fno-pie" ./configure --static --prefix=/
make -j"$JOBS" libz.a
make install DESTDIR="$OUT" prefix=/ >/dev/null
rm -rf "$OUT/share" "$OUT/lib/pkgconfig"
mkdir -p "$OUT/bin"
"$MUSL_GCC" -O2 -static -no-pie -fno-pie -Wl,-z,max-page-size=4096 -I. \
    test/minigzip.c libz.a -o "$OUT/bin/minigzip"
"$MUSL_GCC" -O2 -static -no-pie -fno-pie -Wl,-z,max-page-size=4096 -I"$OUT/include" \
    "$PORT/test.c" -L"$OUT/lib" -lz -o "$OUT/bin/zlib-test"
strip "$OUT/bin/minigzip" "$OUT/bin/zlib-test"
