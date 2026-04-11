"""o2 setup commands - Install skill files for vibe coding tools."""

from pathlib import Path
from typing import Optional

import typer

from o2_cli.setup import (
    interactive_setup,
    setup_tool,
    update_skills,
    show_skill,
    show_status,
    ALL_TOOLS,
)

app = typer.Typer(help="Setup and configure O2 CLI for your coding tool")


@app.callback(invoke_without_command=True)
def setup_main(
    tool: Optional[str] = typer.Option(
        None, "--tool", "-t",
        help=f"Tool name ({', '.join(t.name for t in ALL_TOOLS)}). Interactive if omitted."
    ),
    scope: str = typer.Option(
        "project", "--scope", "-s",
        help="Install scope: global or project"
    ),
    update: bool = typer.Option(
        False, "--update", "-u",
        help="Re-install skill files for all previously configured tools"
    ),
    show: bool = typer.Option(
        False, "--show-skill",
        help="Print the full skill content"
    ),
    status: bool = typer.Option(
        False, "--status",
        help="Show current setup status"
    ),
):
    """Setup O2 CLI for your vibe coding tool.

    \b
    Interactive mode:
      o2 setup

    \b
    Non-interactive (for agents/CI):
      o2 setup --tool claude-code --scope global
      o2 setup --tool cursor --scope project

    \b
    Update all configured tools:
      o2 setup --update

    \b
    Available tools: claude-code, cursor, codex, windsurf, cline, trae
    """
    if show:
        show_skill()
        return

    if status:
        show_status()
        return

    if update:
        update_skills()
        return

    if tool:
        setup_tool(tool, scope)
        return

    # Default: interactive wizard
    interactive_setup()
