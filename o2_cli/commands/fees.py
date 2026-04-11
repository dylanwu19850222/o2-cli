"""o2 fees commands - Fee information."""

import asyncio

import typer

from o2_cli.cli import get_state
from o2_cli.client import O2Client
from o2_cli.config import load_config, get_active_profile
from o2_cli.exceptions import APIError, ConnectionError
from o2_cli.output import OutputFormatter

app = typer.Typer(help="Fee information")


@app.command("rates")
def rates():
    """Show current fee rates (public, no auth required)."""
    asyncio.run(_rates())


async def _rates():
    state = get_state()
    formatter = OutputFormatter(json_mode=state["json_output"])
    config = load_config()
    profile = get_active_profile(config)
    api_url = state.get("api_url") or profile.api_url
    timeout = state.get("timeout") or profile.timeout

    async with O2Client(api_url, timeout) as client:
        try:
            data = await client.get_fee_rates()
            formatter.print_raw(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("estimate")
def estimate(
    amount: str = typer.Option(..., "--amount", "-a", help="Order amount (base units)"),
    price: str = typer.Option(..., "--price", "-p", help="Order price"),
    is_maker: bool = typer.Option(
        False, "--is-maker", help="Calculate as maker order"
    ),
):
    """Estimate fee for a hypothetical order."""
    asyncio.run(_estimate(amount, price, is_maker))


async def _estimate(amount: str, price: str, is_maker: bool):
    state = get_state()
    formatter = OutputFormatter(json_mode=state["json_output"])
    config = load_config()
    profile = get_active_profile(config)
    api_url = state.get("api_url") or profile.api_url
    timeout = state.get("timeout") or profile.timeout

    async with O2Client(api_url, timeout) as client:
        try:
            data = await client.estimate_fee(
                base_amount=amount, price=price, is_maker=is_maker
            )
            formatter.print_raw(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)
