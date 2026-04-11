"""o2 markets commands - Market data (public, no auth required)."""

import asyncio
from typing import Optional

import typer

from o2_cli.cli import get_state
from o2_cli.client import O2Client
from o2_cli.config import load_config, get_active_profile
from o2_cli.exceptions import APIError, ConnectionError
from o2_cli.output import OutputFormatter

app = typer.Typer(help="Market data")


@app.command("list")
def list_markets():
    """List all available markets."""
    asyncio.run(_list_markets())


async def _list_markets():
    state = get_state()
    formatter = OutputFormatter(json_mode=state["json_output"])
    config = load_config()
    profile = get_active_profile(config)
    api_url = state.get("api_url") or profile.api_url
    timeout = state.get("timeout") or profile.timeout

    async with O2Client(api_url, timeout) as client:
        try:
            data = await client.get_markets()
            formatter.print_markets(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("orderbook")
def orderbook(
    market_id: int = typer.Option(..., "--market-id", "-m", help="Market ID"),
):
    """Show order book for a market."""
    asyncio.run(_orderbook(market_id))


async def _orderbook(market_id: int):
    state = get_state()
    formatter = OutputFormatter(json_mode=state["json_output"])
    config = load_config()
    profile = get_active_profile(config)
    api_url = state.get("api_url") or profile.api_url
    timeout = state.get("timeout") or profile.timeout

    async with O2Client(api_url, timeout) as client:
        try:
            data = await client.get_orderbook(market_id)
            formatter.print_orderbook(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("trades")
def trades(
    market_id: int = typer.Option(..., "--market-id", "-m", help="Market ID"),
    limit: int = typer.Option(50, "--limit", "-n", help="Number of trades"),
):
    """Show recent trades for a market."""
    asyncio.run(_trades(market_id, limit))


async def _trades(market_id: int, limit: int):
    state = get_state()
    formatter = OutputFormatter(json_mode=state["json_output"])
    config = load_config()
    profile = get_active_profile(config)
    api_url = state.get("api_url") or profile.api_url
    timeout = state.get("timeout") or profile.timeout

    async with O2Client(api_url, timeout) as client:
        try:
            data = await client.get_market_trades(market_id, limit)
            formatter.print_raw(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("candles")
def candles(
    market_id: int = typer.Option(..., "--market-id", "-m", help="Market ID"),
    interval: str = typer.Option(
        "1h", "--interval", "-i", help="Candle interval (1m/5m/15m/1h/4h/1d)"
    ),
    limit: int = typer.Option(500, "--limit", "-n", help="Number of candles"),
):
    """Show candlestick data for a market."""
    asyncio.run(_candles(market_id, interval, limit))


async def _candles(market_id: int, interval: str, limit: int):
    state = get_state()
    formatter = OutputFormatter(json_mode=state["json_output"])
    config = load_config()
    profile = get_active_profile(config)
    api_url = state.get("api_url") or profile.api_url
    timeout = state.get("timeout") or profile.timeout

    async with O2Client(api_url, timeout) as client:
        try:
            data = await client.get_candles(market_id, interval, limit)
            formatter.print_raw(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)
