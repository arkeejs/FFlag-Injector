# FFlags Injector

**Linux Roblox Fast Flags manager built with Python + Rich.**

**By ArkeeDev** · https://github.com/arkeejs/FFlag-Injector

Current application version: **2.1.0**

## Features

- Detect Sober Flatpak and common Roblox Wine prefixes.
- Store Sober flags in `config.json → fflags` without replacing unrelated Sober settings.
- Parse Sober JSONC comments and trailing commas; preserve the leading warning header.
- Preview changes and create timestamped backups before writing.
- Paste, import, export, validate, view and clear FFlags.
- Save and apply local profiles; restore backups.
- System diagnostics and activity log.
- Refresh the terminal interface in place instead of stacking menus.

## Requirements

- Linux
- Python 3.10+
- `curl` for Quick Setup
- `git` for Git Setup

## Installation

### Quick Setup (no Git clone)

```bash
curl -fsSL https://raw.githubusercontent.com/arkeejs/FFlag-Injector/refs/heads/main/install.sh | bash
```

Choose option `2` (**Quick Setup**). It downloads the latest application files directly from GitHub and installs dependencies in a virtual environment.

### Git Setup

```bash
git clone https://github.com/arkeejs/FFlag-Injector.git
cd FFlag-Injector
bash install.sh
```

Choose option `3` (**Git Setup**).

### Local Setup from ZIP

Extract the release ZIP, enter the `FFlags-Injector` folder, run `bash install.sh`, and choose option `1` (**Local Setup**).

## Run

```bash
fflags-injector
fflags-injector --version
```

For Fish, add the launcher directory if needed:

```fish
fish_add_path ~/.local/bin
```

## Sober configuration

Default path:

`~/.var/app/org.vinegarhq.Sober/config/sober/config.json`

FFlags are stored inside the nested `fflags` object. Existing Sober settings are preserved and a timestamped backup is created before changes.

## Important

- Close Roblox/Sober before changing configuration, then restart it after injection.
- Roblox may ignore flags outside its current allowlist; this tool does not guarantee FPS improvements or bypass restrictions.

## License

MIT
