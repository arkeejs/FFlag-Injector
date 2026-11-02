# FFlags Injector

A modern terminal-based FFlags utility for Linux, built with Python and Rich.

**By ArkeeDev** · https://github.com/arkeejs/FFlag-Injector

## Features

- Animated terminal splash screen and environment checks
- Automatic Linux distribution and Sober detection
- Sober FFlags are written inside the nested `fflags` object
- JSON validation, merge, backup, restore, view and clear
- Quick Setup without cloning Git history, or Git installation/update

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

Choose option `2` (Quick Setup).

### Git Setup

```bash
git clone https://github.com/arkeejs/FFlag-Injector.git
cd FFlag-Injector
bash install.sh
```

Choose option `3` (Git Setup).

### Local Setup from ZIP

Extract the release ZIP, enter the `FFlags-Injector` folder, and run:

```bash
bash install.sh
```

Choose option `1` (Local Setup).

## Run

```bash
fflags-injector
```

If Fish cannot find the command, add the launcher directory:

```fish
fish_add_path ~/.local/bin
```

## Sober configuration

Sober configuration path:

`~/.var/app/org.vinegarhq.Sober/config/sober/config.json`

FFlags are stored inside the `fflags` object. The injector merges supplied flags without replacing unrelated settings and creates a timestamped backup before writing.

## Important

- Close Roblox/Sober before changing configuration, then restart it after injection.
- Roblox may ignore flags outside its current allowlist.
- This project does not bypass anti-cheat, modify game binaries, or guarantee FPS improvements.

## License

MIT
