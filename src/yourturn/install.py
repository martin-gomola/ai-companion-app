"""Install the handoff for each agent app, globally: only under the user's own app folders
(`~/.codex`, `~/.claude`, `~/.cursor`), never in a project, so no repository needs a .gitignore entry.

Codex gets the plugin (skill and MCP server). Claude Code and Cursor get the same skill in their global
skills folder and the same MCP server in their user-level config; Claude Code also gets a short block
in its global CLAUDE.md so every chat follows the handoff, not only those where the skill is picked.
Every step is idempotent, and `uninstall` removes only what `install` added.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from importlib.resources import files
from pathlib import Path

MARKETPLACE_SOURCE = "martin-gomola/your-turn"
MARKETPLACE = "your-turn"
PLUGIN = f"your-turn@{MARKETPLACE}"
NAME = "your-turn"  # Skill folder and MCP server name in Claude Code and Cursor.
APPS = {"codex": "Codex", "claude": "Claude Code", "cursor": "Cursor"}
ASK_TOOLS = {"claude": "AskUserQuestion", "cursor": "AskQuestion"}
START, END = "<!-- your-turn:start -->", "<!-- your-turn:end -->"
# The block with the blank lines around it, so removing or replacing it leaves one blank line between neighbours.
BLOCK = re.compile(rf"\n*{re.escape(START)}.*?{re.escape(END)}\n*", re.DOTALL)
CLAUDE_BLOCK = f"""{START}
## Your Turn handoff

Start every final answer with `**Outcome:**` (one sentence: what is now true) and `**Next step:**`
(`none`, `answer: …`, `review: …`, `approve: …` or `run: …`); from the second turn on, add
`**Recap:**`. Ask the user to choose with `AskUserQuestion`. The `your-turn` skill has the details.
{END}
"""
QUESTIONS = """
## Questions

When you need the user to choose, ask with the `{tool}` tool and list the options. Your Turn shows
the question and its options under Needs you until it is answered.
"""


def plugin_text(name: str) -> str:
    """A file of the Codex plugin: packaged into the wheel, or read from a source checkout."""
    packaged = files("yourturn").joinpath("plugin", name)
    path = packaged if packaged.is_file() else Path(__file__).resolve().parents[2] / "plugin" / name
    return path.read_text(encoding="utf-8")


def skill_text(harness: str) -> str:
    """The Codex handoff skill, renamed and worded for another app, plus how it asks questions."""
    text = plugin_text("skills/your-turn-handoff/SKILL.md")
    text = text.replace("name: your-turn-handoff", f"name: {NAME}").replace("Codex", APPS[harness])
    return text.rstrip("\n") + "\n" + QUESTIONS.format(tool=ASK_TOOLS[harness])


def mcp_server() -> dict[str, object]:
    """The plugin's `your-turn` MCP server (for `log_decision`) without Codex-only keys."""
    server = json.loads(plugin_text(".mcp.json"))["mcpServers"][NAME]
    return {key: server[key] for key in ("type", "command", "args")}


def detect(homes: dict[str, Path]) -> list[str]:
    """Apps whose home folder exists on this machine."""
    return [harness for harness, home in homes.items() if home.is_dir()]


def _write(path: Path, text: str) -> str:
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return "unchanged"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return "written"


def _remove_tree(path: Path) -> str:
    if not path.exists():
        return "not present"
    shutil.rmtree(path)
    return "removed"


# --- Codex ---------------------------------------------------------------------------------------


def _codex(args: list[str], home: Path | None, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "CODEX_HOME": str(home)} if home is not None else None
    return subprocess.run(["codex", *args], capture_output=not check, text=True, check=check, env=env)


def install_plugin(home: Path | None = None) -> bool:
    """Install the handoff skill and MCP server into Codex. Returns False when Codex is unavailable."""
    if not shutil.which("codex"):
        print("Codex CLI not found, so the plugin was not installed. The inbox still works, with weaker recaps.", flush=True)
        return False
    env = {**os.environ, "CODEX_HOME": str(home)} if home is not None else None
    listed = subprocess.run(["codex", "plugin", "marketplace", "list"], capture_output=True, text=True, env=env)
    if not any(line.split()[:1] == [MARKETPLACE] for line in listed.stdout.splitlines()):
        _codex(["plugin", "marketplace", "add", MARKETPLACE_SOURCE], home)
    _codex(["plugin", "add", PLUGIN], home)
    print(f"Codex: installed {PLUGIN}. Restart Codex so agents start writing Your Turn handoffs.", flush=True)
    return True


