"""O2 CLI Setup Wizard - Install skill files for different vibe coding tools.

Supports:
  - Claude Code  → ~/.claude/skills/ or .claude/skills/
  - Cursor       → .cursor/rules/
  - Codex (OpenAI) → AGENTS.md
  - Windsurf     → .windsurfrules
  - Cline        → .clinerules
  - Trae         → .trae/rules/

Usage:
  o2 setup          # Interactive wizard
  o2 setup --tool claude-code --scope global   # Non-interactive
  o2 setup --update # Re-install all configured tools
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from o2_cli import __version__

console = Console()

# ── Skill content (single source of truth) ──────────────────────────────────

SKILL_CONTENT = """\
# O2 CLI Trading Tool

**Category**: Trading
**Severity**: Normal
**Auto-trigger**: Yes

---

## When to Use

当用户提到以下操作时，使用 O2 CLI 而不是直接调用 API：

- 查询 O2 余额、订单、持仓、市场数据
- 创建/取消/修改订单
- 充值/提币操作
- 账户设置（杠杆、保证金模式）
- 查看 K 线、订单簿、手续费

---

## Quick Reference

**安装**（首次使用前检查）:

```bash
which o2 || pip install o2-cli
```

### 核心规则

1. **`--json` 必须放在命令前面**: `o2 --json balance show` / `o2 balance show --json` ❌
2. **公开命令无需登录**: `markets list`, `fees rates`
3. **其他命令需要先登录**: `o2 auth test-login`
4. **退出码**: 0=成功, 1=失败（错误到 stderr，数据到 stdout）

### 常用命令

```bash
# 认证
o2 auth test-login                          # 登录（token 自动保存）

# 市场数据（公开）
o2 --json markets list                      # 市场列表
o2 --json markets orderbook --market-id 1   # BTC 订单簿
o2 --json markets candles --market-id 1 --interval 1h

# 余额
o2 --json balance show                      # 余额（现金+赠金）
o2 --json balance history

# 订单
o2 --json orders create -m 1 -s long -t market -a 0.001       # 市价做多
o2 --json orders create -m 1 -s short -t limit -a 0.001 -p 85000  # 限价做空
o2 --json orders list --status open
o2 --json orders cancel --order-id <ID>
o2 --json orders cancel-all

# 持仓
o2 --json positions list
o2 --json positions close --position-id <ID>
o2 --json positions risk --market-id 1

# 设置
o2 --json settings leverage --market-id 1 --leverage 10
o2 --json settings margin-mode --mode cross

# 充提
o2 --json deposits address --chain base
o2 --json withdrawals create --amount 500 --address 0x... --chain ethereum

# 其他
o2 --json trades list
o2 --json fees rates
o2 --json account overview
o2 --json notifications list
```

### 参数说明

| 参数 | 含义 | 值 |
|------|------|-----|
| `--market-id` / `-m` | 市场 | 1=BTC, 2=ETH |
| `--side` / `-s` | 方向 | `long` / `short` |
| `--order-type` / `-t` | 类型 | `market` / `limit` |
| `--base-amount` / `-a` | 数量 | 实际数量如 0.001 |
| `--price` / `-p` | 价格 | USDC |
| `--leverage` / `-l` | 杠杆 | 1-50 |

### 故障排查

- `Cannot connect` → 启动 O2 Backend
- `Not authenticated` → `o2 auth test-login`
- `o2: command not found` → `pip install o2-cli`

### 更新

```bash
o2 setup --update    # 更新所有已安装工具的 skill 文件
```
"""

# Cursor MDC 格式（带 frontmatter）
CURSOR_MDC_CONTENT = """\
---
description: O2 CLI Trading Tool - 使用命令行操作 O2 交易平台
globs:
alwaysApply: true
---

""" + SKILL_CONTENT

# Codex AGENTS.md 区块
CODEX_SECTION = """

## O2 CLI Trading Tool

使用 O2 CLI 操作 O2 交易平台。安装: `pip install o2-cli`

### 核心规则
1. `--json` 放在命令前面: `o2 --json balance show`
2. 公开命令无需登录: `markets list`, `fees rates`
3. 需要登录的命令先执行: `o2 auth test-login`

