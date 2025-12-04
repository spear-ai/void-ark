# Webway Parser

A Rust library for parsing APB19 and APB21 file formats with support for converting to Arrow and Protobuf formats.

## 🏗️ Project Architecture

### Directory Structure

```rust
src/
├── lib.rs                     // Library code
├── bin/
│   ├── apb19_file_parser.rs   // Binary for APB19 parsing
│   └── apb21_file_parser.rs   // Binary for APB21 parsing  
├── protocols/
│   ├── mod.rs
│   ├── common/
│   │   ├── mod.rs
│   │   ├── primitives.rs
│   │   ├── errors.rs
│   │   └── types.rs
│   ├── ti18-apb19/
│   │   ├── mod.rs
│   │   ├── types.rs
│   │   └── parsers.rs
│   └── ti20-apb21/
│       ├── mod.rs
│       ├── types.rs
│       └── parsers.rs
└── converters/
    ├── mod.rs
    ├── arrow.rs
    └── protobuf.rs
```

### Parsing Architecture

The library follows a component-based architecture where each protocol is parsed using:

1. **Primitives** (`src/protocols/common/primitives.rs`): Low-level data type parsers
2. **Types** (`src/protocols/{protocol}/types.rs`): Rust struct definitions matching C-structs
3. **Parsers** (`src/protocols/{protocol}/parsers.rs`): High-level parsing functions
4. **Converters** (`src/converters/`): Output format converters (Arrow, Protobuf)

## 🔧 Implementation Examples

### Primitive Parsing

Each primitive will be parsed and added to a component-like library:

```rust
// src/protocols/common/primitives.rs
use std::io::Cursor;
use byteorder::{LittleEndian, ReadBytesExt};
use super::errors::ParseError;

pub fn read_i32(data: &[u8], position: usize) -> Result<(i32, usize), ParseError> {
    if position + 4 > data.len() {
        return Err(ParseError::InsufficientData);
    }
    let mut cursor = Cursor::new(&data[position..]);
    let value = cursor.read_i32::<LittleEndian>()?;
    Ok((value, position + 4))
}
```

### Structure Parsing

Each structure parsing file follows this pattern:

```rust
// src/protocols/apb19/parsers.rs
use std::io::Cursor;
use crate::structs::common::{ primitives::*, automation_data::AutomationData, errors::ParseError };
// Or use crate::structs::apb19::AutomationData

pub fn parse_automation_data(cursor: &mut Cursor<&[u8]>) -> Result<AutomationData, ParseError> {
    let field1 = read_i32(cursor)?;
    let field2 = read_f32(cursor)?;

    Ok(AutomationData { field1, field2 })
};

pub fn parse_header_data(cursor: &mut Cursor<&[u8]>) -> Result<HeaderData, ParseError> {
    let field1 = read_i32(cursor)?;
    let field2 = read_f32(cursor)?;

    Ok(HeaderData { field1, field2 })
}
```

### Binary Usage

To call each parsing function:

```rust
// src/bin/apb19_file_parser.rs
use std::env;
use your_crate::protocols::apb19::lib_parser::parse_apb19_file_at_position;
use your_crate::converters::{arrow::*, protobuf::*};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        println!("Usage: apb19_file_parser <input_file> [--output-format arrow|protobuf]");
        return Ok(());
    }
    
    let input_file = &args[1];
    let output_format = args.get(2).map(|s| s.as_str()).unwrap_or("arrow");
    
    println!("Parsing APB19 file: {}", input_file);
    let file_data = std::fs::read(input_file)?;
    let (parsed_file, _) = parse_apb19_file_at_position(&file_data, 0)?;
    
    match output_format {
        "arrow" => {
            let arrow_data = parsed_file.to_arrow()?;
            println!("Converted to Arrow format");
        }
        "protobuf" => {
            let protobuf_data = parsed_file.to_protobuf()?;
            println!("Converted to Protobuf format");
        }
        _ => println!("Unknown output format: {}", output_format),
    }
    
    Ok(())
}
```

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
