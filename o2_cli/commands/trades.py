"""o2 trades commands - Trade history."""

import asyncio
from typing import Optional

import typer

from o2_cli.cli import get_state
from o2_cli.client import O2Client
from o2_cli.config import load_config, get_active_profile
from o2_cli.exceptions import APIError, ConnectionError
from o2_cli.output import OutputFormatter

app = typer.Typer(help="Trade history")


@app.command("list")
def list_trades(
    market_id: Optional[int] = typer.Option(
        None, "--market-id", "-m", help="Filter by market ID"
    ),
    limit: int = typer.Option(50, "--limit", "-n", help="Number of records"),
    skip: int = typer.Option(0, "--skip", help="Number of records to skip"),
):
    """List trade history."""
    asyncio.run(_list_trades(market_id, limit, skip))


async def _list_trades(market_id: Optional[int], limit: int, skip: int):
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
            data = await client.get_trades(skip=skip, limit=limit, market_id=market_id)
            formatter.print_raw(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("summary")
def summary():
    """Show trade summary statistics."""
    asyncio.run(_summary())


async def _summary():
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
            data = await client.get_trade_summary()
            formatter.print_raw(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)
