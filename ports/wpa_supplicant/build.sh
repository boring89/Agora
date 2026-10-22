# wpa_supplicant, wpa_cli and wpa_passphrase, static, with the internal
# crypto and TLS (no OpenSSL). P14 K15: compile-only. STELA has no
# driver interface for it yet (FreeBSD's net80211 ioctls through bsdnet,
# docs/bsdkpi.md), so only the "none" and "wired" drivers are built and
# nothing associates; wpa_passphrase works (PBKDF2).
cd wpa_supplicant
cat > .config <<'CONFIG'
CONFIG_DRIVER_NONE=y
CONFIG_DRIVER_WIRED=y
CONFIG_CTRL_IFACE=y
CONFIG_BACKEND=file
CONFIG_TLS=internal
CONFIG_INTERNAL_LIBTOMMATH=y
CONFIG_CRYPTO=internal
CONFIG_NO_RANDOM_POOL=y
CONFIG_ELOOP=eloop
CONFIG_L2_PACKET=none
CONFIG_NO_CONFIG_BLOBS=y
CONFIG
# CFLAGS and LDFLAGS from the environment: the Makefile appends to them.
CFLAGS="-O2 -fno-pie" LDFLAGS="-static -no-pie -Wl,-z,max-page-size=4096" \
    make -j"$JOBS" CC="$MUSL_GCC" >/dev/null
mkdir -p "$OUT/bin"
cp wpa_supplicant wpa_cli wpa_passphrase "$OUT/bin/"
strip "$OUT/bin/wpa_supplicant" "$OUT/bin/wpa_cli" "$OUT/bin/wpa_passphrase"
