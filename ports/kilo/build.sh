mkdir -p "$OUT/bin"
"$MUSL_GCC" -O2 -static -no-pie -fno-pie -Wl,-z,max-page-size=4096 -std=c99 \
    -D_DEFAULT_SOURCE kilo.c -o "$OUT/bin/kilo"
strip "$OUT/bin/kilo"
