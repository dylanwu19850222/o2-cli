"""o2 notifications commands - Notification management."""

import asyncio
from typing import Optional

import typer

from o2_cli.cli import get_state
from o2_cli.client import O2Client
from o2_cli.config import load_config, get_active_profile
from o2_cli.exceptions import APIError, ConnectionError
from o2_cli.output import OutputFormatter

app = typer.Typer(help="Notifications")


@app.command("list")
def list_notifications(
    unread_only: bool = typer.Option(
        False, "--unread-only", "-u", help="Show only unread notifications"
    ),
    type: Optional[str] = typer.Option(
        None, "--type", "-t",
        help="Filter by type (trade/deposit/withdrawal/system/security/market)"
    ),
):
    """List notifications."""
    asyncio.run(_list_notifications(unread_only, type))


async def _list_notifications(unread_only: bool, type: Optional[str]):
    state = get_state()
    formatter = OutputFormatter(json_mode=state["json_output"])
    config = load_config()
    profile = get_active_profile(config)
    api_url = state.get("api_url") or profile.api_url
    timeout = state.get("timeout") or profile.timeout

    if not profile.token and profile.auth_type == "jwt":
        formatter.print_error("Not authenticated. Run 'o2 auth test-login' first.")
        raise typer.Exit(1)

    params = {}
    if unread_only:
        params["is_read"] = "false"
    if type:
        params["type"] = type

    async with O2Client(api_url, timeout) as client:
        client.set_jwt(profile.token)
        if profile.api_key_id:
            client.set_api_key(profile.api_key_id, profile.api_secret)
        try:
            data = await client.get_notifications(**params)
            formatter.print_raw(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("unread")
def unread():
    """Show unread notification count."""
    asyncio.run(_unread())


async def _unread():
    state = get_state()
    formatter = OutputFormatter(json_mode=state["json_output"])
    config = load_config()
    profile = get_active_profile(config)
    api_url = state.get("api_url") or profile.api_url
    timeout = state.get("timeout") or profile.timeout

    if not profile.token and profile.auth_type == "jwt":
        formatter.print_error("Not authenticated. Run 'o2 auth test-login' first.")
        raise typer.Exit(1)

    async with O2Client(api_url, timeout) as client:
        client.set_jwt(profile.token)
        if profile.api_key_id:
            client.set_api_key(profile.api_key_id, profile.api_secret)
        try:
            data = await client.get_unread_count()
            formatter.print_raw(data)
            if not state["json_output"]:
                count = data.get("unread_count", data.get("count", 0))
                formatter.print_success(f"{count} unread notifications")
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("read")
def read(
    id: str = typer.Option(
        ..., "--id", "-i", help="Notification ID to mark as read"
    ),
):
    """Mark a notification as read."""
    asyncio.run(_read(id))


async def _read(notification_id: str):
    state = get_state()
    formatter = OutputFormatter(json_mode=state["json_output"])
    config = load_config()
    profile = get_active_profile(config)
    api_url = state.get("api_url") or profile.api_url
    timeout = state.get("timeout") or profile.timeout

    if not profile.token and profile.auth_type == "jwt":
        formatter.print_error("Not authenticated. Run 'o2 auth test-login' first.")
        raise typer.Exit(1)

    async with O2Client(api_url, timeout) as client:
        client.set_jwt(profile.token)
        if profile.api_key_id:
            client.set_api_key(profile.api_key_id, profile.api_secret)
        try:
            data = await client.mark_notification_read(notification_id)
            formatter.print_raw(data)
            if not state["json_output"]:
                formatter.print_success(f"Notification {notification_id} marked as read")
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)
