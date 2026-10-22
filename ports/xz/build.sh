# libtool drops -static (it only means "no shared libtool libraries");
# -all-static at make time links the program statically (musl has a
# libc.so since P13).
# A library port (P13 K7): lib/liblzma.a, include/lzma*, bin/xz. One
# thread (no pthread in the xz program's encoder needed).
./configure --host=x86_64-linux-musl CC="$MUSL_GCC" CFLAGS="-O2 -fno-pie" \
    LDFLAGS="-static -no-pie -Wl,-z,max-page-size=4096" --prefix=/ \
    --disable-shared --enable-static --disable-nls --disable-doc \
    --disable-scripts --disable-lzmainfo --disable-lzma-links \
    --disable-xzdec --disable-lzmadec --enable-threads=no >/dev/null
make -j"$JOBS" LDFLAGS="-all-static -no-pie -Wl,-z,max-page-size=4096" >/dev/null
make install DESTDIR="$OUT" >/dev/null
rm -rf "$OUT/share" "$OUT/lib/pkgconfig" "$OUT/lib/liblzma.la"
for f in "$OUT"/bin/*; do [ -L "$f" ] && rm "$f"; done
strip "$OUT/bin/xz"
