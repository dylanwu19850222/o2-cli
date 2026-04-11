"""O2 CLI root - Typer application with global options."""

import asyncio
import typing as t
from typing import Optional

import typer

from o2_cli import __version__, ensure_skill_installed
from o2_cli.self_update import check_for_update, do_self_update

app = typer.Typer(
    name="o2",
    help="O2 DEX Trading Platform CLI",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def version_callback(value: bool):
    if value:
        typer.echo(f"o2-cli version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    config: Optional[str] = typer.Option(None, "--config", help="Config file path"),
    profile: Optional[str] = typer.Option(None, "--profile", help="Config profile"),
    api_url: Optional[str] = typer.Option(None, "--api-url", help="Override API URL"),
    timeout: float = typer.Option(30.0, "--timeout", help="HTTP timeout in seconds"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose logging"),
    version: bool = typer.Option(False, "--version", callback=version_callback, is_eager=True),
):
    """O2 DEX Trading Platform CLI."""
    # Auto-install Claude Code skill on first run
    ensure_skill_installed()
    # Non-blocking version check (skip in --json mode to avoid polluting stdout)
    if not json_output:
        check_for_update()
    # Store global state for commands to access
    app.state = {
        "json_output": json_output,
        "config_path": config,
        "profile": profile,
        "api_url": api_url,
        "timeout": timeout,
        "verbose": verbose,
    }


def get_state() -> dict:
    """Get global CLI state."""
    return getattr(app, "state", {
        "json_output": False,
        "config_path": None,
        "profile": None,
        "api_url": None,
        "timeout": 30.0,
        "verbose": False,
    })


@app.command()
def update():
    """Update o2-cli to the latest version and refresh skills."""
    do_self_update()


# Register command groups
from o2_cli.commands import (  # noqa: E402
    auth,
    balance,
    orders,
    positions,
    markets,
    trades,
    fees,
    deposits,
    withdrawals,
    settings,
    notifications,
    account,
    admin,
    mm,
    setup_cmd,
)

app.add_typer(auth.app, name="auth", help="Authentication")
app.add_typer(balance.app, name="balance", help="Balance queries")
app.add_typer(orders.app, name="orders", help="Order management")
app.add_typer(positions.app, name="positions", help="Position management")
app.add_typer(markets.app, name="markets", help="Market data")
app.add_typer(trades.app, name="trades", help="Trade history")
app.add_typer(fees.app, name="fees", help="Fee information")
app.add_typer(deposits.app, name="deposits", help="Deposit management")
app.add_typer(withdrawals.app, name="withdrawals", help="Withdrawal management")
app.add_typer(settings.app, name="settings", help="User settings")
app.add_typer(notifications.app, name="notifications", help="Notifications")
app.add_typer(account.app, name="account", help="Account overview")
app.add_typer(admin.app, name="admin", help="Admin operations")
app.add_typer(mm.app, name="mm", help="Market maker control")
app.add_typer(setup_cmd.app, name="setup", help="Setup for vibe coding tools")
