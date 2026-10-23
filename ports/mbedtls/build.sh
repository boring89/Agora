# A library port (P13 K7): lib/libmbedtls.a, libmbedx509.a,
# libmbedcrypto.a and include/{mbedtls,psa}; a test program (hashes, AES-GCM).
make -j"$JOBS" lib CC="$MUSL_GCC" AR=ar CFLAGS="-O2 -fno-pie" >/dev/null
mkdir -p "$OUT/lib" "$OUT/include" "$OUT/bin"
cp library/libmbedtls.a library/libmbedx509.a library/libmbedcrypto.a "$OUT/lib/"
cp -r include/mbedtls include/psa "$OUT/include/"
"$MUSL_GCC" -O2 -static -no-pie -fno-pie -Wl,-z,max-page-size=4096 -I"$OUT/include" \
    "$PORT/test.c" -L"$OUT/lib" -lmbedtls -lmbedx509 -lmbedcrypto -o "$OUT/bin/mbedtls-test"
strip "$OUT/bin/mbedtls-test"
