# allnoconfig, then the applets of applets.txt, defaults for their
# sub-options; static and not position independent.
make allnoconfig >/dev/null
while read -r line; do
    case "$line" in ''|'#'*) continue;; esac
    key=${line%%=*}
    if [ "$key" = "$line" ]; then value=y; else value=${line#*=}; fi
    sed -i "/^# CONFIG_$key is not set\$/d; /^CONFIG_$key=/d" .config
    echo "CONFIG_$key=$value" >> .config
done < "$PORT/applets.txt"
sed -i '/^CONFIG_EXTRA_CFLAGS=/d; /^CONFIG_EXTRA_LDFLAGS=/d; /^CONFIG_PREFIX=/d' .config
echo 'CONFIG_EXTRA_CFLAGS="-fno-pie"' >> .config
echo 'CONFIG_EXTRA_LDFLAGS="-no-pie -Wl,-z,max-page-size=4096"' >> .config
yes '' | make oldconfig >/dev/null
make -j"$JOBS" CC="$MUSL_GCC" HOSTCC=gcc busybox
mkdir -p "$OUT/bin"
cp busybox "$OUT/bin/busybox"
