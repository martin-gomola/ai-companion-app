"""Global handoff install and uninstall, run against app folders under tmp_path (never the real home)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from yourturn.cli import main
from yourturn.install import CLAUDE_BLOCK, END, START, install, mcp_server, uninstall

MINE = "# My rules\n\nKeep answers short.\n"
OTHER = {"mcpServers": {"context7": {"command": "npx", "args": ["context7"]}}}


def _homes(tmp_path: Path) -> dict[str, Path]:
    homes = {name: tmp_path / name for name in ("codex", "claude", "cursor")}
    for home in homes.values():
        home.mkdir()
    return homes


def _tree(root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)): path.read_text() for path in sorted(root.rglob("*")) if path.is_file()}


def _fake(tmp_path: Path, name: str, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A CLI on an otherwise empty PATH that logs its arguments and its app-home variable."""
    bin_dir, log = tmp_path / "bin", tmp_path / f"{name}.log"
    bin_dir.mkdir(exist_ok=True)
    script = bin_dir / name
    script.write_text(f'#!/bin/sh\necho "$CODEX_HOME$CLAUDE_CONFIG_DIR|$*" >> {log}\nexit 0\n')
    script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:/usr/bin:/bin")
    return log


@pytest.fixture
def no_clis(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """No codex or claude on PATH, and a project folder as the working directory that must stay empty."""
    empty = tmp_path / "empty-bin"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)
    return project


def test_install_is_global_idempotent_and_uninstall_restores_the_files(tmp_path: Path, no_clis: Path) -> None:
    homes = _homes(tmp_path)
    (homes["claude"] / "CLAUDE.md").write_text(MINE)
    (homes["cursor"] / "mcp.json").write_text(json.dumps(OTHER))

    install(["claude", "cursor"], homes)
    first = _tree(tmp_path)
    claude_skill = (homes["claude"] / "skills" / "your-turn" / "SKILL.md").read_text()
    cursor_skill = (homes["cursor"] / "skills" / "your-turn" / "SKILL.md").read_text()
    assert "name: your-turn\n" in claude_skill and "Claude Code" in claude_skill and "`AskUserQuestion`" in claude_skill
    assert "Cursor" in cursor_skill and "`AskQuestion`" in cursor_skill and "Codex" not in cursor_skill
    assert "**Outcome:**" in cursor_skill and "**Next step:**" in cursor_skill
    assert (homes["claude"] / "CLAUDE.md").read_text() == f"{MINE}\n{CLAUDE_BLOCK}"
    assert json.loads((homes["cursor"] / "mcp.json").read_text())["mcpServers"] == {**OTHER["mcpServers"], "your-turn": mcp_server()}
    # Nothing lands in the project, and Codex (not selected) is untouched.
    assert list(no_clis.iterdir()) == [] and list(homes["codex"].iterdir()) == []

    install(["claude", "cursor"], homes)
    assert _tree(tmp_path) == first

    uninstall(["claude", "cursor"], homes)
    assert (homes["claude"] / "CLAUDE.md").read_text() == MINE
    assert json.loads((homes["cursor"] / "mcp.json").read_text()) == OTHER
    assert not (homes["claude"] / "skills" / "your-turn").exists() and not (homes["cursor"] / "skills" / "your-turn").exists()
    after = _tree(tmp_path)
    uninstall(["claude", "cursor"], homes)
    assert _tree(tmp_path) == after


def test_block_is_replaced_in_place_and_files_it_created_are_removed(tmp_path: Path, no_clis: Path) -> None:
    homes = _homes(tmp_path)
    memory = homes["claude"] / "CLAUDE.md"
    memory.write_text(f"Above.\n\n{START}\nold handoff text\n{END}\n\nBelow.\n")
    install(["claude"], homes)
    assert memory.read_text() == f"Above.\n\n{CLAUDE_BLOCK}\nBelow.\n"
    uninstall(["claude"], homes)
    assert memory.read_text() == "Above.\n\nBelow.\n"

    # Files that held only what install wrote are gone again, so uninstall leaves no empty leftovers.
    memory.unlink()
    install(["claude", "cursor"], homes)
    uninstall(["claude", "cursor"], homes)
    assert not memory.exists() and not (homes["cursor"] / "mcp.json").exists()


def test_invalid_cursor_mcp_json_is_left_alone(tmp_path: Path, no_clis: Path, capsys: pytest.CaptureFixture[str]) -> None:
    homes = _homes(tmp_path)
    (homes["cursor"] / "mcp.json").write_text("{not json")
    install(["cursor"], homes)
    assert (homes["cursor"] / "mcp.json").read_text() == "{not json"
    assert "is not valid JSON" in capsys.readouterr().out


def test_claude_mcp_server_goes_through_the_claude_cli_at_user_scope(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    homes = _homes(tmp_path)
    log = _fake(tmp_path, "claude", monkeypatch)
    install(["claude"], homes)
    uninstall(["claude"], homes)
    home = str(homes["claude"])
    assert log.read_text().splitlines() == [
        f"{home}|mcp remove --scope user your-turn",
        f"{home}|mcp add-json --scope user your-turn {json.dumps(mcp_server())}",
        f"{home}|mcp remove --scope user your-turn",
    ]


def test_codex_uninstall_removes_the_plugin_and_marketplace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    homes = _homes(tmp_path)
    log = _fake(tmp_path, "codex", monkeypatch)
    uninstall(["codex"], homes)
    home = str(homes["codex"])
    assert log.read_text().splitlines() == [f"{home}|plugin remove your-turn@your-turn", f"{home}|plugin marketplace remove your-turn"]


def test_cli_uninstall_only_touches_apps_that_are_present(tmp_path: Path, no_clis: Path) -> None:
    claude = tmp_path / "claude"
    install(["claude"], {"claude": claude})
    main(["uninstall", "--codex-home", str(tmp_path / "no-codex"), "--claude-home", str(claude),
          "--cursor-home", str(tmp_path / "no-cursor")])
    assert not (claude / "skills" / "your-turn").exists() and not (claude / "CLAUDE.md").exists()
    assert not (tmp_path / "no-codex").exists() and not (tmp_path / "no-cursor").exists()
