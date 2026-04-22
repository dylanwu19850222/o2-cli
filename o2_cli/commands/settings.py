"""o2 settings commands - User settings management."""

import asyncio

import typer

from o2_cli.cli import get_state
from o2_cli.client import O2Client
from o2_cli.config import load_config, get_active_profile
from o2_cli.exceptions import APIError, ConnectionError
from o2_cli.output import OutputFormatter

app = typer.Typer(help="User settings")


@app.command("get")
def get():
    """Show current user settings."""
    asyncio.run(_get())


async def _get():
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
            data = await client.get_user_settings()
            formatter.print_raw(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("leverage")
def leverage(
    market_id: int = typer.Option(..., "--market-id", "-m", help="Market ID"),
    leverage: int = typer.Option(..., "--leverage", "-l", help="Leverage value"),
):
    """Set leverage for a market."""
    asyncio.run(_leverage(market_id, leverage))


async def _leverage(market_id: int, leverage_val: int):
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
            data = await client.set_leverage(market_id, leverage_val)
            formatter.print_raw(data)
            if not state["json_output"]:
                formatter.print_success(
                    f"Leverage set to {leverage_val}x for market {market_id}"
                )
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("margin-mode")
def margin_mode(
    mode: str = typer.Option(
        ..., "--mode", "-m", help="Margin mode (cross/isolated)"
    ),
):
    """Set global margin mode."""
    asyncio.run(_margin_mode(mode))


async def _margin_mode(mode: str):
    state = get_state()
    formatter = OutputFormatter(json_mode=state["json_output"])
    config = load_config()
    profile = get_active_profile(config)
    api_url = state.get("api_url") or profile.api_url
    timeout = state.get("timeout") or profile.timeout

    if not profile.token and profile.auth_type == "jwt":
        formatter.print_error("Not authenticated. Run 'o2 auth test-login' first.")
        raise typer.Exit(1)

    if mode not in ("cross", "isolated"):
        formatter.print_error("Margin mode must be 'cross' or 'isolated'.")
        raise typer.Exit(1)

    async with O2Client(api_url, timeout) as client:
        client.set_jwt(profile.token)
        if profile.api_key_id:
            client.set_api_key(profile.api_key_id, profile.api_secret)
        try:
            data = await client.set_margin_mode(mode)
            formatter.print_raw(data)
            if not state["json_output"]:
                formatter.print_success(f"Margin mode set to {mode}")
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("hedging-mode")
def hedging_mode(
    mode: str = typer.Option(
        ..., "--mode", "-m", help="Hedging mode (one_way/hedge)"
    ),
):
    """Set position mode (one-way or hedge). Requires no active positions."""
    asyncio.run(_hedging_mode(mode))


async def _hedging_mode(mode: str):
    state = get_state()
    formatter = OutputFormatter(json_mode=state["json_output"])
    config = load_config()
    profile = get_active_profile(config)
    api_url = state.get("api_url") or profile.api_url
    timeout = state.get("timeout") or profile.timeout

    if not profile.token and profile.auth_type == "jwt":
        formatter.print_error("Not authenticated. Run 'o2 auth test-login' first.")
        raise typer.Exit(1)

    if mode not in ("one_way", "hedge"):
        formatter.print_error("Hedging mode must be 'one_way' or 'hedge'.")
        raise typer.Exit(1)

    async with O2Client(api_url, timeout) as client:
        client.set_jwt(profile.token)
        if profile.api_key_id:
            client.set_api_key(profile.api_key_id, profile.api_secret)
        try:
            data = await client.set_hedging_mode(mode)
            formatter.print_raw(data)
            label = "单向持仓" if mode == "one_way" else "双向持仓(对冲)"
            if not state["json_output"]:
                formatter.print_success(f"Hedging mode set to {mode} ({label})")
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)
