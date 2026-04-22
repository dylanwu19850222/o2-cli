"""o2 orders commands - Order management."""

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer

from o2_cli.cli import get_state
from o2_cli.client import O2Client
from o2_cli.config import load_config, get_active_profile
from o2_cli.exceptions import APIError, ConnectionError
from o2_cli.output import OutputFormatter

app = typer.Typer(help="Order management")


@app.command("create")
def create(
    market_id: int = typer.Option(..., "--market-id", "-m", help="Market ID"),
    side: str = typer.Option(..., "--side", "-s", help="Order side (long/short)"),
    order_type: str = typer.Option(
        "limit", "--order-type", "-t", help="Order type (market/limit)"
    ),
    base_amount: str = typer.Option(
        ..., "--base-amount", "-a", help="Order size in base units"
    ),
    price: Optional[str] = typer.Option(
        None, "--price", "-p", help="Limit price (required for limit orders)"
    ),
    position_mode: str = typer.Option(
        "open", "--position-mode", help="Position mode (open/close)"
    ),
    # leverage 已移除：使用 'o2 settings leverage' 设置
    margin_mode: str = typer.Option(
        "cross", "--margin-mode", help="Margin mode (cross/isolated)"
    ),
    reduce_only: bool = typer.Option(
        False, "--reduce-only", help="Reduce-only order"
    ),
):
    """Create a new order. Leverage is managed via 'o2 settings leverage'."""
    asyncio.run(
        _create(
            market_id, side, order_type, base_amount, price, position_mode,
            margin_mode, reduce_only,
        )
    )


async def _create(
    market_id: int,
    side: str,
    order_type: str,
    base_amount: str,
    price: Optional[str],
    position_mode: str,
    margin_mode: str,
    reduce_only: bool,
):
    state = get_state()
    formatter = OutputFormatter(json_mode=state["json_output"])
    config = load_config()
    profile = get_active_profile(config)
    api_url = state.get("api_url") or profile.api_url
    timeout = state.get("timeout") or profile.timeout

    if not profile.token and profile.auth_type == "jwt":
        formatter.print_error("Not authenticated. Run 'o2 auth test-login' first.")
        raise typer.Exit(1)

    if order_type == "limit" and not price:
        formatter.print_error("Limit orders require --price.")
        raise typer.Exit(1)

    payload = {
        "market_id": market_id,
        "side": side,
        "order_type": order_type,
        "base_amount": base_amount,
        "position_mode": position_mode,
        "margin_mode": margin_mode,
        "reduce_only": reduce_only,
    }
    if price is not None:
        payload["price"] = price

    async with O2Client(api_url, timeout) as client:
        client.set_jwt(profile.token)
        if profile.api_key_id:
            client.set_api_key(profile.api_key_id, profile.api_secret)
        try:
            data = await client.create_order(**payload)
            formatter.print_orders(data)
            if not state["json_output"]:
                formatter.print_success("Order created")
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("list")
def list_orders(
    market_id: Optional[int] = typer.Option(
        None, "--market-id", "-m", help="Filter by market ID"
    ),
    status: Optional[str] = typer.Option(
        None, "--status", "-s", help="Filter by status"
    ),
):
    """List orders."""
    asyncio.run(_list_orders(market_id, status))


async def _list_orders(market_id: Optional[int], status: Optional[str]):
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
            data = await client.list_orders(market_id=market_id, status_filter=status)
            formatter.print_orders(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("cancel")
def cancel(
    order_id: str = typer.Option(..., "--order-id", "-i", help="Order ID to cancel"),
):
    """Cancel an order."""
    asyncio.run(_cancel(order_id))


async def _cancel(order_id: str):
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
            data = await client.cancel_order(order_id)
            formatter.print_raw(data)
            if not state["json_output"]:
                formatter.print_success(f"Order {order_id} cancelled")
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("cancel-all")
def cancel_all(
    market_id: Optional[int] = typer.Option(
        None, "--market-id", "-m", help="Cancel orders for a specific market"
    ),
):
    """Cancel all open orders."""
    asyncio.run(_cancel_all(market_id))


async def _cancel_all(market_id: Optional[int]):
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
            data = await client.cancel_all_orders(market_id=market_id)
            formatter.print_raw(data)
            if not state["json_output"]:
                label = f" for market {market_id}" if market_id else ""
                formatter.print_success(f"All orders cancelled{label}")
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("modify")
def modify(
    order_id: str = typer.Option(..., "--order-id", "-i", help="Order ID to modify"),
    base_amount: Optional[str] = typer.Option(
        None, "--base-amount", "-a", help="New order size"
    ),
    price: Optional[str] = typer.Option(None, "--price", "-p", help="New price"),
):
    """Modify an existing order."""
    asyncio.run(_modify(order_id, base_amount, price))


async def _modify(
    order_id: str, base_amount: Optional[str], price: Optional[str]
):
    state = get_state()
    formatter = OutputFormatter(json_mode=state["json_output"])
    config = load_config()
    profile = get_active_profile(config)
    api_url = state.get("api_url") or profile.api_url
    timeout = state.get("timeout") or profile.timeout

    if not profile.token and profile.auth_type == "jwt":
        formatter.print_error("Not authenticated. Run 'o2 auth test-login' first.")
        raise typer.Exit(1)

    if base_amount is None and price is None:
        formatter.print_error("Provide at least --base-amount or --price to modify.")
        raise typer.Exit(1)

    kwargs = {}
    if base_amount is not None:
        kwargs["base_amount"] = base_amount
    if price is not None:
        kwargs["price"] = price

    async with O2Client(api_url, timeout) as client:
        client.set_jwt(profile.token)
        if profile.api_key_id:
            client.set_api_key(profile.api_key_id, profile.api_secret)
        try:
            data = await client.modify_order(order_id, **kwargs)
            formatter.print_raw(data)
            if not state["json_output"]:
                formatter.print_success(f"Order {order_id} modified")
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("batch")
def batch(
    file: Path = typer.Option(
        ..., "--file", "-f", help="Path to JSON file with batch operations"
    ),
):
    """Submit batch order operations from a JSON file."""
    asyncio.run(_batch(file))


async def _batch(file: Path):
    state = get_state()
    formatter = OutputFormatter(json_mode=state["json_output"])
    config = load_config()
    profile = get_active_profile(config)
    api_url = state.get("api_url") or profile.api_url
    timeout = state.get("timeout") or profile.timeout

    if not profile.token and profile.auth_type == "jwt":
        formatter.print_error("Not authenticated. Run 'o2 auth test-login' first.")
        raise typer.Exit(1)

    if not file.exists():
        formatter.print_error(f"File not found: {file}")
        raise typer.Exit(1)

    try:
        with open(file) as f:
            payload = json.load(f)
    except json.JSONDecodeError as e:
        formatter.print_error(f"Invalid JSON in {file}: {e}")
        raise typer.Exit(1)

    operations = payload if isinstance(payload, list) else payload.get("operations", [])
    if not operations:
        formatter.print_error("No operations found in file.")
        raise typer.Exit(1)

    async with O2Client(api_url, timeout) as client:
        client.set_jwt(profile.token)
        if profile.api_key_id:
            client.set_api_key(profile.api_key_id, profile.api_secret)
        try:
            data = await client.batch_orders(operations)
            formatter.print_raw(data)
            if not state["json_output"]:
                formatter.print_success(f"Batch submitted ({len(operations)} operations)")
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)
