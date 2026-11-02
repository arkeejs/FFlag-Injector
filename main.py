#!/usr/bin/env python3
"""FFlags Injector CLI — Linux"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    from rich import box
    from rich.align import Align
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.prompt import Confirm, Prompt
    from rich.text import Text
    from rich.theme import Theme
except ImportError:
    print("Missing dependencies. Run: python3 -m pip install -r requirements.txt")
    raise SystemExit(1)

APP_NAME = "FFlags Injector"
REPO = "https://github.com/ArkeeDev/FFlags-Injector.git"
RAW_INSTALLER = "https://raw.githubusercontent.com/ArkeeDev/FFlags-Injector/main/install.sh"
console = Console(theme=Theme({
    "accent": "bold white",
    "muted": "bright_black",
    "good": "bold green",
    "bad": "bold red",
    "info": "cyan",
}))

HOME = Path.home()
CONFIG_CANDIDATES = [
    HOME / ".var/app/org.vinegarhq.Sober/config/sober/flags.json",
    HOME / ".var/app/org.vinegarhq.Sober/config/sober/ClientAppSettings.json",
    HOME / ".config/sober/flags.json",
    HOME / ".config/sober/ClientAppSettings.json",
]

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def banner():
    clear()
    console.print()
    console.print(Align.center(Text("FFlags Injector", style="bold white", justify="center")))
    console.print(Align.center(Text("By ArkeeDev", style="bright_black")))
    console.print()
    console.print(Align.center(Text("IF YOU LIKE THIS PROJECT", style="bright_black")))
    console.print(Align.center(Text("★ Give us a star on GitHub :)", style="white")))
    console.print()
    console.print(Align.center(Text("Linux CLI • Sober", style="bright_black")))
    console.print()

def animated_step(label, detail=None, duration=0.45):
    import time
    with Progress(
        SpinnerColumn(style="white"),
        TextColumn("[white]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(label, total=None)
        time.sleep(duration)
        progress.stop_task(task)
    suffix = f" [bright_black]— {detail}[/bright_black]" if detail else ""
    console.print(f"[bold white]✓[/bold white] {label}{suffix}")

def distro_name():
    info = {}
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                info[k] = v.strip().strip('"')
    except OSError:
        pass
    return info.get("PRETTY_NAME", platform.system())

def find_sober():
    checks = [
        ("Flatpak installation", ["flatpak", "info", "org.vinegarhq.Sober"]),
        ("Sober executable", ["sh", "-lc", "command -v sober"]),
    ]
    for label, cmd in checks:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return label
        except (OSError, subprocess.SubprocessError):
            pass
    return None

def choose_config():
    existing = [p for p in CONFIG_CANDIDATES if p.exists()]
    if existing:
        console.print("[muted]Detected possible configuration files:[/muted]")
        for i, path in enumerate(existing, 1):
            console.print(f"  [white]{i}.[/white] {path}")
        console.print(f"  [white]{len(existing)+1}.[/white] Enter a custom path")
        choice = Prompt.ask("Select configuration file", default="1")
        if choice.isdigit() and 1 <= int(choice) <= len(existing):
            return existing[int(choice)-1]
    else:
        console.print("[yellow]No known Sober FFlags file was found.[/yellow]")
        console.print("[muted]The path can vary between Sober versions and installations.[/muted]")
    raw = Prompt.ask("FFlags JSON file path", default=str(CONFIG_CANDIDATES[0]))
    return Path(raw).expanduser()

def read_multiline_json():
    console.print(Panel(
        "Paste your FFlags JSON below.\n"
        "Finish by entering a line containing only [bold white].[/bold white]",
        title="FFlags Configuration", border_style="white"
    ))
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == ".":
            break
        lines.append(line)
    raw = "\n".join(lines).strip()
    if not raw:
        raise ValueError("No JSON was provided.")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("FFlags JSON must be an object, e.g. {\"FlagName\": true}.")
    if not all(isinstance(k, str) for k in data):
        raise ValueError("Every FFlag name must be a string.")
    return data

def backup_file(path: Path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(path.name + f".backup-{stamp}")
    shutil.copy2(path, backup)
    return backup

def inject(path: Path, flags: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = backup_file(path)
    # Merge with existing object instead of silently discarding unrelated flags.
    existing = {}
    if path.exists():
        try:
            loaded = json.loads(path.read_text())
            if isinstance(loaded, dict):
                existing = loaded
        except (json.JSONDecodeError, OSError):
            raise ValueError("The existing file is not valid JSON. It was left untouched.")
    existing.update(flags)
    payload = json.dumps(existing, indent=2, ensure_ascii=False) + "\n"
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(payload)
    temp.replace(path)
    return backup, len(existing)

def show_menu():
    console.print(Panel(
        "[bold white]1[/bold white]  Inject FFlags\n"
        "[bold white]2[/bold white]  View current FFlags\n"
        "[bold white]3[/bold white]  Restore a backup\n"
        "[bold white]4[/bold white]  Clear FFlags\n"
        "[bold white]5[/bold white]  Check environment\n"
        "[bold white]0[/bold white]  Exit",
        title="Main Menu", border_style="white", box=box.ROUNDED
    ))

def environment_check():
    animated_step("Detecting Linux distribution", distro_name())
    found = find_sober()
    if found:
        animated_step("Detecting Roblox environment", f"Sober detected ({found})")
    else:
        console.print("[yellow]• Sober was not detected automatically.[/yellow]")
        console.print("[muted]You can still choose a configuration path manually.[/muted]")
    path = choose_config()
    animated_step("Checking configuration path", str(path))
    console.print("[good]Environment check complete.[/good]")
    return path

def inject_flow(path):
    try:
        flags = read_multiline_json()
        console.print(f"\n[muted]Validated {len(flags)} FFlag(s).[/muted]")
        if not Confirm.ask("Apply these FFlags?", default=True):
            return
        with Progress(SpinnerColumn(), TextColumn("[white]Writing configuration..."),
                      BarColumn(), TimeElapsedColumn(), console=console) as progress:
            task = progress.add_task("inject", total=100)
            for _ in range(5):
                progress.update(task, advance=20)
                import time
                time.sleep(0.12)
            backup, count = inject(path, flags)
        console.print("[good]✓ FFlags injected successfully.[/good]")
        console.print(f"[muted]File: {path}[/muted]")
        console.print(f"[muted]Total flags in file: {count}[/muted]")
        if backup:
            console.print(f"[muted]Backup: {backup}[/muted]")
        console.print("[yellow]Restart Sober for the changes to take effect.[/yellow]")
    except (ValueError, json.JSONDecodeError) as exc:
        console.print(f"[bad]✗ {exc}[/bad]")

def view_flow(path):
    if not path.exists():
        console.print("[yellow]No FFlags file exists at the selected path.[/yellow]")
        return
    try:
        data = json.loads(path.read_text())
        console.print(Panel(json.dumps(data, indent=2, ensure_ascii=False),
                            title=str(path), border_style="white"))
    except (OSError, json.JSONDecodeError) as exc:
        console.print(f"[bad]Unable to read JSON: {exc}[/bad]")

def restore_flow(path):
    backups = sorted(path.parent.glob(path.name + ".backup-*"), reverse=True)
    if not backups:
        console.print("[yellow]No backups found.[/yellow]")
        return
    for i, item in enumerate(backups, 1):
        console.print(f"  [white]{i}.[/white] {item.name}")
    choice = Prompt.ask("Select backup", default="1")
    if not choice.isdigit() or not 1 <= int(choice) <= len(backups):
        console.print("[bad]Invalid selection.[/bad]")
        return
    if Confirm.ask("Restore selected backup?", default=True):
        shutil.copy2(backups[int(choice)-1], path)
        console.print("[good]✓ Backup restored. Restart Sober to apply.[/good]")

def clear_flow(path):
    if not path.exists():
        console.print("[yellow]No FFlags file exists.[/yellow]")
        return
    if Confirm.ask("Remove the FFlags file? A backup will be created first.", default=False):
        backup = backup_file(path)
        path.unlink()
        console.print("[good]✓ FFlags file removed.[/good]")
        if backup:
            console.print(f"[muted]Backup: {backup}[/muted]")

def main():
    banner()
    animated_step("Initializing FFlags Injector", "ArkeeDev")
    animated_step("Detecting Linux distribution", distro_name())
    found = find_sober()
    if found:
        animated_step("Detecting Roblox environment", "Sober detected")
    else:
        animated_step("Detecting Roblox environment", "Sober not detected; manual mode available")
    path = choose_config()
    animated_step("Checking configuration path", str(path))
    while True:
        console.print()
        show_menu()
        choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5", "0"], default="1")
        if choice == "1":
            inject_flow(path)
        elif choice == "2":
            view_flow(path)
        elif choice == "3":
            restore_flow(path)
        elif choice == "4":
            clear_flow(path)
        elif choice == "5":
            path = environment_check()
        else:
            console.print("\n[white]Thanks for using FFlags Injector![/white]")
            break
        Prompt.ask("\n[muted]Press Enter to continue[/muted]", default="", show_default=False)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user.[/yellow]")
        raise SystemExit(130)
