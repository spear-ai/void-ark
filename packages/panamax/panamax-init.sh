#!/bin/bash
set -euo pipefail

# Check prerequisites
command -v cargo >/dev/null 2>&1 || { echo "Error: cargo is required but not installed." >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Error: docker is required but not installed." >&2; exit 1; }

# Create a vendor directory with all the intended binaries
cargo vendor --manifest-path ./Cargo.toml ./mirrors/vendor

# Initialize the panamax files needed for panamax
docker run --rm -it -v ./mirrors:/mirror --user "$(id -u)" panamaxrs/panamax init /mirror

# Overwrite mirror toml with base existing one
cp ./mirror.toml.base ./mirrors/mirror.toml

echo "Initialization successful"
echo "Please remember to edit the base_url within mirrors/mirror.toml to match the ip of the machine!"