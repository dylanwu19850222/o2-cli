"""o2 withdrawals commands - Withdrawal management."""

import asyncio

import typer

from o2_cli.cli import get_state
from o2_cli.client import O2Client
from o2_cli.config import load_config, get_active_profile
from o2_cli.exceptions import APIError, ConnectionError
from o2_cli.output import OutputFormatter

app = typer.Typer(help="Withdrawal management")


@app.command("create")
def create(
    amount: str = typer.Option(..., "--amount", "-a", help="Withdrawal amount (USDC)"),
    address: str = typer.Option(
        ..., "--address", "-d", help="Destination wallet address"
    ),
    chain: str = typer.Option(
        "ethereum", "--chain", "-c", help="Blockchain network (ethereum/base/arbitrum)"
    ),
    currency: str = typer.Option(
        "USDC", "--currency", help="Currency to withdraw"
    ),
):
    """Create a new withdrawal request."""
    asyncio.run(_create(amount, address, chain, currency))


async def _create(amount: str, address: str, chain: str, currency: str):
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
            data = await client.create_withdrawal(
                amount=amount, address=address, chain=chain, currency=currency
            )
            formatter.print_raw(data)
            if not state["json_output"]:
                formatter.print_success(
                    f"Withdrawal request created: {amount} {currency} to {address[:10]}..."
                )
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("status")
def status(
    id: str = typer.Option(
        ..., "--id", "-i", help="Withdrawal ID to check"
    ),
):
    """Check withdrawal status."""
    asyncio.run(_status(id))


async def _status(withdrawal_id: str):
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
            data = await client.get_withdrawal(withdrawal_id)
            formatter.print_raw(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("cancel")
def cancel(
    id: str = typer.Option(
        ..., "--id", "-i", help="Withdrawal ID to cancel"
    ),
):
    """Cancel a pending withdrawal."""
    asyncio.run(_cancel(id))


async def _cancel(withdrawal_id: str):
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
            data = await client.cancel_withdrawal(withdrawal_id)
            formatter.print_raw(data)
            if not state["json_output"]:
                formatter.print_success(f"Withdrawal {withdrawal_id} cancelled")
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("list")
def list_withdrawals(
    limit: int = typer.Option(20, "--limit", "-n", help="Number of records"),
    offset: int = typer.Option(0, "--offset", help="Offset"),
):
    """List withdrawal history."""
    asyncio.run(_list_withdrawals(limit, offset))


async def _list_withdrawals(limit: int, offset: int):
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
            data = await client.get_withdrawal_history(limit, offset)
            formatter.print_raw(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)
