from __future__ import annotations

from pathlib import Path

import pytest
from conftest import (
    OTHER,
    SUBAGENT,
    THREAD,
    append,
    command,
    edit,
    event,
    item,
    meta,
    write_rollout,
)

from codex_companion.rollout import RolloutParser, Sessions, parse_answer


def test_folds_a_turn_into_a_summary_steps_and_decisions(codex_home: Path) -> None:
    state = Sessions(codex_home).state(THREAD)

    assert state is not None
    assert (state.title, state.cwd, state.status, state.subagent) == ("Fix login", "/w/repo", "waiting", False)
    assert (state.context_used, state.context_window) == (250, 1000)
    (turn,) = state.turns
    assert (turn.index, turn.status, turn.prompt) == (1, "waiting", "Fix the login bug")
    assert (turn.outcome, turn.formatted) == ("Need input.", False)
    assert (turn.next_kind, turn.next_text) == ("answer", "Ship now?")
    assert turn.files == ["/w/repo/auth.py"]
    assert [(c.command, c.exit_code) for c in turn.checks] == [("uv run pytest -q", 1)]
    assert turn.edited_after_check is True
    kinds = [step.kind for step in state.steps]
    assert kinds == ["turn", "user", "thinking", "command", "edit", "decision", "answer", "question", "turn"]
    agent, asked = state.decisions
    assert (agent.source, agent.chosen, agent.reason) == ("agent", "Handler", "Smaller change")
    assert (asked.source, asked.question, asked.chosen) == ("asked", "Ship now?", None)


def test_later_check_clears_the_stale_flag_and_formatted_answer_sets_next_step(codex_home: Path) -> None:
    sessions = Sessions(codex_home)
    path = sessions.find(THREAD)
    assert path is not None and sessions.state(THREAD) is not None
    reply = '<send_user_message_question_reply>\n[{"question":"Ship now?","answer":"Yes"}]\n</send_user_message_question_reply>'
    append(
        path,
        event("2026-10-27T10:04:00Z", {"type": "task_started"}),
        item("2026-10-27T10:04:01Z", {"type": "UserMessage", "content": [{"text": reply}]}),
        edit("2026-10-27T10:04:02Z", "/w/repo/auth.py"),
        command("2026-10-27T10:04:03Z", "uv run pytest -q", 0),
        item("2026-10-27T10:04:04Z", {"type": "AgentMessage", "phase": "final_answer", "content": [{"text":
             "**Outcome:** Login works again.\n**Next step:** review: the session timeout change\n\nDetails…"}]}),
        event("2026-10-27T10:04:05Z", {"type": "task_complete"}),
    )

    state = sessions.state(THREAD)
    assert state is not None
    assert state.decisions[-1].chosen == "Yes"
    turn = state.turns[-1]
    assert (turn.index, turn.status, turn.prompt) == (2, "done", "Answered: Yes")
    assert (turn.outcome, turn.next_kind, turn.next_text, turn.formatted) == ("Login works again.", "review", "the session timeout change", True)
    assert (turn.edited_after_check, turn.checks[-1].exit_code) == (False, 0)
    assert state.status == "done"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Outcome: Done.\nNext step: none", ("Done.", "none", "", True)),
        ("## Outcome: Shipped\n- **Next step:** run: make deploy", ("Shipped", "run", "make deploy", True)),
        ("**Result:** Found it\n**Next step:** Check the logs tomorrow", ("Found it", "do", "Check the logs tomorrow", True)),
        ("Fixed the bug. Also refactored.\n\nMore.", ("Fixed the bug.", "unknown", "", False)),
    ],
)
def test_parse_answer(text: str, expected: tuple[str, str, str, bool]) -> None:
    assert parse_answer(text) == expected


