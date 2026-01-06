# Use the official Rust image as the base
FROM rust:1.92
 
ARG DEBIAN_FRONTEND=noninteractive

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
    libclang-dev \
&& rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /usr/src/app

# Set a shell as default command since you're keeping vim
CMD ["/bin/bash"]