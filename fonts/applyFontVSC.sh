#!/usr/bin/env bash
set -euo pipefail

ROOT_PATH="/home/user/.vscode/cli/serve-web/"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for dir in "$ROOT_PATH"/*/; do
  TARGET_PATH="$dir/out/vs/code/browser/workbench"
  FONT_CSS="$TARGET_PATH/font.css"
  WORKBENCH_CSS="$TARGET_PATH/workbench.css"

  if [ -f "$WORKBENCH_CSS" ]; then
    # Add @import "font.css"; to the first line if not present
    grep -qx '@import "font.css";' "$WORKBENCH_CSS" ||
      sed -i '1i@import "font.css";' "$WORKBENCH_CSS"
  fi

  mkdir -p "$TARGET_PATH"
  cp "$SCRIPT_DIR/font.css" "$TARGET_PATH/"
  cp "$SCRIPT_DIR"/*.ttf "$TARGET_PATH/" 2>/dev/null || true

  # if [ ! -f "$FONT_CSS" ]; then
  #   mkdir -p "$TARGET_PATH"
  #   cp "$SCRIPT_DIR/font.css" "$TARGET_PATH/"
  #   cp "$SCRIPT_DIR"/*.ttf "$TARGET_PATH/" 2>/dev/null || true

  # else
  #   cp "$SCRIPT_DIR/font.css" "$TARGET_PATH/"
  #   cp "$SCRIPT_DIR"/*.ttf "$TARGET_PATH/" 2>/dev/null || true
  # fi
done
