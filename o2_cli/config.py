"""YAML configuration management for O2 CLI.

Config file: ~/.o2/config.yaml
Supports named profiles (default, production, etc.).
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import yaml


CONFIG_DIR = Path.home() / ".o2"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


@dataclass
class Profile:
    """A named configuration profile."""

    api_url: str = "http://localhost:8000/api/v1"
    timeout: float = 30.0
    auth_type: str = "jwt"  # "jwt" or "api_key"
    token: Optional[str] = None
    api_key_id: Optional[str] = None
    api_secret: Optional[str] = None
    default_market_id: Optional[int] = None
    default_chain: str = "base"
    output_format: str = "auto"  # "auto", "json", "table", "text"


@dataclass
class AppConfig:
    """Root config with named profiles."""

    active_profile: str = "default"
    profiles: dict[str, Profile] = field(default_factory=lambda: {"default": Profile()})


def load_config(config_path: Path = CONFIG_FILE) -> AppConfig:
    """Load config from YAML file. Returns default config if file doesn't exist."""
    if not config_path.exists():
        return AppConfig()

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    profiles = {}
    for name, pdata in data.get("profiles", {}).items():
        profiles[name] = Profile(**pdata) if isinstance(pdata, dict) else Profile()

    if not profiles:
        profiles["default"] = Profile()

    return AppConfig(
        active_profile=data.get("active_profile", "default"),
        profiles=profiles,
    )


def save_config(config: AppConfig, config_path: Path = CONFIG_FILE) -> None:
    """Save config to YAML file."""
    config_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "active_profile": config.active_profile,
        "profiles": {name: asdict(p) for name, p in config.profiles.items()},
    }

    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def get_active_profile(config: AppConfig) -> Profile:
    """Get the currently active profile."""
    return config.profiles.get(config.active_profile, Profile())


def save_token(profile_name: str, token: str, config_path: Path = CONFIG_FILE) -> None:
    """Persist JWT token to config file for a profile."""
    config = load_config(config_path)
    if profile_name not in config.profiles:
        config.profiles[profile_name] = Profile()
    config.profiles[profile_name].token = token
    config.profiles[profile_name].auth_type = "jwt"
    save_config(config, config_path)