def test_inbox_skips_subagents_and_reads_only_the_tail(codex_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_rollout(codex_home, SUBAGENT, [meta(SUBAGENT, {"subagent": {"other": "guardian"}})], day="2026/10/28")
    write_rollout(codex_home, OTHER, [meta(OTHER), event("2026-10-28T09:00:00Z", {"type": "task_started"})], day="2026/10/28")
    sessions = Sessions(codex_home, scan_ttl=0)

    inbox = {entry["id"]: entry for entry in sessions.inbox()}
    assert set(inbox) == {THREAD, OTHER}
    assert (inbox[THREAD]["status"], inbox[THREAD]["question"], inbox[THREAD]["title"]) == ("waiting", "Ship now?", "Fix login")
    assert inbox[OTHER]["status"] == "working"

    monkeypatch.setattr("codex_companion.rollout.INBOX_TAIL_BYTES", 200)
    path = sessions.find(THREAD)
    assert path is not None
    append(path, event("2026-10-27T10:05:00Z", {"type": "task_started"}))
    assert {entry["id"]: entry for entry in sessions.inbox()}[THREAD]["status"] == "working"
    assert {entry["id"]: entry for entry in sessions.inbox()}[THREAD]["cwd"] == "/w/repo"


def test_attention_identity_survives_usage_updates_and_tail_reads(codex_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sessions = Sessions(codex_home, scan_ttl=0)
    state = sessions.state(THREAD)
    assert state is not None
    key = state.attention_key
    assert len(key) == 64
    path = sessions.find(THREAD)
    assert path is not None
    append(path, event("2026-10-27T10:05:00Z", {"type": "token_count", "info": {"total_token_usage": {"total_tokens": 999}}}))
    monkeypatch.setattr("codex_companion.rollout.INBOX_TAIL_BYTES", 2000)
    assert sessions.inbox()[0]["attention_key"] == key
    assert sessions.state(THREAD).attention_key == key


def test_new_request_gets_new_identity_even_with_identical_text(codex_home: Path) -> None:
    sessions = Sessions(codex_home, scan_ttl=0)
    old = sessions.inbox()[0]["attention_key"]
    path = sessions.find(THREAD)
    assert path is not None
    append(path, event("2026-10-27T10:06:00Z", {"type": "task_started"}))
    assert sessions.inbox()[0]["attention_key"] == ""
    append(path,
           item("2026-10-27T10:06:01Z", {"type": "AgentMessage", "questions": [{"title": "Ship now?", "options": ["Yes", "No"]}]}),
           event("2026-10-27T10:06:02Z", {"type": "task_complete"}))
    new = sessions.inbox()[0]["attention_key"]
    assert new and new != old
    assert sessions.state(THREAD).attention_key == new


def test_final_action_identity_tracks_full_request_not_clipped_preview() -> None:
    parser = RolloutParser(THREAD)
    prefix = "Outcome: Done\nNext step: review: " + "a" * 400
    parser.feed(item("2026-10-27T10:06:01Z", {"type": "AgentMessage", "phase": "final_answer", "content": [{"text": prefix + "one"}]}))
    old = parser.state.attention_key
    parser.feed(item("2026-10-27T10:06:01Z", {"type": "AgentMessage", "phase": "final_answer", "content": [{"text": prefix + "two"}]}))
    assert old and parser.state.attention_key != old
    parser.feed(item("2026-10-27T10:06:02Z", {"type": "AgentMessage", "phase": "final_answer", "content": [{"text": "Outcome: Done\nNext step: none"}]}))
    assert parser.state.attention_key == ""


def test_reports_latest_usage_snapshot_without_double_counting(codex_home: Path) -> None:
    sessions = Sessions(codex_home)
    path = sessions.find(THREAD)
    assert path is not None
    append(
        path,
        {"type": "turn_context", "payload": {"model": "fixture-model", "effort": "high"}},
        event("2026-10-27T10:06:00Z", {"type": "token_count", "info": {
            "total_token_usage": {"input_tokens": 120, "cached_input_tokens": 80, "output_tokens": 40, "reasoning_output_tokens": 10, "total_tokens": 160},
            "last_token_usage": {"total_tokens": 90}, "model_context_window": 1000,
        }}),
        event("2026-10-27T10:07:00Z", {"type": "token_count", "info": {
            "total_token_usage": {"input_tokens": 200, "cached_input_tokens": 150, "cache_write_input_tokens": 0, "output_tokens": 60, "reasoning_output_tokens": 20, "total_tokens": 260},
            "last_token_usage": {"total_tokens": 0}, "model_context_window": 1000,
        }}),
    )
    state = sessions.state(THREAD)
    assert state is not None
    assert (state.model, state.reasoning_effort) == ("fixture-model", "high")
    assert state.token_usage == {"input_tokens": 200, "cached_input_tokens": 150, "cache_write_input_tokens": 0, "output_tokens": 60, "reasoning_output_tokens": 20, "total_tokens": 260}
    assert state.token_usage_at == "2026-10-27T10:07:00Z"
    assert state.context_used == 0 and state.last_token_usage == {"total_tokens": 0}


def test_usage_and_session_metadata_ignore_malformed_values() -> None:
    parser = RolloutParser(THREAD)
    parser.feed({"type": "session_meta", "payload": {"cwd": "/w/repo", "model_provider": "fixture-provider", "cli_version": "1.2.3", "git": {"branch": "feature/telemetry"}}})
    for info in (None, [], {"total_token_usage": [1], "last_token_usage": "invalid", "model_context_window": "unknown"}):
        parser.feed(event("2026-10-27T10:08:00Z", {"type": "token_count", "info": info}))
    assert parser.state.token_usage == {} and parser.state.last_token_usage == {}
    parser.feed(event("2026-10-27T10:09:00Z", {"type": "token_count", "info": {
        "total_token_usage": {"input_tokens": -1, "cached_input_tokens": True, "output_tokens": "12", "total_tokens": 0, "unknown_field": 42},
        "last_token_usage": {"total_tokens": False}, "model_context_window": -1,
    }}))
    assert parser.state.token_usage == {"total_tokens": 0}
    assert parser.state.last_token_usage == {} and parser.state.context_window == 0
    assert (parser.state.model_provider, parser.state.cli_version, parser.state.git_branch) == ("fixture-provider", "1.2.3", "feature/telemetry")
    parser.feed({"type": "turn_context", "payload": {"model": "first-model", "effort": "high"}})
    parser.feed({"type": "turn_context", "payload": {"model": "second-model"}})
    assert (parser.state.model, parser.state.reasoning_effort) == ("second-model", "")


def test_rejects_non_thread_ids(codex_home: Path) -> None:
    sessions = Sessions(codex_home)
    assert sessions.find("../../etc/passwd") is None
    assert sessions.find("*") is None
