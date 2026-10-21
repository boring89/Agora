# No /bin/sh on STELA: recipes run with dash from its package.
sed -i 's|const char \*default_shell = "/bin/sh";|const char *default_shell = "/Data/Programs/dash/bin/dash";|' src/job.c
CC="$MUSL_GCC" CFLAGS="-O2 -fno-pie -w -std=gnu17" LDFLAGS="-static -no-pie -Wl,-z,max-page-size=4096" \
    ./configure --host=x86_64-linux-musl --disable-nls --without-guile \
    --disable-load >/dev/null
make -j"$JOBS"
mkdir -p "$OUT/bin"
cp make "$OUT/bin/make"
strip "$OUT/bin/make"
