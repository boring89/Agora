# less with ncurses ($DEPS), static.
./configure --host=x86_64-linux-musl CC="$MUSL_GCC" CFLAGS="-O2 -fno-pie" \
    CPPFLAGS="-I$DEPS/include" LDFLAGS="-static -no-pie -Wl,-z,max-page-size=4096 -L$DEPS/lib" \
    --with-editor=vi --prefix=/ >/dev/null
make -j"$JOBS" >/dev/null
mkdir -p "$OUT/bin"
cp less lesskey "$OUT/bin/"
strip "$OUT/bin/less" "$OUT/bin/lesskey"
