#!/bin/bash
# install_license.sh — install license*.json (excluding license_request*.json) into /opt/AutoDrive/

set -Eeuo pipefail

TARGET_DIR="/opt/AutoDrive"

# Make globs that don't match expand to nothing
shopt -s nullglob

# Collect candidates from current directory
candidates=(license*.json)

# Filter out license_request*.json
FILES=()
for f in "${candidates[@]}"; do
  base="$(basename "$f")"
  [[ "$base" == license_request*.json ]] && continue
  FILES+=("$f")
done

# Check if any file exists
if [ ${#FILES[@]} -eq 0 ]; then
  echo "No valid license*.json file found in current directory (excluding license_request*.json)."
  exit 1
fi

# If more than one file, let user choose
if [ ${#FILES[@]} -gt 1 ]; then
  echo "Multiple license files found:"
  PS3="#? "
  select LICENSE_FILE in "${FILES[@]}"; do
    if [ -n "${LICENSE_FILE:-}" ]; then
      break
    fi
  done
else
  LICENSE_FILE="${FILES[0]}"
fi

# Ask for confirmation
echo "Selected license file: $LICENSE_FILE"
read -r -p "Do you want to proceed with installation? [y/N] " CONFIRM
CONFIRM=${CONFIRM:-N}
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
  echo "Installation aborted."
  exit 0
fi

echo "Installing license file to $TARGET_DIR..."

sudo mkdir -p "$TARGET_DIR"

# Backup existing license.json if it exists
if [ -f "$TARGET_DIR/license.json" ]; then
  BACKUP_NAME="license.json.bak-$(date +%Y%m%d%H%M%S)"
  echo "Existing license.json found. Backing up to $TARGET_DIR/$BACKUP_NAME"
  sudo mv "$TARGET_DIR/license.json" "$TARGET_DIR/$BACKUP_NAME"
fi

# Install new license
sudo cp "$LICENSE_FILE" "$TARGET_DIR/license.json"
sudo cp "$LICENSE_FILE" "$TARGET_DIR/"

echo "License installed as:"
echo " - $TARGET_DIR/license.json"
echo " - $TARGET_DIR/$(basename "$LICENSE_FILE") (backup of original filename)"
