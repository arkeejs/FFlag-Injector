#!/usr/bin/env python3
"""FFlags Injector — Linux Roblox Fast Flags manager by ArkeeDev."""
from __future__ import annotations

import argparse
import difflib
import json
import os
import platform
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from rich import box
    from rich.align import Align
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    from rich.text import Text
    from rich.theme import Theme
except ImportError:
    print("Missing dependency: rich. Run the installer again.")
    raise SystemExit(1)

APP = "FFlags Injector"
VERSION = "2.1.0"
GITHUB = "https://github.com/arkeejs/FFlag-Injector"
SOBER_ID = "org.vinegarhq.Sober"
HOME = Path.home()
SOBER_CONFIG = HOME / ".var/app" / SOBER_ID / "config/sober/config.json"
DATA_DIR = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config")) / "fflags-injector"
PROFILE_DIR = DATA_DIR / "profiles"
LOG_FILE = DATA_DIR / "activity.log"
console = Console(theme=Theme({
    "good": "bold green", "bad": "bold red", "muted": "bright_black",
    "warn": "bold yellow", "accent": "bold cyan",
}))


@dataclass
class Target:
    name: str
    path: Path
    kind: str
    detail: str


def clear_screen() -> None:
    if console.is_terminal:
        os.system("cls" if os.name == "nt" else "clear")


def banner() -> None:
    clear_screen()
    console.print()
    console.print(Align.center(Text(APP, style="bold white")))
    console.print(Align.center(Text(f"v{VERSION}  •  By ArkeeDev", style="bright_black")))
    console.print(Align.center(Text("★  Star the project on GitHub", style="white")))
    console.print(Align.center(Text("Linux • Sober • Wine", style="bright_black")))
    console.print()


def pause() -> None:
    Prompt.ask("\n[muted]Press Enter to continue[/muted]", default="", show_default=False)


def log_event(message: str) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat(timespec='seconds')}  {message}\n")
    except OSError:
        pass


def distro_name() -> str:
    try:
        for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
            if line.startswith("PRETTY_NAME="):
                return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return platform.system()


def command_exists(command: list[str]) -> bool:
    try:
        return subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              timeout=5, check=False).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def detect_targets() -> list[Target]:
    found: list[Target] = []
    if command_exists(["flatpak", "info", SOBER_ID]) or SOBER_CONFIG.parent.exists():
        found.append(Target("Sober", SOBER_CONFIG, "sober", "Flatpak · config.json → fflags"))

    prefixes = [HOME / ".wine"]
    wine_root = HOME / ".local/share/wineprefixes"
    if wine_root.exists():
        prefixes.extend(p for p in wine_root.iterdir() if p.is_dir())
    seen: set[str] = set()
    pattern = "drive_c/users/*/AppData/Local/Roblox/Versions/*/ClientSettings/ClientAppSettings.json"
    for prefix in prefixes:
        try:
            for path in prefix.glob(pattern):
                key = str(path.resolve())
                if key not in seen:
                    seen.add(key)
                    found.append(Target("Roblox (Wine)", path, "plain", f"Wine prefix · {prefix}"))
        except OSError:
            continue
    return found


def choose_target(targets: list[Target]) -> Target:
    if targets:
        console.print("\n[bold]Detected Roblox environments[/bold]")
        for i, target in enumerate(targets, 1):
            state = "[green]found[/green]" if target.path.exists() else "[yellow]will be created[/yellow]"
            console.print(f"  [white]{i}.[/white] {target.name} · {target.detail} · {state}")
        console.print("  [white]M.[/white] Choose a path manually")
        choice = Prompt.ask("Target", default="1").strip().lower()
        if choice != "m":
            if choice.isdigit() and 1 <= int(choice) <= len(targets):
                return targets[int(choice) - 1]
            console.print("[warn]Invalid choice; using first detected target.[/warn]")
            return targets[0]

    console.print("\n[warn]No supported client detected. Select a target manually.[/warn]")
    kind = Prompt.ask("1) Sober config  2) ClientAppSettings  3) Custom JSON",
                      choices=["1", "2", "3"], default="1")
    if kind == "1":
        return Target("Sober (manual)", SOBER_CONFIG, "sober", "config.json → fflags")
    if kind == "2":
        path = Path(Prompt.ask("Full ClientAppSettings.json path").strip()).expanduser()
        return Target("Roblox ClientSettings", path, "plain", "Plain JSON")
    path = Path(Prompt.ask("Full JSON file path").strip()).expanduser()
    return Target("Custom JSON", path, "plain", "Custom JSON")


