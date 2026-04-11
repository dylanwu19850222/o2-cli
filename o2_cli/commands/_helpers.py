"""Shared helpers for CLI commands to reduce boilerplate."""

import asyncio
from pathlib import Path
from functools import wraps
from typing import Callable, Any

import typer

from o2_cli.cli import get_state
from o2_cli.client import O2Client
from o2_cli.config import load_config, get_active_profile, CONFIG_FILE
from o2_cli.exceptions import APIError, ConnectionError
from o2_cli.output import OutputFormatter


def resolve_context(state: dict | None = None):
    """Resolve CLI context: config, profile, formatter, api_url, timeout.

    Returns: (profile, formatter, api_url, timeout)
    """
    if state is None:
        state = get_state()

    config_path = Path(state["config_path"]) if state.get("config_path") else CONFIG_FILE
    config = load_config(config_path)
    if state.get("profile"):
        config.active_profile = state["profile"]

    profile = get_active_profile(config)
    formatter = OutputFormatter(json_mode=state["json_output"])
    api_url = state.get("api_url") or profile.api_url
    timeout = state.get("timeout", profile.timeout) or profile.timeout

    return profile, formatter, api_url, timeout


def require_auth(profile, formatter) -> bool:
    """Check if user is authenticated. Returns True if OK, False if not."""
    if profile.auth_type == "jwt" and not profile.token:
        formatter.print_error("Not authenticated. Run 'o2 auth test-login' or 'o2 auth login' first.")
        return False
    return True


def setup_client(client: O2Client, profile):
    """Configure client auth from profile."""
    if profile.token:
        client.set_jwt(profile.token)
    if profile.api_key_id:
        client.set_api_key(profile.api_key_id, profile.api_secret)


def handle_api_errors(func: Callable) -> Callable:
    """Decorator for async command handlers that catches API/Connection errors."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except APIError as e:
            # Need to get formatter from somewhere - callers should handle
            raise
        except ConnectionError as e:
            raise
    return wrapper
