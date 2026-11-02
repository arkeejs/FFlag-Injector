# FFlags Injector

A modern terminal-based FFlags utility for Linux, built with Python and Rich.

**By ArkeeDev**

## Features

- Animated terminal splash screen and setup checks
- Linux distribution and Sober detection
- Interactive FFlags JSON input and validation
- Merge FFlags into an existing JSON object
- Automatic timestamped backups before changes
- View, restore, and clear configuration
- Quick Setup without cloning Git history
- Git installation with pull-to-update support

## Requirements

- Linux
- Python 3.9+
- `curl` for Quick Setup
- `git` for Git Installation
- Python package `rich` (installed by the setup script)

## Installation

### Quick Setup (no Git clone)

This fetches the current application files directly from GitHub raw content. It does **not** clone the repository or download Git history.

```bash
curl -fsSL https://raw.githubusercontent.com/arkeejs/FFlags-Injector/main/install.sh | bash
```

### Git Installation

```bash
git clone https://github.com/arkeejs/FFlags-Injector.git
cd FFlags-Injector
bash install.sh
```

Choose option `2` in the installer.

## Run

```bash
fflags-injector
```

If the command is not found, add `~/.local/bin` to PATH:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## FFlags file path

The injector checks common Sober configuration paths first. If none exists, it asks for a path manually. Sober's configuration layout can change between releases, so verify the selected path for your installed version.

## Important

- Close Roblox/Sober before changing flags, then restart it after injection.
- The tool validates JSON and creates a backup before modifying an existing file.
- It merges supplied flags with existing flags; keys with the same name are replaced.
- Only use FFlags that are supported by your Roblox client. Unsupported flags may be ignored or cause unexpected behavior.
- This project does not bypass anti-cheat, modify game binaries, or guarantee FPS improvements.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## License

MIT