def strip_jsonc_comments(source: str) -> str:
    """Remove JSONC comments without touching comment-like text inside strings."""
    out: list[str] = []
    i, in_string, escaped = 0, False, False
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if in_string:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
        elif ch == '"':
            in_string = True
            out.append(ch)
            i += 1
        elif ch == "/" and nxt == "/":
            i += 2
            while i < len(source) and source[i] not in "\r\n":
                i += 1
        elif ch == "/" and nxt == "*":
            i += 2
            while i < len(source) and source[i:i + 2] != "*/":
                out.append("\n" if source[i] == "\n" else " ")
                i += 1
            i += 2 if i < len(source) else 0
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def remove_trailing_commas(source: str) -> str:
    out: list[str] = []
    i, in_string, escaped = 0, False, False
    while i < len(source):
        ch = source[i]
        if in_string:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
        elif ch == '"':
            in_string = True
            out.append(ch)
            i += 1
        elif ch == ",":
            j = i + 1
            while j < len(source) and source[j].isspace():
                j += 1
            if j < len(source) and source[j] in "}]":
                i += 1
            else:
                out.append(ch)
                i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def split_sober_preamble(raw: str) -> tuple[str, str]:
    lines = raw.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.lstrip().startswith("{"):
            return "".join(lines[:i]), "".join(lines[i:])
    return "", raw


def parse_document(target: Target) -> tuple[dict[str, Any], str]:
    if not target.path.exists():
        return {}, ""
    try:
        raw = target.path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Cannot read {target.path}: {exc}") from exc
    preamble, body = ("", raw)
    if target.kind == "sober":
        preamble, body = split_sober_preamble(raw)
    cleaned = remove_trailing_commas(strip_jsonc_comments(body))
    try:
        document = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Malformed configuration near line {exc.lineno}, column {exc.colno}: {exc.msg}. "
            "No changes were made."
        ) from exc
    if not isinstance(document, dict):
        raise ValueError("The configuration root must be a JSON object.")
    return document, preamble


def get_flags(target: Target, document: dict[str, Any]) -> dict[str, Any]:
    if target.kind == "sober":
        flags = document.get("fflags", {})
        if not isinstance(flags, dict):
            raise ValueError('Sober config has an invalid "fflags" value; expected an object.')
        return flags
    return document


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            shutil.copystat(path, temp_name)
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def make_backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = path.with_name(f"{path.name}.backup-{stamp}")
    shutil.copy2(path, backup)
    return backup


def write_document(target: Target, document: dict[str, Any], preamble: str) -> Path | None:
    backup = make_backup(target.path)
    serialized = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    atomic_write(target.path, (preamble if target.kind == "sober" else "") + serialized)
    return backup


def preview_changes(target: Target, incoming: dict[str, Any]) -> tuple[dict[str, Any], str]:
    document, _ = parse_document(target)
    before = json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True).splitlines()
    if target.kind == "sober":
        existing = document.get("fflags", {})
        if not isinstance(existing, dict):
            raise ValueError('Sober config has an invalid "fflags" value.')
        document["fflags"] = {**existing, **incoming}
    else:
        document.update(incoming)
    after = json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True).splitlines()
    diff = "\n".join(difflib.unified_diff(before, after, fromfile="current", tofile="proposed", lineterm=""))
    return document, diff or "No changes."


