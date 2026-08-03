fn main() {
    println!("cargo:rerun-if-changed=build.rs");
    if std::env::var("CARGO_CFG_TARGET_ARCH").as_deref() == Ok("wasm32") {
        // Keep this policy in the build script rather than `.cargo/config.toml`:
        // Cargo discovers config from its invocation directory, so a
        // repository-root `--manifest-path` build could otherwise omit it.
        println!("cargo:rustc-link-arg=--export-memory");
        println!("cargo:rustc-link-arg=--max-memory=268435456");
        println!("cargo:rustc-link-arg=-zstack-size=2097152");
    }
}
