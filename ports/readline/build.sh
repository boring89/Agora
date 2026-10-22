# A library port (P13 K7): lib/libreadline.a, lib/libhistory.a,
# include/readline/; built against ncurses ($DEPS). A test program reads a
# line with readline().
./configure --host=x86_64-linux-musl CC="$MUSL_GCC" CFLAGS="-O2 -fno-pie" \
    CPPFLAGS="-I$DEPS/include" LDFLAGS="-L$DEPS/lib" --prefix=/ \
    --disable-shared --enable-static --with-curses --disable-install-examples >/dev/null
make -j"$JOBS" >/dev/null
make install DESTDIR="$OUT" >/dev/null
rm -rf "$OUT/share" "$OUT/lib/pkgconfig" "$OUT/bin"
mkdir -p "$OUT/bin"
"$MUSL_GCC" -O2 -static -no-pie -fno-pie -Wl,-z,max-page-size=4096 -I"$OUT/include" \
    "$PORT/test.c" -L"$OUT/lib" -L"$DEPS/lib" -lreadline -lhistory -lncurses \
    -o "$OUT/bin/readline-test"
strip "$OUT/bin/readline-test"
