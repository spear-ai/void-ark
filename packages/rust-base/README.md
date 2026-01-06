# Rust Base

This package serves as a dummy package containing a base rust dockerfile and a Cargo.toml referred to by the panamax package.

## 🎯 Code Conventions

Each Rust struct should:

- Maintain the exact data type as the original C-struct
- Struct names should be `UpperCamelCase`
- Field names should be `snake_case`

## 📋 Quick Commands

```bash
# Basic testing
cargo test                              # Run all unit tests
cargo test --lib                        # Run only library tests
cargo test --features property-tests    # Include property-based tests
cargo test --features integration-tests # Include integration tests (needs Docker)
cargo test --features full-test-suite   # Run everything

# Linting and formatting
cargo fmt                               # Format code
cargo fmt -- --check                   # Check formatting without changes
cargo clippy                           # Run linter
cargo clippy -- -D warnings            # Treat warnings as errors

# Documentation
cargo doc                               # Generate documentation
cargo doc --open                       # Generate and open docs
cargo test --doc                       # Test code examples in docs

# Coverage (requires cargo-llvm-cov)
cargo llvm-cov --all-features              # Quick coverage report in terminal
cargo llvm-cov --all-features --html       # Generate HTML coverage report
cargo llvm-cov --all-features --lcov --output-path lcov.info  # LCOV format for CI/CD

# Docker coverage
docker run --rm your-image cargo llvm-cov --all-features  # Run coverage in container
```

## 🔧 Setup Requirements

### Core Tools

Install these tools for the full development experience:

```bash
# Essential tools
rustup component add rustfmt clippy

# Coverage tool 
cargo install cargo-llvm-cov
```

## 🧹 Code Quality Tools

### Formatting with `rustfmt`

```bash
# Format all code
cargo fmt

# Check if code is formatted (CI usage)
cargo fmt -- --check
```

**Configuration**: Create `.rustfmt.toml` for custom formatting rules:

```toml
max_width = 100
hard_tabs = false
tab_spaces = 4
newline_style = "Unix"
use_small_heuristics = "Default"
```

### Linting with `clippy`

```bash
# Basic linting
cargo clippy

# Strict linting (treat warnings as errors)
cargo clippy -- -D warnings

# Fix automatically fixable issues
cargo clippy --fix

# Lint tests too
cargo clippy --tests
```

## 📚 Additional Resources

- [Rust Testing Guide](https://doc.rust-lang.org/book/ch11-00-testing.html)
- [Clippy Lint List](https://rust-lang.github.io/rust-clippy/master/)
- [Property-Based Testing with QuickCheck](https://docs.rs/quickcheck/latest/quickcheck/)
- [Testcontainers for Rust](https://docs.rs/testcontainers/latest/testcontainers/)
- [Criterion Benchmarking](https://bheisler.github.io/criterion.rs/book/)
