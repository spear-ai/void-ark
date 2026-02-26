+---
+panamax: minor
+---
- Adds crates for Apache Arrow, YAML, and TOML
- Add crates wincode and rkyv to replace bincode
- Renamed mirror.toml.base to mirror.base.toml, to keep syntax highlighting in editors looking for the .toml extension
- Added GNU and musl Rustup targets for both x86_64 and i686
- I updated all crate versions
- Rather than grouping by use, I organized alphabetically. That should help us avoid duplicates.
- I had trouble getting Cargo.toml to resolve without a compile target, so I needed to create a trivial src/lib.rs.
- Other small changes like specifying the container name in the docker-compose.yml