### 常用命令
```bash
o2 auth test-login                    # 登录
o2 --json markets list                # 市场列表
o2 --json balance show                # 余额
o2 --json orders create -m 1 -s long -t market -a 0.001  # 市价做多
o2 --json orders list --status open   # 查询订单
o2 --json positions list              # 持仓
o2 --json settings leverage --market-id 1 --leverage 10   # 杠杆
o2 --json deposits address --chain base  # 充值地址
o2 --json account overview            # 账户总览
```

详细文档: `o2 setup --show-skill`
"""

# Windsurf / Cline 规则格式（追加到文件末尾）
RULES_SECTION = """

# O2 CLI Trading Tool

使用 O2 CLI 操作 O2 交易平台。安装: `pip install o2-cli`

## 规则
1. `--json` 放命令前面: `o2 --json balance show` (不是 `o2 balance show --json`)
2. 公开命令无需登录: `markets list`, `fees rates`
3. 需要登录先执行: `o2 auth test-login`

## 常用命令
- `o2 --json markets list` - 市场列表
- `o2 --json balance show` - 余额
- `o2 --json orders create -m 1 -s long -t market -a 0.001` - 市价做多
- `o2 --json orders list --status open` - 查询订单
- `o2 --json positions list` - 持仓
- `o2 --json account overview` - 账户总览

详细文档: `o2 setup --show-skill`
"""


# ── Tool definitions ────────────────────────────────────────────────────────

class ToolConfig:
    """Defines how to install skill for a specific vibe coding tool."""

    def __init__(
        self,
        name: str,
        display_name: str,
        install_scopes: list[str],  # ["global", "project"] or ["project"]
    ):
        self.name = name
        self.display_name = display_name
        self.install_scopes = install_scopes

    def get_install_path(self, scope: str, project_dir: Path) -> Path:
        raise NotImplementedError

    def get_content(self) -> str:
        raise NotImplementedError

    def is_installed(self, scope: str, project_dir: Path) -> bool:
        return self.get_install_path(scope, project_dir).exists()

    def install(self, scope: str, project_dir: Path) -> Path:
        path = self.get_install_path(scope, project_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        content = self.get_content()

        if self.name == "codex":
            # Append to AGENTS.md, don't overwrite
            if path.exists():
                existing = path.read_text(encoding="utf-8")
                if "O2 CLI Trading Tool" in existing:
                    # Replace existing section
                    import re
                    pattern = r"\n## O2 CLI Trading Tool\n.*"
                    existing = re.sub(pattern, "", existing, flags=re.DOTALL)
                path.write_text(existing.rstrip() + "\n" + content, encoding="utf-8")
            else:
                path.write_text(content.lstrip(), encoding="utf-8")
        elif self.name in ("windsurf", "cline"):
            # Append to rules file
            if path.exists():
                existing = path.read_text(encoding="utf-8")
                if "O2 CLI Trading Tool" in existing:
                    import re
                    pattern = r"\n# O2 CLI Trading Tool\n.*"
                    existing = re.sub(pattern, "", existing, flags=re.DOTALL)
                path.write_text(existing.rstrip() + "\n" + content, encoding="utf-8")
            else:
                path.write_text(content.lstrip(), encoding="utf-8")
        else:
            path.write_text(content, encoding="utf-8")

        return path


class ClaudeCodeTool(ToolConfig):
    def __init__(self):
        super().__init__("claude-code", "Claude Code", ["global", "project"])

    def get_install_path(self, scope: str, project_dir: Path) -> Path:
        if scope == "global":
            return Path.home() / ".claude" / "skills" / "o2-cli" / "SKILL.md"
        return project_dir / ".claude" / "skills" / "o2-cli" / "SKILL.md"

    def get_content(self) -> str:
        return SKILL_CONTENT


class CursorTool(ToolConfig):
    def __init__(self):
        super().__init__("cursor", "Cursor", ["project"])

    def get_install_path(self, scope: str, project_dir: Path) -> Path:
        return project_dir / ".cursor" / "rules" / "o2-cli.mdc"

    def get_content(self) -> str:
        return CURSOR_MDC_CONTENT


class CodexTool(ToolConfig):
    def __init__(self):
        super().__init__("codex", "Codex (OpenAI)", ["project"])

    def get_install_path(self, scope: str, project_dir: Path) -> Path:
        return project_dir / "AGENTS.md"

    def get_content(self) -> str:
        return CODEX_SECTION


class WindsurfTool(ToolConfig):
    def __init__(self):
        super().__init__("windsurf", "Windsurf", ["project"])

    def get_install_path(self, scope: str, project_dir: Path) -> Path:
        return project_dir / ".windsurfrules"

    def get_content(self) -> str:
        return RULES_SECTION


class ClineTool(ToolConfig):
    def __init__(self):
        super().__init__("cline", "Cline (VS Code)", ["project"])

    def get_install_path(self, scope: str, project_dir: Path) -> Path:
        return project_dir / ".clinerules"

    def get_content(self) -> str:
        return RULES_SECTION


class TraeTool(ToolConfig):
    def __init__(self):
        super().__init__("trae", "Trae", ["project"])

    def get_install_path(self, scope: str, project_dir: Path) -> Path:
        return project_dir / ".trae" / "rules" / "o2-cli.md"

    def get_content(self) -> str:
        return SKILL_CONTENT


ALL_TOOLS: list[ToolConfig] = [
    ClaudeCodeTool(),
    CursorTool(),
    CodexTool(),
    WindsurfTool(),
    ClineTool(),
    TraeTool(),
]

TOOL_BY_NAME: dict[str, ToolConfig] = {t.name: t for t in ALL_TOOLS}

# ── Install state tracking ──────────────────────────────────────────────────

STATE_FILE = Path.home() / ".o2" / "setup-state.json"


def load_state() -> dict:
    """Load setup state (which tools are installed, version, etc.)."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"installed_tools": [], "version": None}


