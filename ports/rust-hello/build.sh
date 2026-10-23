# STELA loads static, non-PIE executables (ET_EXEC).
export RUSTUP_TOOLCHAIN=$(sed -n 's/^channel = "\(.*\)"/\1/p' "$STELA_ROOT/rust-toolchain.toml")
RUSTFLAGS="-C relocation-model=static -C target-feature=+crt-static \
-C link-arg=-Wl,-z,max-page-size=4096 -C link-arg=-Wl,--build-id=none" \
    cargo build --release --target x86_64-unknown-linux-musl --target-dir "$SRC/target"
mkdir -p "$OUT/bin"
cp "$SRC/target/x86_64-unknown-linux-musl/release/rust-hello" "$OUT/bin/"
