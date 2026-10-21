# Lua's own makefile, the "posix" target (no dlopen), static.
cd "$SRC/src"
make -j"$JOBS" CC="$MUSL_GCC" MYCFLAGS="-fno-pie" \
    MYLDFLAGS="-static -no-pie -Wl,-z,max-page-size=4096" posix
mkdir -p "$OUT/bin"
cp lua luac "$OUT/bin/"
strip "$OUT/bin/lua" "$OUT/bin/luac"
