"""o2 auth commands - Authentication management."""

import asyncio

import typer

from o2_cli.client import O2Client
from o2_cli.config import save_token
from o2_cli.exceptions import APIError, ConnectionError
from o2_cli.commands._helpers import resolve_context, setup_client

app = typer.Typer(help="Authentication commands")


@app.command("test-login")
def test_login():
    """Dev: get a test JWT token."""
    asyncio.run(_test_login())


async def _test_login():
    profile, formatter, api_url, timeout = resolve_context()

    async with O2Client(api_url, timeout) as client:
        try:
            data = await client.auth_test_login()
            token = data.get("token") or data.get("access_token")
            if token:
                save_token(profile.auth_type if profile.auth_type == "jwt" else "default", token)
                # Save to active profile
                from o2_cli.config import load_config, get_active_profile, CONFIG_FILE
                config = load_config(CONFIG_FILE)
                save_token(config.active_profile, token)
                formatter.print_success("Logged in (token saved to config)")
            formatter.print_raw(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("challenge")
def challenge(
    wallet: str = typer.Option(..., "--wallet", "-w", help="Wallet address"),
):
    """Get a login challenge nonce for wallet signing."""
    asyncio.run(_challenge(wallet))


async def _challenge(wallet: str):
    profile, formatter, api_url, timeout = resolve_context()

    async with O2Client(api_url, timeout) as client:
        try:
            data = await client.auth_challenge(wallet)
            formatter.print_raw(data)
            formatter.print_success("Sign this message with your wallet to login")
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("login")
def login(
    wallet: str = typer.Option(..., "--wallet", "-w", help="Wallet address"),
    signature: str = typer.Option(..., "--signature", "-s", help="Wallet signature"),
    message: str = typer.Option(..., "--message", "-m", help="Signed message"),
):
    """Login with wallet signature."""
    asyncio.run(_login(wallet, signature, message))


async def _login(wallet: str, signature: str, message: str):
    profile, formatter, api_url, timeout = resolve_context()

    async with O2Client(api_url, timeout) as client:
        try:
            data = await client.auth_signature_login(wallet, signature, message)
            token = data.get("token") or data.get("access_token")
            if token:
                from o2_cli.config import load_config, CONFIG_FILE
                config = load_config(CONFIG_FILE)
                save_token(config.active_profile, token)
                formatter.print_success(f"Logged in as {wallet[:8]}...")
            formatter.print_raw(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("me")
def me():
    """Show current user info."""
    asyncio.run(_me())


async def _me():
    profile, formatter, api_url, timeout = resolve_context()

    async with O2Client(api_url, timeout) as client:
        setup_client(client, profile)
        try:
            data = await client.auth_me()
            formatter.print_raw(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)


@app.command("session")
def session():
    """Check session status."""
    asyncio.run(_session())


async def _session():
    profile, formatter, api_url, timeout = resolve_context()

    async with O2Client(api_url, timeout) as client:
        setup_client(client, profile)
        try:
            data = await client.auth_session_status()
            formatter.print_raw(data)
        except APIError as e:
            formatter.print_error(str(e), e.code)
            raise typer.Exit(1)
        except ConnectionError as e:
            formatter.print_error(str(e))
            raise typer.Exit(1)
