# libtool drops -static (it only means "no shared libtool libraries");
# -all-static at make time links the program statically (musl has a
# libc.so since P13).
# file compiles its magic database with a file of the same version: one
# is built for the build machine first. The database goes to
# share/misc/magic.mgc, where the program looks (Data:/Programs/file).
mkdir -p host && (cd host && ../configure --disable-shared --disable-zlib --disable-bzlib \
    --disable-xzlib --disable-zstdlib --disable-lzlib --disable-libseccomp >/dev/null && \
    make -j"$JOBS" >/dev/null)
./configure --host=x86_64-linux-musl CC="$MUSL_GCC" CFLAGS="-O2 -fno-pie" \
    LDFLAGS="-static -no-pie -Wl,-z,max-page-size=4096" --prefix=/Data/Programs/file \
    --disable-shared --enable-static --disable-zlib --disable-bzlib --disable-xzlib \
    --disable-zstdlib --disable-lzlib --disable-libseccomp >/dev/null
make -j"$JOBS" FILE_COMPILE="$PWD/host/src/file" \
    LDFLAGS="-all-static -no-pie -Wl,-z,max-page-size=4096" >/dev/null
mkdir -p "$OUT/bin" "$OUT/share/misc"
cp src/file "$OUT/bin/"
cp magic/magic.mgc "$OUT/share/misc/"
strip "$OUT/bin/file"
