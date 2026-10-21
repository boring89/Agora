# Configured for a static musl build; the helper programs it builds and
# runs (mkinit, mknodes...) run on the host too.
CC="$MUSL_GCC" CC_FOR_BUILD=gcc CFLAGS="-O2 -fno-pie -w" LDFLAGS="-static -no-pie -Wl,-z,max-page-size=4096" \
    ./configure --enable-static --host=x86_64-linux-musl >/dev/null
make -j"$JOBS" CC_FOR_BUILD=gcc
mkdir -p "$OUT/bin"
cp src/dash "$OUT/bin/dash"
strip "$OUT/bin/dash"
