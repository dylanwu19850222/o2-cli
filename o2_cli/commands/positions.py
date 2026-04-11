"""o2 positions commands - Position management."""

import asyncio
from typing import Optional

import typer

from o2_cli.cli import get_state
from o2_cli.client import O2Client
from o2_cli.config import load_config, get_active_profile
from o2_cli.exceptions import APIError, ConnectionError
from o2_cli.output import OutputFormatter

app = typer.Typer(help="Position management")


@app.command("list")
def list_positions():
    """List all open positions."""
    asyncio.run(_list_positions())


async def _list_positions():
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
            data = await client.get_positions()
            formatter.print_positions(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("market")
def market(
    market_id: int = typer.Option(..., "--market-id", "-m", help="Market ID"),
):
    """Show position for a specific market."""
    asyncio.run(_market(market_id))


async def _market(market_id: int):
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
            data = await client.get_position_by_market(market_id)
            formatter.print_positions(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("close")
def close(
    position_id: str = typer.Option(
        ..., "--position-id", "-i", help="Position ID to close"
    ),
):
    """Close an open position."""
    asyncio.run(_close(position_id))


async def _close(position_id: str):
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
            data = await client.close_position(position_id)
            formatter.print_raw(data)
            if not state["json_output"]:
                formatter.print_success(f"Position {position_id} closed")
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("risk")
def risk(
    market_id: int = typer.Option(
        ..., "--market-id", "-m", help="Market ID to check liquidation risk"
    ),
):
    """Check liquidation risk for a market position."""
    asyncio.run(_risk(market_id))


async def _risk(market_id: int):
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
            data = await client.get_liquidation_risk(market_id)
            formatter.print_raw(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)
