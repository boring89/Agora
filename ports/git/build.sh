# Git, static: zlib, libcurl with Mbed TLS ($DEPS) for http(s) remotes; no
# Perl, Python, Tcl/Tk, gettext or expat. bin/git and the HTTP helper in
# libexec/git-core (where git looks: --exec-path, set at build time).
# C17: git 2.47 names a struct member thread_local (a C23 keyword).
# Commands git runs through a shell (local transport: git-upload-pack)
# use dash, a runtime dependency (STELA has no /bin/sh).
cat > config.mak <<EOM
CC = $MUSL_GCC
CFLAGS = -O2 -fno-pie -std=gnu17 -I$DEPS/include
LDFLAGS = -static -no-pie -Wl,-z,max-page-size=4096 -L$DEPS/lib
prefix = /Data/Programs/git
NO_OPENSSL = 1
NO_PERL = 1
NO_PYTHON = 1
NO_TCLTK = 1
NO_GETTEXT = 1
NO_EXPAT = 1
NO_INSTALL_HARDLINKS = 1
NO_REGEX = NeedsStartEnd
CURLDIR = $DEPS
CURL_LDFLAGS = -lcurl -lmbedtls -lmbedx509 -lmbedcrypto -lz
ZLIB_PATH = $DEPS
uname_S = Linux
EOM
# The build itself runs with the build machine's /bin/sh; only the shell
# compiled into git (SHELL_PATH) is dash's path on STELA.
sed -i "s|^BASIC_CFLAGS += -DSHELL_PATH='\$(SHELL_PATH_CQ_SQ)'|BASIC_CFLAGS += -DSHELL_PATH='\"/Data/Programs/dash/bin/dash\"'|" Makefile
grep -q 'DSHELL_PATH=.*dash' Makefile
make -j"$JOBS" git git-remote-http >/dev/null
mkdir -p "$OUT/bin" "$OUT/libexec/git-core"
cp git "$OUT/bin/"
cp git-remote-http "$OUT/libexec/git-core/"
cp git-remote-http "$OUT/libexec/git-core/git-remote-https"
# The local transport starts git-upload-pack (a git builtin by name).
cp git "$OUT/libexec/git-core/git-upload-pack"
strip "$OUT/bin/git" "$OUT"/libexec/git-core/*