def uninstall_plugin(home: Path | None = None) -> None:
    if not shutil.which("codex"):
        print("Codex: CLI not found, nothing to remove.", flush=True)
        return
    # Either may already be gone; that is the state uninstall wants.
    _codex(["plugin", "remove", PLUGIN], home, check=False)
    _codex(["plugin", "marketplace", "remove", MARKETPLACE], home, check=False)
    print(f"Codex: removed {PLUGIN} and its marketplace.", flush=True)


# --- Claude Code ---------------------------------------------------------------------------------


def _claude_env(home: Path) -> dict[str, str]:
    # Only for a non-default home: with CLAUDE_CONFIG_DIR set, Claude Code keeps its user config in
    # $CLAUDE_CONFIG_DIR/.claude.json instead of ~/.claude.json.
    if home.expanduser().resolve() == (Path.home() / ".claude").resolve():
        return dict(os.environ)
    return {**os.environ, "CLAUDE_CONFIG_DIR": str(home)}


def _claude_mcp(home: Path, add: bool) -> str:
    if not shutil.which("claude"):
        return "skipped (claude CLI not found)"
    env = _claude_env(home)
    subprocess.run(["claude", "mcp", "remove", "--scope", "user", NAME], capture_output=True, text=True, env=env)
    if not add:
        return "removed"
    added = subprocess.run(["claude", "mcp", "add-json", "--scope", "user", NAME, json.dumps(mcp_server())],
                           capture_output=True, text=True, env=env)
    return "added" if added.returncode == 0 else f"failed: {(added.stderr or added.stdout).strip()}"


def install_claude(home: Path) -> None:
    skill = _write(home / "skills" / NAME / "SKILL.md", skill_text("claude"))
    memory = home / "CLAUDE.md"
    current = memory.read_text(encoding="utf-8") if memory.is_file() else ""
    if BLOCK.search(current):
        updated = BLOCK.sub(lambda _: f"\n\n{CLAUDE_BLOCK}\n", current, count=1).strip("\n") + "\n"
    else:
        updated = f"{current.rstrip()}\n\n{CLAUDE_BLOCK}" if current.strip() else CLAUDE_BLOCK
    block = _write(memory, updated)
    print(f"Claude Code: skill {skill}, CLAUDE.md block {block}, MCP server {_claude_mcp(home, add=True)} ({home}).", flush=True)


def uninstall_claude(home: Path) -> None:
    skill = _remove_tree(home / "skills" / NAME)
    memory, block = home / "CLAUDE.md", "not present"
    if memory.is_file():
        current = memory.read_text(encoding="utf-8")
        if BLOCK.search(current):
            rest = BLOCK.sub("\n\n", current, count=1).strip("\n")
            if rest:
                memory.write_text(rest + "\n", encoding="utf-8")
            else:
                memory.unlink()  # The file held only our block.
            block = "removed"
    print(f"Claude Code: skill {skill}, CLAUDE.md block {block}, MCP server {_claude_mcp(home, add=False)} ({home}).", flush=True)


# --- Cursor --------------------------------------------------------------------------------------


def _cursor_mcp(home: Path, add: bool) -> str:
    path = home / "mcp.json"
    try:
        config = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except json.JSONDecodeError:
        return f"skipped ({path} is not valid JSON)"
    servers = config.setdefault("mcpServers", {}) if isinstance(config, dict) else None
    if not isinstance(servers, dict):
        return f"skipped ({path} has an unexpected shape)"
    if add:
        servers[NAME] = mcp_server()
        return "unchanged" if _write(path, json.dumps(config, indent=2) + "\n") == "unchanged" else "added"
    if servers.pop(NAME, None) is None:
        return "not present"
    if not servers and set(config) == {"mcpServers"}:
        path.unlink()  # The file held only our server.
    else:
        _write(path, json.dumps(config, indent=2) + "\n")
    return "removed"


def install_cursor(home: Path) -> None:
    skill = _write(home / "skills" / NAME / "SKILL.md", skill_text("cursor"))
    print(f"Cursor: skill {skill}, MCP server {_cursor_mcp(home, add=True)} ({home}).", flush=True)


def uninstall_cursor(home: Path) -> None:
    skill = _remove_tree(home / "skills" / NAME)
    print(f"Cursor: skill {skill}, MCP server {_cursor_mcp(home, add=False)} ({home}).", flush=True)


def install(harnesses: list[str], homes: dict[str, Path]) -> None:
    if not harnesses:
        print("No Codex, Claude Code or Cursor folder found, so nothing was installed.", flush=True)
    for harness in harnesses:
        {"codex": install_plugin, "claude": install_claude, "cursor": install_cursor}[harness](homes[harness])


def uninstall(harnesses: list[str], homes: dict[str, Path]) -> None:
    for harness in harnesses:
        {"codex": uninstall_plugin, "claude": uninstall_claude, "cursor": uninstall_cursor}[harness](homes[harness])
