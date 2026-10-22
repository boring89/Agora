# The amalgamation and its shell, one thread, no extension loading.
mkdir -p "$OUT/bin"
"$MUSL_GCC" -O2 -static -no-pie -fno-pie -Wl,-z,max-page-size=4096 \
    -DSQLITE_THREADSAFE=0 -DSQLITE_OMIT_LOAD_EXTENSION -DSQLITE_DQS=0 \
    shell.c sqlite3.c -o "$OUT/bin/sqlite3" -lm
strip "$OUT/bin/sqlite3"
# P13 K7: also the library and its header, for ports that build against it
# (python3's sqlite3 module).
mkdir -p "$OUT/lib" "$OUT/include"
"$MUSL_GCC" -O2 -fno-pie -DSQLITE_THREADSAFE=0 -DSQLITE_OMIT_LOAD_EXTENSION -DSQLITE_DQS=0 \
    -c sqlite3.c -o sqlite3.o
ar crs "$OUT/lib/libsqlite3.a" sqlite3.o
cp sqlite3.h "$OUT/include/"
