# A library port (P13 K7): lib/libbz2.a, include/bzlib.h, bin/bzip2.
make -j"$JOBS" CC="$MUSL_GCC" CFLAGS="-O2 -fno-pie -D_FILE_OFFSET_BITS=64" \
    LDFLAGS="-static -no-pie -Wl,-z,max-page-size=4096" libbz2.a bzip2
mkdir -p "$OUT/bin" "$OUT/lib" "$OUT/include"
cp libbz2.a "$OUT/lib/"
cp bzlib.h "$OUT/include/"
cp bzip2 "$OUT/bin/"
strip "$OUT/bin/bzip2"