def read_multiline_json() -> dict[str, Any]:
    console.print(Panel("Paste a JSON object. Finish with a line containing only a dot (.).",
                        title="FFlags input", border_style="cyan"))
    lines: list[str] = []
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
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc.msg} (line {exc.lineno}, column {exc.colno}).") from exc
    if not isinstance(data, dict) or not all(isinstance(k, str) for k in data):
        raise ValueError("FFlags must be a JSON object with string keys.")
    return data


def inject_flow(target: Target) -> None:
    try:
        incoming = read_multiline_json()
        document, diff = preview_changes(target, incoming)
        console.print(Panel(diff, title="Change preview", border_style="cyan"))
        if not Confirm.ask(f"Apply {len(incoming)} supplied FFlag(s)?", default=True):
            return
        _, preamble = parse_document(target)
        backup = write_document(target, document, preamble)
        log_event(f"INJECT target={target.path} supplied={len(incoming)}")
        console.print("[good]✓ Configuration updated.[/good]")
        if backup:
            console.print(f"[muted]Backup: {backup}[/muted]")
        console.print("[warn]Restart Roblox/Sober. Unsupported flags may be ignored.[/warn]")
    except (ValueError, OSError) as exc:
        console.print(f"[bad]✗ {exc}[/bad]")


def view_flow(target: Target) -> None:
    try:
        flags = get_flags(target, parse_document(target)[0])
        table = Table(title=f"{target.name} · {len(flags)} FFlag(s)", box=box.ROUNDED)
        table.add_column("Flag", style="cyan", overflow="fold")
        table.add_column("Value", overflow="fold")
        for key, value in sorted(flags.items()):
            table.add_row(key, json.dumps(value, ensure_ascii=False))
        console.print(table)
        if not flags:
            console.print("[muted]No FFlags configured.[/muted]")
    except (ValueError, OSError) as exc:
        console.print(f"[bad]✗ {exc}[/bad]")


def validate_flow(target: Target) -> None:
    try:
        flags = get_flags(target, parse_document(target)[0])
        console.print(f"[good]✓ Configuration is valid · {len(flags)} FFlag(s).[/good]")
        log_event(f"VALIDATE target={target.path} flags={len(flags)}")
    except (ValueError, OSError) as exc:
        console.print(f"[bad]✗ {exc}[/bad]")


def import_flow(target: Target) -> None:
    path = Path(Prompt.ask("Path to JSON file").strip()).expanduser()
    try:
        incoming = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(incoming, dict):
            raise ValueError("Import file must contain a JSON object.")
        document, diff = preview_changes(target, incoming)
        console.print(Panel(diff, title=f"Import preview · {path.name}", border_style="cyan"))
        if Confirm.ask("Apply imported flags?", default=False):
            _, preamble = parse_document(target)
            backup = write_document(target, document, preamble)
            log_event(f"IMPORT target={target.path} source={path} flags={len(incoming)}")
            console.print("[good]✓ Import completed.[/good]")
            if backup:
                console.print(f"[muted]Backup: {backup}[/muted]")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        console.print(f"[bad]✗ Import failed: {exc}[/bad]")


def export_flow(target: Target) -> None:
    try:
        flags = get_flags(target, parse_document(target)[0])
        if not flags:
            console.print("[warn]No FFlags to export.[/warn]")
            return
        path = Path(Prompt.ask("Export file", default=str(HOME / "fflags-export.json"))).expanduser()
        atomic_write(path, json.dumps(flags, indent=2, ensure_ascii=False) + "\n")
        log_event(f"EXPORT target={target.path} output={path} flags={len(flags)}")
        console.print(f"[good]✓ Exported {len(flags)} flag(s) to {path}.[/good]")
    except (OSError, ValueError) as exc:
        console.print(f"[bad]✗ Export failed: {exc}[/bad]")


def backup_files(target: Target) -> list[Path]:
    return sorted(target.path.parent.glob(target.path.name + ".backup-*"), reverse=True)


