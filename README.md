# O2 CLI

Command-line interface for [O2 DEX](https://github.com/dylanwu19850222/lighter-dex) Trading Platform.

## Install

```bash
pip install o2-cli
```

## Quick Start

```bash
# Login (dev environment)
o2 auth test-login

# View markets (public, no login needed)
o2 --json markets list

# Check balance
o2 --json balance show

# Place a market order (long 0.001 BTC)
o2 --json orders create -m 1 -s long -t market -a 0.001

# View positions
o2 --json positions list
```

## Vibe Coding Tool Setup

After installing, run the setup wizard to install skill files for your AI coding tool:

```bash
# Interactive wizard
o2 setup

# Non-interactive
o2 setup --tool claude-code --scope global
o2 setup --tool cursor --scope project

# Update all installed tools
o2 setup --update
```

Supported tools: **Claude Code**, **Cursor**, **Codex (OpenAI)**, **Windsurf**, **Cline**, **Trae**

## Key Rules

1. `--json` must come before the subcommand: `o2 --json balance show` (not `o2 balance show --json`)
2. Public commands (no login): `markets list`, `fees rates`
3. Other commands require `o2 auth test-login` first
4. Exit codes: 0 = success, 1 = error

## Commands

| Group | Commands | Auth Required |
|-------|----------|---------------|
| `auth` | `test-login`, `me`, `session` | No (login) |
| `markets` | `list`, `orderbook`, `candles`, `trades` | No |
| `fees` | `rates`, `estimate` | No |
| `balance` | `show`, `history` | Yes |
| `orders` | `create`, `list`, `cancel`, `cancel-all`, `modify`, `batch` | Yes |
| `positions` | `list`, `market`, `close`, `risk` | Yes |
| `trades` | `list`, `summary` | Yes |
| `deposits` | `address`, `history` | Yes |
| `withdrawals` | `create`, `status`, `cancel`, `list` | Yes |
| `settings` | `get`, `leverage`, `margin-mode` | Yes |
| `notifications` | `list`, `unread`, `read` | Yes |
| `account` | `overview` | Yes |
| `mm` | `status`, `start`, `stop`, `stats`, `orders` | API Key |
| `admin` | `gas-status`, `proxy-list`, `api-keys`, `reconcile` | Admin JWT |
| `setup` | wizard, `--tool`, `--update`, `--status` | No |

## Configuration

Config file: `~/.o2/config.yaml`

```yaml
active_profile: default
profiles:
  default:
    api_url: http://localhost:8000/api/v1
    timeout: 30
    auth_type: jwt
    token: eyJ...  # auto-saved
```

Override at runtime:
```bash
o2 --profile production --json balance show
o2 --api-url https://api.example.com/api/v1 --json markets list
```

## Development

```bash
git clone https://github.com/dylanwu19850222/o2-cli.git
cd o2-cli
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check o2_cli/
```

## License

MIT
