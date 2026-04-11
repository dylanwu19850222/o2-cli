"""O2 CLI - Command-line interface for O2 DEX Trading Platform."""

from pathlib import Path

__version__ = "0.1.3"


def ensure_skill_installed() -> bool:
    """自动安装或更新 Claude Code Skill 到 ~/.claude/skills/o2-cli/。

    首次运行时安装。CLI 升级后自动刷新 skill 内容。

    Returns:
        True 如果 skill 已存在或刚安装成功，False 如果安装失败。
    """
    skill_dir = Path.home() / ".claude" / "skills" / "o2-cli"
    skill_file = skill_dir / "SKILL.md"
    version_file = skill_dir / ".version"

    try:
        from o2_cli.setup import SKILL_CONTENT

        # Check if skill needs update (missing or version mismatch)
        current_version = __version__
        installed_version = ""
        if version_file.exists():
            installed_version = version_file.read_text(encoding="utf-8").strip()

        needs_update = (
            not skill_file.exists()
            or installed_version != current_version
        )

        if not needs_update:
            return True

        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(SKILL_CONTENT, encoding="utf-8")
        version_file.write_text(current_version, encoding="utf-8")
        return True
    except OSError:
        return False
