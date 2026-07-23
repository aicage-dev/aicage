# Base image tooling

All prebuilt `aicage` base images install the same tool categories, with minor distro-specific package differences.
This page summarizes what is included.

## Tool groups

<!-- pyml disable md013 -->
| Group                   | Included tooling                                                                                                                                                                                         |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Core shell/dev tools    | bash, bash-completion, bats, ca-certificates, curl, dns/network tools, file, git, gnupg, jq, less, nano, netcat, openssh-client, p7zip, patch, ripgrep, rsync, tar, time, tini, tree, unzip, xz, yq, zip |
| Locale + user switching | locale packages, gosu                                                                                                                                                                                    |
| C/C++ toolchain         | compiler/build toolchain, clang, cmake, gdb, lld/lldb, strace/ltrace, ninja, pkg-config, valgrind, ssl/zlib dev headers                                                                                  |
| musl toolchain          | musl-based C toolchain support for Linux native/static builds; `musl-gcc` on Debian/Red Hat family images, native musl userspace on Alpine                                                               |
| Java ecosystem          | latest Temurin JDK, ant, maven, protobuf compiler                                                                                                                                                        |
| Gradle                  | latest Gradle release                                                                                                                                                                                    |
| Python ecosystem        | python3, pip, venv/virtualenv, python dev headers, pipx, uv                                                                                                                                              |
| Perl                    | perl runtime                                                                                                                                                                                             |
| Ruby ecosystem          | ruby, gem, bundler, ruby dev headers/tooling                                                                                                                                                             |
| Node.js ecosystem       | Node.js (LTS on non-Alpine, distro package on Alpine), npm/npx, corepack (when available), xdg-utils                                                                                                     |
| Go                      | golang/go                                                                                                                                                                                                |
| Rust ecosystem          | rustup with minimal profile, rustc/cargo, rustfmt, clippy                                                                                                                                                |
| Docker client tooling   | Docker CLI, Compose plugin, Buildx plugin                                                                                                                                                                |
<!-- pyml enable md013 -->

## Version policy

- JDK: latest feature release from Adoptium (Temurin).
- Gradle: current release from Gradle services.
- Node.js (non-Alpine): latest LTS release from nodejs.org.
- Rust: installed via rustup with `rustfmt` and `clippy`.
- musl support: provided via distro-native packages on Debian and Red Hat family images; Alpine already uses musl as its native libc.

Exact versions may change over time as upstream releases move.

## Source of truth

Installer scripts:

- `scripts/os-installers/distro/*/install/*.sh`
- `scripts/os-installers/generic/*.sh`

Repository: [aicage-image-base](https://github.com/aicage/aicage-image-base)
