from __future__ import annotations

import io
import json
from pathlib import Path

from conftest import OTHER, SUBAGENT, THREAD, event, item, meta, write_rollout
from fastapi.testclient import TestClient

from codex_companion.app import create_app
from codex_companion.mcp import serve


def client(codex_home: Path) -> TestClient:
    return TestClient(create_app(codex_home), base_url="http://127.0.0.1")


def test_inbox_lists_chats_without_subagents(codex_home: Path) -> None:
    write_rollout(codex_home, SUBAGENT, [meta(SUBAGENT, {"subagent": {"thread_spawn": {}}})])
    inbox = client(codex_home).get("/api/inbox").json()

    assert [(entry["id"], entry["status"], entry["title"]) for entry in inbox] == [(THREAD, "waiting", "Fix login")]


def test_needs_you_is_computed_server_side(codex_home: Path) -> None:
    done = [event("2026-10-27T10:00:00Z", {"type": "task_started"})]
    answer = {"type": "AgentMessage", "phase": "final_answer"}
    write_rollout(codex_home, OTHER, [meta(OTHER), *done,
                  item("2026-10-27T10:00:01Z", {**answer, "content": [{"text": "Outcome: Ok\nNext step: review: the diff"}]}),
                  event("2026-10-27T10:00:02Z", {"type": "task_complete"})])
    write_rollout(codex_home, SUBAGENT, [meta(SUBAGENT), *done,
                  item("2026-10-27T10:00:01Z", {**answer, "content": [{"text": "Outcome: Ok\nNext step: none"}]}),
                  event("2026-10-27T10:00:02Z", {"type": "task_complete"})])
    app = client(codex_home)

    inbox = {entry["id"]: entry["needs_you"] for entry in app.get("/api/inbox").json()}
    assert inbox == {THREAD: True, OTHER: True, SUBAGENT: False}
    assert app.get(f"/api/threads/{THREAD}").json()["needs_you"] is True
    assert app.get(f"/api/threads/{SUBAGENT}").json()["needs_you"] is False


def test_stream_sends_the_current_inbox_first(codex_home: Path) -> None:
    polls = iter([False, True])
    app = TestClient(create_app(codex_home, poll_seconds=0, should_stop=lambda: next(polls, True)), base_url="http://127.0.0.1")

    with app.stream("GET", "/api/stream") as response:
        body = response.read().decode()
    head, data = body.split("\n", 2)[:2]
    assert head == "event: inbox"
    assert [entry["id"] for entry in json.loads(data.removeprefix("data: "))] == [THREAD]


def test_thread_state_and_bad_ids(codex_home: Path) -> None:
    app = client(codex_home)

    state = app.get(f"/api/threads/{THREAD}").json()
    assert (state["title"], state["turns"][0]["next_kind"]) == ("Fix login", "answer")
    assert app.get("/api/threads/not-a-thread").status_code == 400
    assert app.get(f"/api/threads/{OTHER}").status_code == 404
    assert app.get("/api/stream?thread=../x").status_code == 400


def test_serves_page_with_policy_and_only_loopback(codex_home: Path) -> None:
    app = client(codex_home)
    page = app.get("/")

    assert page.status_code == 200 and "script-src 'self'" in page.headers["content-security-policy"]
    assert app.get("/assets/app.js").headers["content-type"].startswith("text/javascript")
    assert app.get("/assets/secrets.txt").status_code == 404
    evil = TestClient(create_app(codex_home), base_url="http://evil.example")
    assert evil.get("/").status_code == 400


def test_mcp_server_offers_only_log_decision() -> None:
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "log_decision", "arguments": {"question": "q", "chosen": "A"}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "set_active_thread", "arguments": {}}},
    ]
    out = io.StringIO()
    serve(io.StringIO("".join(json.dumps(r) + "\n" for r in requests)), out)
    replies = {reply["id"]: reply for reply in map(json.loads, out.getvalue().splitlines())}

    assert set(replies) == {1, 2, 3, 4}
    assert [tool["name"] for tool in replies[2]["result"]["tools"]] == ["log_decision"]
    assert replies[3]["result"]["content"][0]["text"] == "Recorded decision: A"
    assert replies[4]["result"]["isError"] is True
