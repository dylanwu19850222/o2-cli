"""o2 balance commands - Balance queries."""

import asyncio

import typer

from o2_cli.client import O2Client
from o2_cli.exceptions import APIError, ConnectionError
from o2_cli.commands._helpers import resolve_context, setup_client, require_auth

app = typer.Typer(help="Balance queries")


@app.command("show")
def show():
    """Show account balance (cash + bonus)."""
    asyncio.run(_show())


async def _show():
    profile, formatter, api_url, timeout = resolve_context()

    if not require_auth(profile, formatter):
        raise typer.Exit(1)

    async with O2Client(api_url, timeout) as client:
        setup_client(client, profile)
        try:
            data = await client.get_balance()
            formatter.print_balance(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("history")
def history(
    limit: int = typer.Option(50, "--limit", "-n", help="Number of records"),
    offset: int = typer.Option(0, "--offset", help="Offset"),
):
    """Show balance change history."""
    asyncio.run(_history(limit, offset))


async def _history(limit: int, offset: int):
    profile, formatter, api_url, timeout = resolve_context()

    if not require_auth(profile, formatter):
        raise typer.Exit(1)

    async with O2Client(api_url, timeout) as client:
        setup_client(client, profile)
        try:
            data = await client.get_balance_history(limit, offset)
            formatter.print_raw(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)
