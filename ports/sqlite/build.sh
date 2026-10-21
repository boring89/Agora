# The amalgamation and its shell, one thread, no extension loading.
mkdir -p "$OUT/bin"
"$MUSL_GCC" -O2 -static -no-pie -fno-pie -Wl,-z,max-page-size=4096 \
    -DSQLITE_THREADSAFE=0 -DSQLITE_OMIT_LOAD_EXTENSION -DSQLITE_DQS=0 \
    shell.c sqlite3.c -o "$OUT/bin/sqlite3" -lm
strip "$OUT/bin/sqlite3"
