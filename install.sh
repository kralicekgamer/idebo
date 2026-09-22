#!/bin/bash
set -euo pipefail

INSTALL_DIR="${IDEBO_INSTALL_DIR:-$HOME/.local/share/idebo}"
BIN_DIR="${IDEBO_BIN_DIR:-$HOME/.local/bin}"
REPO_DIR="$INSTALL_DIR/repo"

echo "Instalace idebo..."
mkdir -p "$INSTALL_DIR" "$BIN_DIR"

if [ -d "$REPO_DIR/.git" ]; then
    git -C "$REPO_DIR" pull --ff-only
else
    rm -rf "$REPO_DIR"
    git clone https://github.com/kralicekgamer/idebo.git "$REPO_DIR"
fi

python3 -m venv "$REPO_DIR/.venv"
"$REPO_DIR/.venv/bin/python" -m pip install --upgrade pip
"$REPO_DIR/.venv/bin/python" -m pip install "$REPO_DIR"

cat > "$BIN_DIR/idebo" <<EOF
#!/bin/sh
exec "$REPO_DIR/.venv/bin/idebo" "\$@"
EOF
chmod +x "$BIN_DIR/idebo"

echo "Instalace dokončena: $BIN_DIR/idebo"
echo "Pokud příkaz není nalezen, přidejte $BIN_DIR do PATH."
