"""Render README screenshots from a made-up Codex home, so no real chat content is captured.

Run with `make screenshots`. Needs Google Chrome; Playwright comes from `uvx --with playwright`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "images"
PORT = 8799
NOW = datetime.now(UTC)


def at(minutes_ago: float) -> str:
    return (NOW - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


class Chat:
    def __init__(self, number: int, title: str, project: str, started: float) -> None:
        self.id = f"0d3e{number:04x}-0000-7000-8000-{number:012x}"
        self.title, self.project, self.clock, self.turn = title, project, started, 0
        self.records: list[dict] = [
            {"timestamp": at(started), "type": "session_meta", "payload": {
                "id": self.id, "cwd": f"/workspace/{project}", "timestamp": at(started), "source": "vscode",
                "model_provider": "openai", "cli_version": "0.80.0", "git": {"branch": "main"}}},
            {"timestamp": at(started), "type": "turn_context", "payload": {"model": "gpt-5.5", "effort": "medium"}},
        ]

    def _add(self, record_type: str, payload: dict) -> None:
        self.clock -= 0.5
        self.records.append({"timestamp": at(self.clock), "type": record_type, "payload": payload})

    def _item(self, body: dict) -> None:
        self._add("event_msg", {"type": "item_completed", "thread_id": self.id, "turn_id": f"t{self.turn}", "item": body})

    def ask(self, prompt: str) -> Chat:
        self.turn += 1
        self._add("event_msg", {"type": "task_started", "turn_id": f"t{self.turn}"})
        self._item({"type": "UserMessage", "content": [{"type": "text", "text": prompt}]})
        return self

    def think(self, summary: str) -> Chat:
        self._item({"type": "Reasoning", "summary_text": [summary]})
        return self

    def run(self, command: str, exit_code: int = 0) -> Chat:
        self._item({"type": "CommandExecution", "command": ["/bin/zsh", "-lc", command], "exit_code": exit_code})
        return self

    def edit(self, *paths: str) -> Chat:
        changes = {f"/workspace/{self.project}/{path}": {"type": "update"} for path in paths}
        self._item({"type": "FileChange", "changes": changes})
        return self

    def decide(self, question: str, options: list[str], chosen: str, reason: str) -> Chat:
        arguments = {"question": question, "options": options, "chosen": chosen, "reason": reason}
        self._item({"type": "McpToolCall", "server": "codex-companion", "tool": "log_decision",
                    "status": "completed", "arguments": arguments})
        return self

    def answer(self, text: str, question: dict | None = None) -> Chat:
        body = {"type": "AgentMessage", "phase": "final_answer", "content": [{"type": "Text", "text": text}]}
        if question:
            body["questions"] = [question]
        self._item(body)
        self._add("event_msg", {"type": "token_count", "info": {
            "total_token_usage": {"input_tokens": 182_000, "cached_input_tokens": 120_000, "output_tokens": 9_400,
                                  "reasoning_output_tokens": 3_100, "total_tokens": 191_400},
            "last_token_usage": {"input_tokens": 61_000, "output_tokens": 1_800, "total_tokens": 62_800},
            "model_context_window": 258_000}})
        self._add("event_msg", {"type": "task_complete", "turn_id": f"t{self.turn}", "duration_ms": 184_000})
        return self

    def write(self, home: Path) -> None:
        folder = home / "sessions" / NOW.strftime("%Y/%m/%d")
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"rollout-{NOW.strftime('%Y-%m-%dT%H-%M-%S')}-{self.id}.jsonl"
        path.write_text("".join(json.dumps(record) + "\n" for record in self.records), encoding="utf-8")
        mtime = (NOW - timedelta(minutes=self.clock)).timestamp()
        os.utime(path, (mtime, mtime))


def demo_chats() -> list[Chat]:
    return [
        Chat(1, "Add watering reminders", "garden-planner", 40)
        .ask("Add watering reminders to the plant detail screen.")
        .think("**Checking how plant schedules are stored**")
        .edit("frontend/src/features/plants/Reminders.tsx", "backend/api/reminders.py")
        .run("make check")
        .answer("**Outcome:** Reminders work on the plant screen; storage is the open question.\n\n"
                "**Next step:** answer: choose where reminders are stored.",
                {"title": "Store reminders on this device only, or sync them to the server?",
                 "options": ["This device only", "Sync to server"]}),
        Chat(2, "Fix plant search ranking", "garden-planner", 95)
        .ask("Search for 'basil' shows thyme first. Fix the ranking.")
        .think("**Comparing prefix and fuzzy scores**")
        .decide("How should exact names rank?", ["Boost exact prefix", "Tune fuzzy threshold"],
                "Boost exact prefix", "Smaller change; keeps typo tolerance")
        .edit("backend/search/ranking.py", "backend/tests/test_ranking.py")
        .run("uv run pytest -q backend/tests/test_ranking.py", 1)
        .edit("backend/search/ranking.py")
        .run("uv run pytest -q")
        .answer("**Outcome:** Exact name matches now rank first; all 48 tests pass.\n\n"
                "**Next step:** none."),
        Chat(3, "Fix recipe import", "recipe-box", 180)
        .ask("Recipe import fails on the new CSV header.")
        .run("make check")
        .edit("app/recipes/importer.py")
        .answer("**Outcome:** The importer accepts both header formats.\n\n"
                "**Next step:** run: `make check` again; the importer changed after the last run."),
        Chat(4, "Upgrade Vite to v6", "weather-widget", 6)
        .ask("Upgrade Vite to v6 and fix anything that breaks.")
        .think("**Reading the Vite 6 migration notes**")
        .edit("frontend/package.json", "frontend/vite.config.ts")
        .run("npm run build"),
        Chat(5, "Write offline sync guide", "weather-widget", 60 * 30)
        .ask("Document how the outbox handles conflicts.")
        .edit("docs/SYNC.md")
        .answer("**Outcome:** Added docs/SYNC.md with the conflict flow.\n\n**Next step:** none."),
    ]


def wait_for(url: str) -> None:
    for _ in range(40):
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except OSError:
            time.sleep(0.25)
    sys.exit(f"Server did not start on {url}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        chats = demo_chats()
        for chat in chats:
            chat.write(home)
        (home / "session_index.jsonl").write_text(
            "".join(json.dumps({"id": c.id, "thread_name": c.title}) + "\n" for c in chats), encoding="utf-8")
        server = subprocess.Popen([str(ROOT / ".venv" / "bin" / "codex-companion"), "serve",
                                   "--port", str(PORT), "--codex-home", str(home)])
        try:
            base = f"http://127.0.0.1:{PORT}"
            wait_for(base + "/")
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(channel="chrome")
                page = browser.new_page(viewport={"width": 420, "height": 900}, device_scale_factor=2,
                                        color_scheme="light")
                shots = (("inbox", "/"), ("chat-waiting", f"/?thread={chats[0].id}"),
                         ("chat-done", f"/?thread={chats[1].id}"))
                # Every image gets the tallest page's height so the README images line up.
                heights = []
                for _, path in shots:
                    page.goto(base + path)
                    page.wait_for_timeout(1200)
                    heights.append(page.evaluate("document.documentElement.scrollHeight"))
                page.set_viewport_size({"width": 420, "height": max(heights)})
                for name, path in shots:
                    page.goto(base + path)
                    page.wait_for_timeout(1200)
                    page.screenshot(path=str(OUT / f"{name}.png"))
                    print(f"wrote docs/images/{name}.png")
                browser.close()
        finally:
            server.terminate()
            server.wait()


if __name__ == "__main__":
    main()