def restore_flow(target: Target) -> None:
    backups = backup_files(target)
    if not backups:
        console.print("[warn]No backups found for this target.[/warn]")
        return
    for i, path in enumerate(backups, 1):
        console.print(f"  [cyan]{i}.[/cyan] {path.name}")
    choice = Prompt.ask("Backup number", default="1")
    if not choice.isdigit() or not 1 <= int(choice) <= len(backups):
        console.print("[warn]Invalid selection.[/warn]")
        return
    selected = backups[int(choice) - 1]
    try:
        raw = selected.read_text(encoding="utf-8")
        body = split_sober_preamble(raw)[1] if target.kind == "sober" else raw
        json.loads(remove_trailing_commas(strip_jsonc_comments(body)))
        if Confirm.ask(f"Restore {selected.name}?", default=False):
            shutil.copy2(selected, target.path)
            log_event(f"RESTORE target={target.path} backup={selected}")
            console.print("[good]✓ Backup restored.[/good]")
    except (OSError, json.JSONDecodeError) as exc:
        console.print(f"[bad]Backup could not be validated/restored: {exc}[/bad]")


def clear_flow(target: Target) -> None:
    try:
        document, preamble = parse_document(target)
        flags = get_flags(target, document)
        if not flags:
            console.print("[warn]No FFlags are configured.[/warn]")
            return
        if not Confirm.ask(f"Remove {len(flags)} FFlag(s)? A backup will be created.", default=False):
            return
        if target.kind == "sober":
            document["fflags"] = {}
        else:
            document = {}
        backup = write_document(target, document, preamble)
        log_event(f"CLEAR target={target.path} removed={len(flags)}")
        console.print("[good]✓ FFlags cleared. Other Sober settings were preserved.[/good]")
        if backup:
            console.print(f"[muted]Backup: {backup}[/muted]")
    except (ValueError, OSError) as exc:
        console.print(f"[bad]✗ {exc}[/bad]")


def save_profile() -> None:
    try:
        data = read_multiline_json()
        name = Prompt.ask("Profile name").strip()
        if not name or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 _.-" for ch in name) or len(name) > 48:
            raise ValueError("Use 1–48 letters, numbers, spaces, dots, dashes or underscores.")
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        path = PROFILE_DIR / (name.replace(" ", "_") + ".json")
        if path.exists() and not Confirm.ask("Profile exists. Overwrite?", default=False):
            return
        atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        console.print(f"[good]✓ Profile saved: {path.name}[/good]")
    except (ValueError, OSError) as exc:
        console.print(f"[bad]✗ {exc}[/bad]")


