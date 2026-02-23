#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/dist"
ZIP_NAME="lloyds-jira-orchestrator.zip"
ZIP_PATH="$OUT_DIR/$ZIP_NAME"

mkdir -p "$OUT_DIR"
rm -f "$ZIP_PATH"

cd "$ROOT_DIR"
zip -r "$ZIP_PATH" . \
  -x ".git/*" \
  -x "dist/*" \
  -x "**/__pycache__/*" \
  -x "*.pyc" \
  -x ".pytest_cache/*" \
  -x ".env"

echo "Created: $ZIP_PATH"
