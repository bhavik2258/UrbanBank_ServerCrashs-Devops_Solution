#!/usr/bin/env bash
set -euo pipefail

# Renders Mermaid diagrams found in docs/*.mmd to PNG using mermaid-cli
OUT_DIR="docs"
mkdir -p "$OUT_DIR"

if ! command -v npx >/dev/null 2>&1; then
  echo "npx is required to run @mermaid-js/mermaid-cli. Install Node.js/npm or run this inside a Node-enabled environment."
  exit 1
fi

echo "Rendering docs/architecture.mmd -> docs/architecture.png"
npx -y @mermaid-js/mermaid-cli -i "$OUT_DIR/architecture.mmd" -o "$OUT_DIR/architecture.png"

echo "Rendered: $OUT_DIR/architecture.png"