def save_state(state: dict) -> None:
    """Save setup state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["version"] = __version__
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


# ── CLI check ───────────────────────────────────────────────────────────────

def is_cli_installed() -> bool:
    """Check if o2 CLI is in PATH."""
    try:
        result = subprocess.run(
            ["which", "o2"], capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


# ── Interactive setup ───────────────────────────────────────────────────────

def interactive_setup(project_dir: Path | None = None) -> None:
    """Run interactive setup wizard."""
    if project_dir is None:
        project_dir = Path.cwd()

    console.print(Panel(
        "[bold]O2 CLI Setup Wizard[/bold]\n\n"
        "Select your vibe coding tool(s) to install the skill file.\n"
        "Run again anytime to add more tools or switch tools.",
        title="o2 setup",
        border_style="cyan",
    ))

    # Step 1: Check CLI
    if is_cli_installed():
        console.print("[green]✓[/green] o2 CLI is installed")
    else:
        console.print("[yellow]⚠[/yellow] o2 CLI not in PATH")
        console.print("  Install with: [bold]pip install -e .[/bold]")
        if not confirm("Continue setup anyway?"):
            return

    # Step 2: Show installed tools
    state = load_state()
    if state.get("installed_tools"):
        console.print(f"\n[dim]Previously installed: {', '.join(state['installed_tools'])}[/dim]")

    # Step 3: Select tools
    console.print("\n[bold]Available tools:[/bold]")
    for i, tool in enumerate(ALL_TOOLS, 1):
        scopes = "/".join(tool.install_scopes)
        console.print(f"  {i}. {tool.display_name} ({scopes})")
    console.print(f"  0. [bold]All tools[/bold]")

    choice = input("\nSelect tool number (or comma-separated, e.g. 1,3): ").strip()

    if choice == "0":
        selected_tools = ALL_TOOLS
    else:
        selected_tools = []
        for num in choice.split(","):
            try:
                idx = int(num.strip()) - 1
                if 0 <= idx < len(ALL_TOOLS):
                    selected_tools.append(ALL_TOOLS[idx])
            except ValueError:
                console.print(f"[red]Invalid: {num}[/red]")

    if not selected_tools:
        console.print("[red]No tools selected.[/red]")
        return

    # Step 4: For each tool, choose scope and install
    installed = []
    for tool in selected_tools:
        console.print(f"\n[bold cyan]→ {tool.display_name}[/bold cyan]")

        # Choose scope
        if len(tool.install_scopes) > 1:
            scope = choose_scope(tool.install_scopes)
        else:
            scope = tool.install_scopes[0]
            console.print(f"  Scope: {scope}")

        # Install
        path = tool.install(scope, project_dir)
        console.print(f"  [green]✓[/green] Installed to: [dim]{path}[/dim]")
        installed.append({"tool": tool.name, "scope": scope, "path": str(path)})

    # Step 5: Save state
    state["installed_tools"] = [item["tool"] for item in installed]
    state["install_details"] = installed
    save_state(state)

    console.print(Panel(
        f"[bold green]Setup complete![/bold green]\n\n"
        f"Installed {len(installed)} tool(s):\n"
        + "\n".join(f"  • {item['tool']} ({item['scope']}) → {item['path']}" for item in installed)
        + f"\n\nTo update skills later: [bold]o2 setup --update[/bold]"
        + f"\nTo change tools: [bold]o2 setup[/bold] (re-run)",
        border_style="green",
    ))


def choose_scope(scopes: list[str]) -> str:
    """Let user choose install scope."""
    if len(scopes) == 1:
        return scopes[0]

    console.print("  Choose scope:")
    for i, s in enumerate(scopes, 1):
        desc = "system-wide (~/.claude/skills/)" if s == "global" else "project-level (./.claude/skills/)"
        console.print(f"    {i}. {s} ({desc})")

    while True:
        try:
            choice = int(input("  Scope [1]: ").strip() or "1")
            if 1 <= choice <= len(scopes):
                return scopes[choice - 1]
        except ValueError:
            pass
        console.print("  [red]Invalid choice[/red]")


def confirm(message: str) -> bool:
    return input(f"{message} [y/N]: ").strip().lower() in ("y", "yes")


# ── Non-interactive setup ───────────────────────────────────────────────────

def setup_tool(tool_name: str, scope: str = "project", project_dir: Path | None = None) -> None:
    """Non-interactive setup for CI/agent use."""
    if project_dir is None:
        project_dir = Path.cwd()

    tool = TOOL_BY_NAME.get(tool_name)
    if not tool:
        console.print(f"[red]Unknown tool: {tool_name}[/red]")
        console.print(f"Available: {', '.join(TOOL_BY_NAME.keys())}")
        return

    path = tool.install(scope, project_dir)
    state = load_state()
    if tool_name not in state.get("installed_tools", []):
        state.setdefault("installed_tools", []).append(tool_name)
    save_state(state)
    console.print(f"[green]✓[/green] {tool.display_name} installed to: {path}")


# ── Update ──────────────────────────────────────────────────────────────────

def update_skills(project_dir: Path | None = None) -> None:
    """Re-install skill files for all previously configured tools."""
    if project_dir is None:
        project_dir = Path.cwd()

    state = load_state()
    installed = state.get("installed_tools", [])

    if not installed:
        console.print("[yellow]No tools configured. Run [bold]o2 setup[/bold] first.[/yellow]")
        return

    console.print(f"[bold]Updating skills for: {', '.join(installed)}[/bold]")
    for tool_name in installed:
        tool = TOOL_BY_NAME.get(tool_name)
        if not tool:
            continue
        # Find the scope from install details
        details = state.get("install_details", [])
        scope = "project"
        for d in details:
            if d.get("tool") == tool_name:
                scope = d.get("scope", "project")
                break
        path = tool.install(scope, project_dir)
        console.print(f"  [green]✓[/green] {tool.display_name} → {path}")

    state["version"] = __version__
    save_state(state)
    console.print("[green]All skills updated![/green]")


def show_skill() -> None:
    """Print the full skill content to stdout."""
    print(SKILL_CONTENT)


def show_status() -> None:
    """Show current setup status."""
    state = load_state()
    installed = state.get("installed_tools", [])
    version = state.get("version", "unknown")

    table = Table(title="O2 CLI Setup Status")
    table.add_column("Item", style="bold")
    table.add_column("Value")

    table.add_row("CLI Version", __version__)
    table.add_row("Installed in PATH", "Yes" if is_cli_installed() else "No")
    table.add_row("Skills Version", version)
    table.add_row("Configured Tools", ", ".join(installed) if installed else "None")

    console.print(table)

    if installed:
        console.print("\n[bold]Install details:[/bold]")
        for d in state.get("install_details", []):
            tool = TOOL_BY_NAME.get(d.get("tool", ""))
            name = tool.display_name if tool else d["tool"]
            console.print(f"  • {name} ({d.get('scope', '?')}) → {d.get('path', '?')}")
