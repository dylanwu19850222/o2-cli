"""o2 config commands - Profile and environment management."""

import typer

from o2_cli.config import (
    load_config,
    save_config,
    get_active_profile,
    AppConfig,
    Profile,
    CONFIG_FILE,
)
from o2_cli.output import OutputFormatter
from o2_cli.cli import get_state

app = typer.Typer(help="Configuration and profile management")

PRODUCTION_API_URL = "https://lighter-dex-production.up.railway.app/api/v1"


@app.command("list")
def list_profiles():
    """Show all profiles and highlight the active one."""
    state = get_state()
    formatter = OutputFormatter(json_mode=state["json_output"])
    config = load_config(CONFIG_FILE)

    if state["json_output"]:
        import json

        data = {
            "active_profile": config.active_profile,
            "profiles": {
                name: {"api_url": p.api_url}
                for name, p in config.profiles.items()
            },
        }
        print(json.dumps(data, indent=2))
    else:
        for name, profile in config.profiles.items():
            marker = " (active)" if name == config.active_profile else ""
            formatter.print_success(f"  {name}{marker}: {profile.api_url}")


@app.command("use")
def use_profile(
    name: str = typer.Argument(..., help="Profile name to switch to"),
):
    """Switch active profile."""
    state = get_state()
    formatter = OutputFormatter(json_mode=state["json_output"])
    config = load_config(CONFIG_FILE)

    if name not in config.profiles:
        formatter.print_error(f"Profile '{name}' not found. Available: {', '.join(config.profiles.keys())}")
        raise typer.Exit(1)

    config.active_profile = name
    save_config(config, CONFIG_FILE)
    formatter.print_success(f"Switched to profile '{name}' ({config.profiles[name].api_url})")


@app.command("set")
def set_profile(
    name: str = typer.Argument(..., help="Profile name"),
    api_url: str = typer.Option(..., "--api-url", help="API URL"),
    timeout: float = typer.Option(None, "--timeout", help="HTTP timeout"),
):
    """Create or update a profile."""
    state = get_state()
    formatter = OutputFormatter(json_mode=state["json_output"])
    config = load_config(CONFIG_FILE)

    if name in config.profiles:
        profile = config.profiles[name]
        profile.api_url = api_url
        if timeout is not None:
            profile.timeout = timeout
    else:
        profile = Profile(api_url=api_url)
        if timeout is not None:
            profile.timeout = timeout
        config.profiles[name] = profile

    save_config(config, CONFIG_FILE)
    formatter.print_success(f"Profile '{name}' saved: {api_url}")


@app.command("init-production")
def init_production():
    """Quick setup: create production profile pointing to Railway."""
    state = get_state()
    formatter = OutputFormatter(json_mode=state["json_output"])
    config = load_config(CONFIG_FILE)

    config.profiles["production"] = Profile(
        api_url=PRODUCTION_API_URL,
        timeout=30.0,
    )
    save_config(config, CONFIG_FILE)
    formatter.print_success(f"Production profile created: {PRODUCTION_API_URL}")
    formatter.print_success("Switch with: o2 config use production")
