#!/usr/bin/env bash
set -Eeuo pipefail

REPO="https://github.com/arkeejs/FFlag-Injector.git"
RAW="https://raw.githubusercontent.com/arkeejs/FFlag-Injector/refs/heads/main"
APP_DIR="${HOME}/.local/share/fflags-injector"
BIN_DIR="${HOME}/.local/bin"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

banner() {
  clear 2>/dev/null || true
  printf '\n  FFlags Injector — By ArkeeDev\n'
  printf '  ★ https://github.com/arkeejs/FFlag-Injector\n\n'
}

need_python() {
  command -v python3 >/dev/null 2>&1 || {
    echo "Python 3 is required. Install it with your distro package manager."
    exit 1
  }
  python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' || {
    echo "Python 3.10 or newer is required."
    exit 1
  }
}

install_deps() {
  python3 -m venv "$APP_DIR/.venv"
  "$APP_DIR/.venv/bin/python" -m pip install --upgrade pip
  "$APP_DIR/.venv/bin/python" -m pip install -r "$APP_DIR/requirements.txt"
}

make_launcher() {
  mkdir -p "$BIN_DIR"
  cat > "$BIN_DIR/fflags-injector" <<EOF_LAUNCHER
#!/usr/bin/env bash
exec "$APP_DIR/.venv/bin/python" "$APP_DIR/main.py" "\$@"
EOF_LAUNCHER
  chmod +x "$BIN_DIR/fflags-injector"
}

local_setup() {
  need_python
  for file in main.py requirements.txt README.md; do
    [[ -f "$SCRIPT_DIR/$file" ]] || {
      echo "Missing $file. Run this option from the extracted FFlag-Injector folder."
      exit 1
    }
  done
  echo "[•] Installing this extracted ZIP version..."
  mkdir -p "$APP_DIR"
  install -m 644 "$SCRIPT_DIR/main.py" "$APP_DIR/main.py"
  install -m 644 "$SCRIPT_DIR/requirements.txt" "$APP_DIR/requirements.txt"
  install -m 644 "$SCRIPT_DIR/README.md" "$APP_DIR/README.md"
  install_deps
  make_launcher
  echo "[✓] Local Setup completed."
}

quick_setup() {
  need_python
  command -v curl >/dev/null 2>&1 || { echo "curl is required."; exit 1; }
  echo "[•] Downloading the latest files from GitHub (no Git clone)..."
  mkdir -p "$APP_DIR"
  curl -fsSL "$RAW/main.py" -o "$APP_DIR/main.py"
  curl -fsSL "$RAW/requirements.txt" -o "$APP_DIR/requirements.txt"
  curl -fsSL "$RAW/README.md" -o "$APP_DIR/README.md"
  install_deps
  make_launcher
  echo "[✓] Quick Setup completed."
}

git_setup() {
  need_python
  command -v git >/dev/null 2>&1 || { echo "Git is required."; exit 1; }
  echo "[•] Installing/updating with Git..."
  mkdir -p "$(dirname "$APP_DIR")"
  if [[ -d "$APP_DIR/.git" ]]; then
    git -C "$APP_DIR" pull --ff-only
  elif [[ -e "$APP_DIR" ]]; then
    echo "A non-Git installation already exists at $APP_DIR."
    echo "Use Quick Setup to replace it, or back it up before switching to Git."
    exit 1
  else
    git clone "$REPO" "$APP_DIR"
  fi
  install_deps
  make_launcher
  echo "[✓] Git Setup completed."
}

banner
echo "Choose installation method:"
echo "  [1] Local Setup  — install this extracted ZIP version"
echo "  [2] Quick Setup  — download latest files directly, no Git"
echo "  [3] Git Setup    — clone/update repository"
echo "  [0] Exit"

if [[ ! -r /dev/tty ]]; then
  echo "An interactive terminal is required. Run this command in a terminal."
  exit 1
fi
read -r -p "Select [1/2/3/0]: " choice </dev/tty

case "$choice" in
  1) local_setup ;;
  2) quick_setup ;;
  3) git_setup ;;
  0) exit 0 ;;
  *) echo "Invalid selection."; exit 2 ;;
esac

echo
echo "Run the app with: fflags-injector"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    echo "Add this to your Fish config: fish_add_path $BIN_DIR"
    echo "Or add to Bash/Zsh: export PATH=\"\$HOME/.local/bin:\$PATH\""
    ;;
esac
