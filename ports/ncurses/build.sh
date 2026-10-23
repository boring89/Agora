# A library port (P13 K7): lib/libncurses.a (wide characters, the
# terminfo part included), include/ (curses.h at the top), and a test
# program. No terminfo database on STELA: the descriptions of a few
# terminals are compiled in (--with-fallbacks, made with the build
# machine's tic). Cross-built, its configure cannot test what bool is and
# takes int; it is told what a native build finds (<stdbool.h>, one byte),
# so programs that mix bool and ncurses agree with the library.
cf_cv_header_stdbool_h=1 cf_cv_type_of_bool="unsigned char" ./configure --host=x86_64-linux-musl --build=x86_64-linux-gnu CC="$MUSL_GCC" BUILD_CC=gcc \
    CFLAGS="-O2 -fno-pie" --prefix=/ --without-shared --without-cxx --without-cxx-binding \
    --without-ada --without-tests --without-manpages --without-progs --without-debug \
    --enable-widec --disable-lib-suffixes --enable-overwrite --disable-database \
    --with-fallbacks=dumb,vt100,vt220,linux,xterm,xterm-256color,ansi,screen \
    --disable-home-terminfo --without-pkg-config >/dev/null
make -j"$JOBS" >/dev/null
make install DESTDIR="$OUT" >/dev/null
rm -rf "$OUT/share" "$OUT/lib/pkgconfig" "$OUT/bin"
mkdir -p "$OUT/bin"
"$MUSL_GCC" -O2 -static -no-pie -fno-pie -Wl,-z,max-page-size=4096 -I"$OUT/include" \
    "$PORT/test.c" -L"$OUT/lib" -lncurses -o "$OUT/bin/ncurses-test"
strip "$OUT/bin/ncurses-test"
