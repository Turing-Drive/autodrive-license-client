#!/bin/bash
# install_license.sh — place license.json into /opt/app/

set -e

TARGET_DIR="/opt/app"
LICENSE_FILE="license.json"

if [ ! -f "$LICENSE_FILE" ]; then
    echo "$LICENSE_FILE not found in current directory."
    echo "Please make sure you have the license.json file before running this script."
    exit 1
fi

echo "Installing license file to $TARGET_DIR..."

sudo mkdir -p "$TARGET_DIR"
sudo cp "$LICENSE_FILE" "$TARGET_DIR/"

echo "License installed at $TARGET_DIR/$LICENSE_FILE"
