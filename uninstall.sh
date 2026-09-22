#!/bin/bash
set -euo pipefail

BIN="${IDEBO_BIN_DIR:-$HOME/.local/bin}/idebo"
INSTALL_DIR="${IDEBO_INSTALL_DIR:-$HOME/.local/share/idebo}"

rm -f "$BIN"
rm -rf "$INSTALL_DIR"
echo "idebo bylo odinstalováno."
