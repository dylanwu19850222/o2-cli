"""O2 CLI - Command-line interface for O2 DEX Trading Platform."""

from pathlib import Path

__version__ = "0.1.1"


def ensure_skill_installed() -> bool:
    """自动安装 Claude Code Skill 到 ~/.claude/skills/o2-cli/。

    首次运行 o2 命令时检查并安装。不覆盖已有文件（用户可能自定义过）。

    Returns:
        True 如果 skill 已存在或刚安装成功，False 如果安装失败。
    """
    skill_dir = Path.home() / ".claude" / "skills" / "o2-cli"
    skill_file = skill_dir / "SKILL.md"

    if skill_file.exists():
        return True

    try:
        from o2_cli.setup import SKILL_CONTENT

        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(SKILL_CONTENT, encoding="utf-8")
        return True
    except OSError:
        # 权限不足或其他 IO 错误，静默失败不影响 CLI 使用
        return False
