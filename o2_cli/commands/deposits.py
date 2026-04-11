"""o2 deposits commands - Deposit management."""

import asyncio

import typer

from o2_cli.cli import get_state
from o2_cli.client import O2Client
from o2_cli.config import load_config, get_active_profile
from o2_cli.exceptions import APIError, ConnectionError
from o2_cli.output import OutputFormatter

app = typer.Typer(help="Deposit management")


@app.command("address")
def address(
    chain: str = typer.Option(
        "base", "--chain", "-c", help="Blockchain network (base/arbitrum/ethereum)"
    ),
):
    """Get or activate your deposit address."""
    asyncio.run(_address(chain))


async def _address(chain: str):
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
            data = await client.get_deposit_address(chain)
            formatter.print_raw(data)
            if not state["json_output"]:
                deposit_addr = data.get("deposit_address", "")
                if deposit_addr:
                    formatter.print_success(f"Deposit address: {deposit_addr}")
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("history")
def history(
    limit: int = typer.Option(50, "--limit", "-n", help="Number of records"),
):
    """Show deposit history."""
    asyncio.run(_history(limit))


async def _history(limit: int):
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
            data = await client.get_deposit_history(limit)
            formatter.print_raw(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)
