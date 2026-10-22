# libtool drops -static (it only means "no shared libtool libraries");
# -all-static at make time links the program statically (musl has a
# libc.so since P13).
# curl and libcurl, static, TLS from Mbed TLS and zlib ($DEPS). The CA
# bundle is STELA's (Initrd:/certs is DER; curl wants PEM): the package
# carries share/cacert.pem from STELA's third_party/mozilla-ca.
./configure --host=x86_64-linux-musl CC="$MUSL_GCC" CFLAGS="-O2 -fno-pie" \
    CPPFLAGS="-I$DEPS/include" LDFLAGS="-static -no-pie -Wl,-z,max-page-size=4096 -L$DEPS/lib" \
    --prefix=/ --disable-shared --enable-static --with-mbedtls="$DEPS" --with-zlib="$DEPS" \
    --without-libpsl --without-brotli --without-zstd --without-libidn2 --without-nghttp2 \
    --disable-ldap --disable-ldaps --without-librtmp --disable-threaded-resolver \
    --disable-docs --disable-manual \
    --with-ca-bundle=/Data/Programs/curl/share/cacert.pem --without-ca-path >/dev/null
make -j"$JOBS" LDFLAGS="-all-static -no-pie -Wl,-z,max-page-size=4096 -L$DEPS/lib" >/dev/null
make install DESTDIR="$OUT" >/dev/null
rm -rf "$OUT/share" "$OUT/lib/pkgconfig" "$OUT/lib/libcurl.la" "$OUT/bin/curl-config" "$OUT/bin/wcurl"
mkdir -p "$OUT/share"
cp "$STELA_ROOT/third_party/mozilla-ca/cacert.pem" "$OUT/share/"
strip "$OUT/bin/curl"
