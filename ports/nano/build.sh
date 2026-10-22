# nano with wide-character ncurses ($DEPS), static, no NLS or libmagic.
# musl's <sys/vt.h> includes the kernel's <linux/vt.h>, which the musl
# build does not have: the two things nano uses (Linux UAPI values).
mkdir -p shim/linux
printf '#define VT_GETSTATE 0x5603\nstruct vt_stat { unsigned short v_active, v_signal, v_state; };\n' \
    > shim/linux/vt.h
./configure --host=x86_64-linux-musl CC="$MUSL_GCC" CFLAGS="-O2 -fno-pie" \
    CPPFLAGS="-I$DEPS/include -I$PWD/shim" LDFLAGS="-static -no-pie -Wl,-z,max-page-size=4096 -L$DEPS/lib" \
    --prefix=/Data/Programs/nano --disable-nls --disable-libmagic --disable-speller \
    --disable-browser >/dev/null
make -j"$JOBS" >/dev/null
mkdir -p "$OUT/bin"
cp src/nano "$OUT/bin/"
strip "$OUT/bin/nano"