def load_profile(target: Target) -> None:
    profiles = sorted(PROFILE_DIR.glob("*.json")) if PROFILE_DIR.exists() else []
    if not profiles:
        console.print("[warn]No saved profiles yet.[/warn]")
        return
    for i, path in enumerate(profiles, 1):
        console.print(f"  [cyan]{i}.[/cyan] {path.stem}")
    choice = Prompt.ask("Profile number", default="1")
    if not choice.isdigit() or not 1 <= int(choice) <= len(profiles):
        console.print("[warn]Invalid selection.[/warn]")
        return
    try:
        data = json.loads(profiles[int(choice) - 1].read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Profile is not a JSON object.")
        document, diff = preview_changes(target, data)
        console.print(Panel(diff, title="Profile preview", border_style="cyan"))
        if Confirm.ask("Apply this profile?", default=False):
            _, preamble = parse_document(target)
            backup = write_document(target, document, preamble)
            log_event(f"PROFILE target={target.path} profile={profiles[int(choice)-1].name}")
            console.print("[good]✓ Profile applied.[/good]")
            if backup:
                console.print(f"[muted]Backup: {backup}[/muted]")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        console.print(f"[bad]✗ {exc}[/bad]")


def diagnostics(target: Target) -> None:
    table = Table(title="System diagnostics", box=box.ROUNDED)
    table.add_column("Check", style="cyan")
    table.add_column("Result")
    table.add_row("Operating system", distro_name())
    table.add_row("Python", platform.python_version())
    table.add_row("Target", target.name)
    table.add_row("Configuration path", str(target.path))
    table.add_row("File exists", "Yes" if target.path.exists() else "No (will be created)")
    table.add_row("Flatpak", "Available" if shutil.which("flatpak") else "Not installed")
    table.add_row("Git", "Available" if shutil.which("git") else "Not installed")
    try:
        table.add_row("Configuration status", f"Valid · {len(get_flags(target, parse_document(target)[0]))} flags")
    except ValueError as exc:
        table.add_row("Configuration status", f"[red]Invalid · {exc}[/red]")
    console.print(table)
    console.print(f"[muted]Activity log: {LOG_FILE}[/muted]")


def show_menu() -> None:
    console.print(Panel(
        "[bold white]1[/bold white]  Inject / paste FFlags\n"
        "[bold white]2[/bold white]  View current FFlags\n"
        "[bold white]3[/bold white]  Import FFlags from file\n"
        "[bold white]4[/bold white]  Export current FFlags\n"
        "[bold white]5[/bold white]  Validate configuration\n"
        "[bold white]6[/bold white]  Save FFlags profile\n"
        "[bold white]7[/bold white]  Apply saved profile\n"
        "[bold white]8[/bold white]  Restore backup\n"
        "[bold white]9[/bold white]  Clear FFlags safely\n"
        "[bold white]D[/bold white]  System diagnostics\n"
        "[bold white]R[/bold white]  Re-detect client\n"
        "[bold white]0[/bold white]  Exit",
        title="Main Menu", border_style="cyan", box=box.ROUNDED))


def run_check(target: Target) -> int:
    try:
        flags = get_flags(target, parse_document(target)[0])
        console.print(f"[good]OK[/good] {target.path} · {len(flags)} flags")
        return 0
    except (ValueError, OSError) as exc:
        console.print(f"[bad]ERROR[/bad] {exc}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely manage Roblox FastFlags on Linux.")
    parser.add_argument("--version", action="version", version=f"{APP} {VERSION}")
    parser.add_argument("--check", action="store_true", help="detect and validate the selected configuration")
    args = parser.parse_args()

    banner()
    with Progress(SpinnerColumn(), TextColumn("[white]{task.description}"), console=console,
                  transient=True) as progress:
        task = progress.add_task("Detecting Linux and Roblox environments...", total=None)
        time.sleep(0.25)
        progress.stop_task(task)
    target = choose_target(detect_targets())
    console.print(f"[muted]System: {distro_name()} · Python {platform.python_version()}[/muted]")
    console.print(f"[muted]Selected: {target.path}[/muted]")
    if args.check:
        return run_check(target)

    while True:
        clear_screen()
        banner()
        console.print(f"[muted]System: {distro_name()} · Python {platform.python_version()}[/muted]")
        console.print(f"[muted]Selected: {target.path}[/muted]\n")
        show_menu()
        choice = Prompt.ask("Select", default="1").strip().lower()
        actions = {
            "1": lambda: inject_flow(target),
            "2": lambda: view_flow(target),
            "3": lambda: import_flow(target),
            "4": lambda: export_flow(target),
            "5": lambda: validate_flow(target),
            "6": save_profile,
            "7": lambda: load_profile(target),
            "8": lambda: restore_flow(target),
            "9": lambda: clear_flow(target),
            "d": lambda: diagnostics(target),
        }
        if choice == "0":
            console.print("\n[white]Thanks for using FFlags Injector![/white]")
            return 0
        if choice == "r":
            target = choose_target(detect_targets())
            continue
        action = actions.get(choice)
        if action:
            action()
        else:
            console.print("[warn]Unknown option.[/warn]")
        pause()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        console.print("\n[warn]Cancelled.[/warn]")
        raise SystemExit(130)
