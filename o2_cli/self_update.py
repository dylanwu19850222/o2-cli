"""Self-update: check PyPI for new version, upgrade, and refresh skills."""

import json
import subprocess
import sys

from rich.console import Console

from o2_cli import __version__

console = Console()

PYPI_API = "https://pypi.org/pypi/o2-cli/json"


def get_latest_version() -> str | None:
    """Fetch latest version from PyPI (no auth needed)."""
    import httpx

    try:
        resp = httpx.get(PYPI_API, timeout=10.0)
        resp.raise_for_status()
        return resp.json()["info"]["version"]
    except Exception:
        return None


def check_for_update() -> None:
    """Check if a newer version is available. Print result."""
    latest = get_latest_version()
    if latest is None:
        console.print("[yellow]Could not check for updates.[/yellow]")
        return

    if latest == __version__:
        console.print(f"[green]Already up to date[/green] (v{__version__})")
    else:
        console.print(f"[yellow]Update available:[/yellow] v{__version__} → v{latest}")
        console.print(f"  Run [bold]o2 update[/bold] to upgrade")


def do_self_update() -> None:
    """Full update: pip upgrade → skill refresh → version check."""
    console.print(f"[bold]O2 CLI Self-Update[/bold] (current: v{__version__})\n")

    # Step 1: pip install --upgrade
    console.print("1. Upgrading package...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "o2-cli"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            # Parse new version from pip output
            for line in result.stdout.splitlines():
                if "Successfully installed o2-cli" in line:
                    console.print(f"   [green]Upgraded:[/green] {line.strip()}")
                    break
                elif "Requirement already satisfied: o2-cli" in line:
                    console.print("   Already on latest version")
                    break
            else:
                console.print("   [green]Done[/green]")
        else:
            console.print(f"   [red]pip error:[/red] {result.stderr.strip()}")
            console.print("   You may need: pip install --upgrade o2-cli")
    except subprocess.TimeoutExpired:
        console.print("   [red]Timeout[/red] - pip install took too long")
        return

    # Step 2: refresh skill files
    console.print("\n2. Refreshing skill files...")
    try:
        result = subprocess.run(
            ["o2", "setup", "--update"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "updated" in line.lower() or "✓" in line:
                    console.print(f"   {line}")
        else:
            console.print("   [yellow]No tools configured yet.[/yellow] Run [bold]o2 setup[/bold]")
    except Exception:
        console.print("   [yellow]Skill refresh skipped[/yellow]")

    # Step 3: check API diff
    console.print("\n3. Checking API changes...")
    try:
        result = subprocess.run(
            ["o2", "admin", "api-diff"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.strip():
                    console.print(f"   {line}")
    except Exception:
        console.print("   [yellow]API diff check skipped (backend may be offline)[/yellow]")

    # Done
    console.print("\n[bold green]Update complete![/bold green]")
