# A library port (P13 K7): lib/libffi.a and include/ (python3's ctypes),
# a test program in bin/. No executable trampolines (STELA refuses
# anonymous executable memory): closures use the static trampoline table.
./configure --host=x86_64-linux-musl CC="$MUSL_GCC" CFLAGS="-O2 -fno-pie" --prefix=/ \
    --disable-shared --enable-static --disable-docs --disable-multi-os-directory \
    --disable-exec-static-tramp >/dev/null
make -j"$JOBS" >/dev/null
make install DESTDIR="$OUT" >/dev/null
rm -rf "$OUT/share" "$OUT/lib/pkgconfig" "$OUT/lib/libffi.la"
mkdir -p "$OUT/bin"
"$MUSL_GCC" -O2 -static -no-pie -fno-pie -Wl,-z,max-page-size=4096 -I"$OUT/include" \
    "$PORT/test.c" -L"$OUT/lib" -lffi -o "$OUT/bin/libffi-test"
strip "$OUT/bin/libffi-test"
