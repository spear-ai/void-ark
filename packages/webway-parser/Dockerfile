# Use the official Rust image as the base
FROM rust:1.87

# Install only the rustup components you need
RUN rustup component add rustfmt clippy llvm-tools-preview

# Add target architecture
RUN rustup target add i686-unknown-linux-gnu

# Install cargo-llvm-cov for test coverage
RUN cargo install cargo-llvm-cov

# Install system dependencies
RUN apt-get update && apt-get install -y \
    vim \
    libsasl2-dev \
    libssl-dev \
    pkg-config \
    cmake \
    protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

RUN dpkg --add-architecture i386 && \
apt-get update && \
apt-get install -y \
    gcc-multilib \
    g++-multilib \
    libc6-dev-i386 \
    libstdc++6:i386 \
    libc6:i386 \
    libclang-dev \
    clang \
&& rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy dependency files and fetch everything
COPY Cargo.toml Cargo.lock ./
COPY README.md ./
RUN cargo fetch

# Create a dummy main.rs to trigger dependency compilation
RUN mkdir -p src/bin && \
    echo "fn main() {}" > src/main.rs && \
    echo "fn main() {}" > src/bin/apb19_file_parser.rs && \
    echo "fn main() {}" > src/bin/apb21_file_parser.rs && \
    echo "" > src/lib.rs

# Build dependencies (this will compile and cache all dependencies)
RUN cargo build --release && \
    cargo build --bins --release

# Remove the dummy source files
RUN rm -rf src/

# Copy source code (for when you want to build/test)
COPY src/ ./src/

# Set a shell as default command since you're keeping vim
CMD ["/bin/bash"]