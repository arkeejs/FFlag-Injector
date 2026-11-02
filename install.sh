#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/ArkeeDev/FFlags-Injector.git"
APP_DIR="${HOME}/.local/share/fflags-injector"
BIN_DIR="${HOME}/.local/bin"

banner() {
  clear 2>/dev/null || true
  printf '\n'
  printf '             FFlags Injector\n'
  printf '                By ArkeeDev\n\n'
  printf '       ★ Give us a star on GitHub :)\n\n'
}

need_python() {
  command -v python3 >/dev/null 2>&1 || {
    echo "Python 3 is required. Install it with your distro package manager."
    exit 1
  }
}

setup_quick() {
  echo "[•] Preparing Quick Setup (no Git clone)..."
  need_python
  mkdir -p "$APP_DIR" "$BIN_DIR"
  # This mode downloads the application source directly, without cloning Git history.
  curl -fsSL "https://raw.githubusercontent.com/ArkeeDev/FFlags-Injector/main/main.py" -o "$APP_DIR/main.py"
  curl -fsSL "https://raw.githubusercontent.com/ArkeeDev/FFlags-Injector/main/requirements.txt" -o "$APP_DIR/requirements.txt"
  python3 -m pip install --user -r "$APP_DIR/requirements.txt"
  cat > "$BIN_DIR/fflags-injector" <<EOF
#!/usr/bin/env bash
exec python3 "$APP_DIR/main.py" "\$@"
EOF
  chmod +x "$BIN_DIR/fflags-injector"
  echo "[✓] Quick Setup completed. Run: fflags-injector"
}

setup_git() {
  echo "[•] Installing with Git..."
  need_python
  command -v git >/dev/null 2>&1 || {
    echo "Git is required for Git Installation."
    exit 1
  }
  mkdir -p "$(dirname "$APP_DIR")" "$BIN_DIR"
  if [[ -d "$APP_DIR/.git" ]]; then
    git -C "$APP_DIR" pull --ff-only
  else
    git clone "$REPO" "$APP_DIR"
  fi
  python3 -m pip install --user -r "$APP_DIR/requirements.txt"
  cat > "$BIN_DIR/fflags-injector" <<EOF
#!/usr/bin/env bash
exec python3 "$APP_DIR/main.py" "\$@"
EOF
  chmod +x "$BIN_DIR/fflags-injector"
  echo "[✓] Git Installation completed. Run: fflags-injector"
}

banner
echo "Choose installation method:"
echo "  [1] Quick Setup  - no Git clone (fetches the latest app files)"
echo "  [2] Git Setup    - clone/update the repository"
echo "  [0] Exit"
read -r -p "Select [1/2/0]: " choice
case "$choice" in
  1) setup_quick ;;
  2) setup_git ;;
  0) exit 0 ;;
  *) echo "Invalid option."; exit 2 ;;
esac

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "Add this to your shell profile: export PATH=\"\$HOME/.local/bin:\$PATH\"" ;;
esac
