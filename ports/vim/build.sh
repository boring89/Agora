# Vim with ncurses ($DEPS), static. Cross-built, its configure cannot run
# test programs: the answers a Linux/musl system gives are passed in.
export vim_cv_toupper_broken=no vim_cv_terminfo=yes vim_cv_tgetent=zero \
    vim_cv_getcwd_broken=no vim_cv_stat_ignores_slash=no vim_cv_memmove_handles_overlap=yes \
    vim_cv_bcopy_handles_overlap=yes vim_cv_memcpy_handles_overlap=yes \
    vim_cv_tty_group=world vim_cv_tty_mode=0620
./configure --host=x86_64-linux-musl CC="$MUSL_GCC" CFLAGS="-O2 -fno-pie" \
    CPPFLAGS="-I$DEPS/include" LDFLAGS="-static -no-pie -Wl,-z,max-page-size=4096 -L$DEPS/lib" \
    --prefix=/Data/Programs/vim --with-features=normal --disable-gui --without-x \
    --disable-nls --with-tlib=ncurses --disable-netbeans --disable-channel \
    --disable-terminal --disable-canberra --disable-libsodium --disable-gpm \
    --disable-sysmouse --disable-selinux --disable-xattr --enable-multibyte >/dev/null
make -j"$JOBS" >/dev/null
mkdir -p "$OUT/bin"
cp src/vim "$OUT/bin/"
strip "$OUT/bin/vim"
