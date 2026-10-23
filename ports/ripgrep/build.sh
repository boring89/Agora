# P14 K10: a Rust program from crates.io, static for musl (STELA loads
# static, non-PIE executables). Cargo fetches its dependencies from
# crates.io (Cargo.lock in the crate pins them).
export RUSTUP_TOOLCHAIN=$(sed -n 's/^channel = "\(.*\)"/\1/p' "$STELA_ROOT/rust-toolchain.toml")
cd "$SRC"
# jemalloc (a C library some crates build for musl) with STELA's musl-gcc.
export CC_x86_64_unknown_linux_musl="$MUSL_GCC" AR_x86_64_unknown_linux_musl=ar
CARGO_PROFILE_RELEASE_DEBUG=false CARGO_PROFILE_RELEASE_STRIP=symbols \
RUSTFLAGS="-C relocation-model=static -C target-feature=+crt-static \
-C link-arg=-Wl,-z,max-page-size=4096 -C link-arg=-Wl,--build-id=none" \
    cargo build --release --locked --target x86_64-unknown-linux-musl --target-dir "$SRC/target"
mkdir -p "$OUT/bin"
cp "$SRC/target/x86_64-unknown-linux-musl/release/rg" "$OUT/bin/"
