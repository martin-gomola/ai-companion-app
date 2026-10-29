"""Read-only view of a Codex chat, derived from the rollout JSONL file Codex writes per thread."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import threading
import time
from collections import OrderedDict, deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

THREAD_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
ROLLOUT_GLOB = "*/*/*/rollout-*.jsonl"
DECISION_TOOL = "log_decision"
MAX_STEPS = 300
MAX_TURNS = 30
MAX_TEXT = 280
MAX_TAILS = 16
INBOX_TAIL_BYTES = 8 * 1024 * 1024
ATTENTION_DAYS = 14
ACTION_KINDS = {"answer", "review", "approve", "run", "decide", "do"}
# Substring prefilter: rollout files carry multi-megabyte encrypted reasoning lines we never need to parse.
WANTED = (b'"item_completed"', b'"task_started"', b'"task_complete"', b'"turn_aborted"', b'"session_meta"', b'"turn_context"', b'"token_count"')
TOKEN_FIELDS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens", "reasoning_output_tokens", "total_tokens")
SHELL_WRAPPERS = {"-lc", "-c"}
MARKDOWN_EMPHASIS = re.compile(r"\*\*|__|`")
QUESTION_REPLY = re.compile(r"<send_user_message_question_reply>\s*(.*?)\s*</send_user_message_question_reply>", re.DOTALL)
# Codex prepends app and environment context to user messages; it is not what the user typed.
INJECTED_CONTEXT = re.compile(r"<([\w-]*context[\w-]*|user_instructions)\b[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
ANSWER_LABEL = re.compile(
    r"^[\s#>*_-]*(outcome|result|next step|your next step|next|recap)[*_\s]*:[*_\s]*(.*)$", re.IGNORECASE | re.MULTILINE
)
NEXT_KIND = re.compile(r"^(answer|review|approve|run|decide)\b\s*[:\-–]?\s*", re.IGNORECASE)
NOTHING_NEEDED = re.compile(r"^(none|nothing|no action|n/a|—|-)\b", re.IGNORECASE)
CHECK_COMMAND = re.compile(
    r"\b(pytest|vitest|jest|mypy|ruff|eslint|tsc|pyright|go test|cargo (test|clippy)|"
    r"(npm|pnpm|yarn|bun) (run )?(test|lint|check|typecheck|build)|make (check|test|lint|ci|build))\b"
)
HEADING = re.compile(r"#{1,6}\s+.*|(\*\*|__)[^*_\n]+\1:?")
REQUEST = re.compile(r"^(please (provide|share|confirm|send|tell)|can you|could you)\b", re.IGNORECASE)


@dataclass
class Step:
    at: str
    kind: str
    title: str
    detail: str = ""
    status: str = "done"
    turn: int = 0


@dataclass
class Decision:
    at: str
    source: str
    question: str
    options: list[str] = field(default_factory=list)
    chosen: str | None = None
    reason: str = ""
    turn: int = 0


@dataclass
class Check:
    command: str
    exit_code: int | None
    at: str


@dataclass
class Turn:
    index: int
    started_at: str = ""
    ended_at: str = ""
    status: str = "working"
    prompt: str = ""
    outcome: str = ""
    recap: str = ""
    next_kind: str = "unknown"
    next_text: str = ""
    formatted: bool = False
    files: list[str] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)
    edited_after_check: bool = False


@dataclass
class ThreadState:
    id: str
    title: str = ""
    cwd: str = ""
    project: str = ""
    parent_id: str = ""
    subagent: bool = False
    started_at: str = ""
    updated_at: str = ""
    status: str = "idle"
    context_used: int = 0
    context_window: int = 0
    token_usage: dict[str, int] = field(default_factory=dict)
    last_token_usage: dict[str, int] = field(default_factory=dict)
    token_usage_at: str = ""
    model: str = ""
    reasoning_effort: str = ""
    model_provider: str = ""
    git_branch: str = ""
    cli_version: str = ""
    activity: str = ""
    attention_key: str = ""
    version: int = 0
    turns: deque[Turn] = field(default_factory=lambda: deque(maxlen=MAX_TURNS))
    steps: deque[Step] = field(default_factory=lambda: deque(maxlen=MAX_STEPS))
    decisions: list[Decision] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        data = asdict(self)
        data["turns"] = [asdict(turn) for turn in self.turns]
        data["steps"] = [asdict(step) for step in self.steps]
        turn = data["turns"][-1] if data["turns"] else {"next_kind": "unknown", "next_text": ""}
        data["needs_you"] = needs_you({**turn, "status": self.status})
        return data


def _clip(text: str, limit: int = MAX_TEXT) -> str:
    text = " ".join(MARKDOWN_EMPHASIS.sub("", text).split())
    return text if len(text) <= limit else f"{text[: limit - 1]}…"


def _token_counts(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    return {key: value[key] for key in TOKEN_FIELDS if type(value.get(key)) is int and value[key] >= 0}


def _texts(content: object) -> str:
    if not isinstance(content, list):
        return ""
    return "\n".join(part["text"] for part in content if isinstance(part, dict) and isinstance(part.get("text"), str))


def _command(item: dict[str, Any]) -> str:
    command = item.get("command")
    if isinstance(command, list):
        shell = len(command) >= 3 and command[-2] in SHELL_WRAPPERS
        command = command[-1] if shell else " ".join(map(str, command))
    lines = str(command or "").strip().splitlines()
    return _clip(lines[0] if lines else "", 120)


def parse_answer(text: str) -> tuple[str, str, str, bool]:
    """Return (outcome, next_kind, next_text, formatted) from a final answer.

    Answers following the Your Turn handoff format carry `Outcome:` and `Next step:` lines; anything else
    falls back to the first prose paragraph, and to an inferred `answer` step when the reply opens
    with a request or ends with a question.
    """
    labels = {match.group(1).lower(): match.group(2) for match in ANSWER_LABEL.finditer(text)}
    outcome = labels.get("outcome") or labels.get("result")
    step = labels.get("your next step") or labels.get("next step") or labels.get("next")
    if outcome is None:
        parts = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
        flat = [" ".join(line.strip(" -*#>") for line in part.splitlines()).strip() for part in parts]
        body = [line for part, line in zip(parts, flat) if not HEADING.fullmatch(part) and not line.endswith(":")]
        request = ""
        if flat and REQUEST.match(flat[0]):
            request = " ".join(flat[:2]) if flat[0].endswith(":") else flat[0]
        elif flat and flat[-1].endswith("?"):
            request = flat[-1]
        summary = body[0] if body else flat[0] if flat else ""
        return _clip(summary, 200), "answer" if request else "unknown", _clip(request, 200), False
    kind, step_text = "unknown", _clip(step or "", 200)
    if step is not None:
        if NOTHING_NEEDED.match(step_text):
            kind, step_text = "none", ""
        elif match := NEXT_KIND.match(step_text):
            kind, step_text = match.group(1).lower(), step_text[match.end():]
        else:
            kind = "do"
    return _clip(outcome, 200), kind, step_text, True


def parse_recap(text: str) -> str:
    """The whole-chat summary from a `Recap:` line, which the handoff asks for after the first turn."""
    recap = next((m.group(2) for m in ANSWER_LABEL.finditer(text) if m.group(1).lower() == "recap"), "")
    return _clip(recap, 400)


def needs_you(entry: dict[str, Any]) -> bool:
    """A pending question, or a finished turn that recorded an action for the user."""
    if entry["status"] == "waiting":
        return True
    return entry["status"] == "done" and entry["next_kind"] in ACTION_KINDS and bool(entry["next_text"])


def user_text(text: str) -> str:
    return INJECTED_CONTEXT.sub("", text).strip()


class RolloutParser:
    """Folds rollout records into a ThreadState; feed records in file order."""

    def __init__(self, thread_id: str) -> None:
        self.state = ThreadState(id=thread_id)

    def feed(self, record: dict[str, Any]) -> None:
        payload = record.get("payload")
        if not isinstance(payload, dict):
            return
        self.state.version += 1
        at = str(record.get("timestamp", ""))
        if at:
            self.state.updated_at = at
        kind = record.get("type")
        if kind == "session_meta":
            self.state.cwd = str(payload.get("cwd", ""))
            for name in ("model_provider", "cli_version"):
                if isinstance(payload.get(name), str):
                    setattr(self.state, name, _clip(payload[name], 120))
            git = payload.get("git")
            if isinstance(git, dict) and isinstance(git.get("branch"), str):
                self.state.git_branch = _clip(git["branch"], 160)
            self.state.started_at = str(payload.get("timestamp", at))
            source = payload.get("source")
            self.state.subagent = isinstance(source, dict) and "subagent" in source
            self.state.parent_id = str(payload.get("parent_thread_id") or "")
        elif kind == "turn_context":
            self.state.model = _clip(payload["model"], 120) if isinstance(payload.get("model"), str) else ""
            self.state.reasoning_effort = _clip(payload["effort"], 80) if isinstance(payload.get("effort"), str) else ""
        elif kind == "event_msg":
            self._event(at, payload)

    def _turn(self, at: str) -> Turn:
        """The current turn; created lazily when reading starts mid-turn (inbox tail reads)."""
        if not self.state.turns:
            self.state.turns.append(Turn(index=0, started_at=at))
            self.state.status = "working"
        return self.state.turns[-1]

    def _step(self, at: str, kind: str, title: str, detail: str = "", status: str = "done") -> None:
        self.state.steps.append(Step(at, kind, _clip(title), _clip(detail), status, self._turn(at).index))
        if kind not in {"turn", "user"}:
            self.state.activity = _clip(title, 120)

    def _pending(self) -> list[Decision]:
        return [d for d in self.state.decisions if d.source == "asked" and d.chosen is None]

    def _attention(self, at: str, kind: str, content: object) -> None:
        # Event identity survives tail reads; usage updates and file mtimes do not identify a new request.
        value = json.dumps([self.state.id, at, kind, content], sort_keys=True, ensure_ascii=False)
        self.state.attention_key = hashlib.sha256(value.encode()).hexdigest() if at else ""

    def _event(self, at: str, payload: dict[str, Any]) -> None:
        state = self.state
        event = payload.get("type")
        if event == "task_started":
            state.attention_key = ""
            if state.turns and not state.turns[-1].ended_at:
                state.turns[-1].ended_at, state.turns[-1].status = at, "interrupted"
            index = state.turns[-1].index + 1 if state.turns else 1
            state.turns.append(Turn(index=index, started_at=at))
            state.status = "working"
            self._step(at, "turn", f"Turn {index} started")
        elif event in ("task_complete", "turn_aborted"):
            turn = self._turn(at)
            turn.ended_at = at
            if event == "turn_aborted":
                turn.status = "interrupted"
                self._step(at, "turn", f"Turn {turn.index} stopped", str(payload.get("reason", "")), "failed")
            else:
                pending = [d for d in self._pending() if d.turn == turn.index]
                turn.status = "waiting" if pending else "done"
                if pending and turn.next_kind in ("unknown", "none"):
                    turn.next_kind, turn.next_text = "answer", pending[0].question
                duration = payload.get("duration_ms")
                seconds = round(duration / 1000) if isinstance(duration, (int, float)) else 0
                self._step(at, "turn", f"Turn {turn.index} finished", f"{seconds}s" if seconds else "")
            state.status = turn.status
        elif event == "token_count":
            info = payload.get("info")
            if not isinstance(info, dict):
                return
            total = _token_counts(info.get("total_token_usage"))
            last = _token_counts(info.get("last_token_usage"))
            if total:
                state.token_usage, state.token_usage_at = total, at
            if last:
                state.last_token_usage = last
                if "total_tokens" in last:
                    state.context_used = last["total_tokens"]
            window = info.get("model_context_window")
            if type(window) is int and window >= 0:
                state.context_window = window
        elif event == "item_completed" and isinstance(payload.get("item"), dict):
            self._item(at, payload["item"])

    def _item(self, at: str, item: dict[str, Any]) -> None:
        turn = self._turn(at)
        kind = item.get("type")
        if kind == "UserMessage":
            self._user(at, turn, _texts(item.get("content")))
        elif kind == "AgentMessage":
            text = _texts(item.get("content"))
            if item.get("phase") == "final_answer":
                turn.outcome, turn.next_kind, turn.next_text, turn.formatted = parse_answer(text)
                turn.recap = parse_recap(text)
                self.state.attention_key = ""
                if turn.next_kind not in {"unknown", "none"} and turn.next_text:
                    self._attention(at, turn.next_kind, text)
                self._step(at, "answer", turn.outcome or text)
            else:
                self._step(at, "message", text)
            for question in item.get("questions") or []:
                if not isinstance(question, dict):
                    continue
                self._attention(at, "question", question)
                options = [str(option) for option in question.get("options") or []]
                title = _clip(str(question.get("title", "")))
                self.state.decisions.append(Decision(at, "asked", title, options, turn=turn.index))
                self._step(at, "question", title, " · ".join(options), "waiting")
        elif kind == "Reasoning":
            summary = " ".join(item.get("summary_text") or [])
            if summary:
                self._step(at, "thinking", summary)
        elif kind == "CommandExecution":
            self._command(at, turn, item)
        elif kind == "FileChange":
            changes = item.get("changes")
            paths = list(changes) if isinstance(changes, dict) else []
            turn.files.extend(path for path in paths if path not in turn.files)
            turn.edited_after_check = turn.edited_after_check or bool(turn.checks)
            noun = "file" if len(paths) == 1 else "files"
            self._step(at, "edit", f"Edited {len(paths)} {noun}", ", ".join(Path(p).name for p in paths))
        elif kind == "McpToolCall":
            if item.get("tool") == DECISION_TOOL:
                self._decision(at, turn, item.get("arguments") or {})
            else:
                failed = item.get("status") not in ("completed", None)
                self._step(at, "tool", f"{item.get('server')} · {item.get('tool')}", status="failed" if failed else "done")
        elif kind == "SubAgentActivity" and item.get("kind") == "started":
            self._step(at, "agent", f"Sub-agent started: {item.get('agent_path') or item.get('agent_thread_id')}")
        elif kind == "ContextCompaction":
            self._step(at, "turn", "Context compacted")

    def _user(self, at: str, turn: Turn, raw: str) -> None:
        text = user_text(raw)
        if not text:
            return
        pending = self._pending()
        match = QUESTION_REPLY.search(text)
        if match is None:
            for decision in pending:
                decision.chosen = _clip(text, 120)
            turn.prompt = turn.prompt or _clip(text, 160)
            self._step(at, "user", "You", text)
            return
        try:
            replies = json.loads(match.group(1))
        except json.JSONDecodeError:
            replies = []
        for reply in replies if isinstance(replies, list) else []:
            if not isinstance(reply, dict):
                continue
            question, answer = _clip(str(reply.get("question", ""))), _clip(str(reply.get("answer", "")), 120)
            decision = next((d for d in pending if d.question == question), pending[0] if pending else None)
            if decision is not None:
                decision.chosen = answer
                pending.remove(decision)
            turn.prompt = turn.prompt or f"Answered: {answer}"
            self._step(at, "user", f"You answered: {answer}", question)

    def _command(self, at: str, turn: Turn, item: dict[str, Any]) -> None:
        command = _command(item)
        exit_code = item.get("exit_code")
        failed = exit_code not in (0, None)
        if CHECK_COMMAND.search(command):
            turn.checks = [check for check in turn.checks if check.command != command]
            turn.checks.append(Check(command, exit_code, at))
            turn.edited_after_check = False
        self._step(at, "command", command, f"exit {exit_code}" if failed else "", "failed" if failed else "done")

    def _decision(self, at: str, turn: Turn, args: dict[str, Any]) -> None:
        options = [str(option) for option in args.get("options") or []]
        decision = Decision(
            at,
            "agent",
            _clip(str(args.get("question", ""))),
            options,
            _clip(str(args.get("chosen", "")), 120),
            _clip(str(args.get("reason", ""))),
            turn.index,
        )
        self.state.decisions.append(decision)
        self._step(at, "decision", decision.question, f"Chose {decision.chosen}")


class RolloutTail:
    """Incrementally follows one rollout file so each poll only parses newly appended lines."""

    def __init__(self, path: Path, thread_id: str, start: int = 0) -> None:
        self.path = path
        self.parser = RolloutParser(thread_id)
        self.offset = start
        self._skip_partial = start > 0
        if start > 0:
            try:
                with path.open("rb") as handle:
                    metadata = json.loads(handle.readline())
                if isinstance(metadata, dict) and metadata.get("type") == "session_meta":
                    self.parser.feed(metadata)
            except (OSError, ValueError):
                pass

    def read(self) -> ThreadState:
        size = self.path.stat().st_size
        if size < self.offset:
            self.parser = RolloutParser(self.parser.state.id)
            self.offset, self._skip_partial = 0, False
        if size <= self.offset:
            return self.parser.state
        # Line by line: rollouts can be hundreds of megabytes and must not be loaded whole.
        with self.path.open("rb") as handle:
            handle.seek(self.offset)
            while self.offset < size:
                raw = handle.readline()
                if not raw.endswith(b"\n"):
                    break
                self.offset += len(raw)
                if self._skip_partial:
                    self._skip_partial = False
                    continue
                if not any(marker in raw for marker in WANTED):
                    continue
                try:
                    record = json.loads(raw.decode("utf-8", errors="replace"))
                except json.JSONDecodeError:
                    continue
                if not isinstance(record, dict):
                    continue
                # One unexpected record must not stop the rest of the file from being read.
                try:
                    self.parser.feed(record)
                except (TypeError, AttributeError, ValueError):
                    continue
        return self.parser.state


def thread_id_of(path: Path) -> str:
    return path.stem[-36:]


def _iso(epoch: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


def _signature(path: Path) -> tuple[int, int]:
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns


class Sessions:
    """Locates rollout files and chat titles under a Codex home directory."""

    def __init__(self, codex_home: Path, scan_ttl: float = 3.0) -> None:
        self.root = codex_home / "sessions"
        self.index = codex_home / "session_index.jsonl"
        self.scan_ttl = scan_ttl
        self._scan: tuple[float, list[Path]] = (0.0, [])
        self._titles: tuple[float, dict[str, str]] = (-1.0, {})
        self._tails: OrderedDict[str, RolloutTail] = OrderedDict()
        self._subagent: dict[Path, bool] = {}
        self._inbox: dict[Path, tuple[tuple[int, int], dict[str, Any]]] = {}
        self._project_db_mtime = -1
        self._project_roots: list[tuple[str, str]] = []
        # Request threads and the event stream share these caches and tails.
        self._lock = threading.RLock()

    def project_name(self, cwd: str) -> str:
        """Match a chat's working directory to Codex's saved project roots when available."""
        state_db = self.root.parent / "state_5.sqlite"
        try:
            modified = state_db.stat().st_mtime_ns
        except OSError:
            return Path(cwd).name
        if modified != self._project_db_mtime:
            self._project_roots = []
            try:
                connection = sqlite3.connect(f"{state_db.as_uri()}?mode=ro")
                try:
                    self._project_roots = sorted(
                        ((root, name) for root, name in connection.execute(
                            "SELECT project_roots.path, projects.name FROM project_roots "
                            "JOIN projects ON projects.id = project_roots.project_id"
                        ) if root and name),
                        key=lambda item: len(item[0]), reverse=True,
                    )
                finally:
                    connection.close()
            except sqlite3.Error:
                pass
            self._project_db_mtime = modified
        for root, name in self._project_roots:
            root = root.rstrip("/")
            if cwd == root or cwd.startswith(root + "/"):
                return name
        return Path(cwd).name

    def rollouts(self) -> list[Path]:
        """All rollout files, newest modification first; cached briefly because there can be thousands."""
        scanned_at, paths = self._scan
        if time.monotonic() - scanned_at > self.scan_ttl:
            found = []
            for path in self.root.glob(ROLLOUT_GLOB):
                try:
                    found.append((path.stat().st_mtime, path))
                except OSError:
                    continue
            paths = [path for _, path in sorted(found, reverse=True)]
            self._scan = (time.monotonic(), paths)
        return paths

    def is_subagent(self, path: Path) -> bool:
        """Sub-agent threads get their own rollout file; session_meta on the first line says so."""
        if path not in self._subagent:
            try:
                with path.open("rb") as handle:
                    meta = json.loads(handle.readline())
                source = meta.get("payload", {}).get("source")
                self._subagent[path] = isinstance(source, dict) and "subagent" in source
            except (OSError, ValueError, AttributeError):
                self._subagent[path] = False
        return self._subagent[path]

    def chats(self, limit: int) -> list[Path]:
        """Newest user-facing chats, skipping sub-agent threads."""
        chats: list[Path] = []
        for path in self.rollouts():
            if len(chats) >= limit:
                break
            if not self.is_subagent(path):
                chats.append(path)
        return chats

    def find(self, thread_id: str) -> Path | None:
        if not THREAD_ID.match(thread_id):
            return None
        for path in self.rollouts():
            if thread_id_of(path) == thread_id:
                return path
        # A chat started since the last cached scan.
        return next(self.root.glob(f"*/*/*/rollout-*-{thread_id}.jsonl"), None)

    def titles(self) -> dict[str, str]:
        try:
            modified = self.index.stat().st_mtime
        except OSError:
            return {}
        if modified != self._titles[0]:
            titles: dict[str, str] = {}
            for line in self.index.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(entry, dict) and entry.get("id"):
                    titles[str(entry["id"])] = str(entry.get("thread_name") or "")
            self._titles = (modified, titles)
        return self._titles[1]

    def inbox(self, limit: int = 30) -> list[dict[str, Any]]:
        """Status and latest-turn summary per chat, parsed from each file's tail only."""
        with self._lock:
            return self._read_inbox(limit)

    def _read_inbox(self, limit: int) -> list[dict[str, Any]]:
        titles = self.titles()
        chats = self.chats(limit)
        entries = [entry for path in chats if (entry := self._entry(path, titles))]
        # Older chats that still need the user stay visible; unchanged files hit the signature cache.
        kept = set(chats)
        cutoff = time.time() - ATTENTION_DAYS * 86400
        for path in self.rollouts():
            if path in kept or self.is_subagent(path):
                continue
            try:
                if path.stat().st_mtime < cutoff:
                    break
            except OSError:
                continue
            kept.add(path)
            entry = self._entry(path, titles)
            if entry and needs_you(entry):
                entries.append(entry)
        for stale in set(self._inbox) - kept:
            del self._inbox[stale]
        return entries

    def _entry(self, path: Path, titles: dict[str, str]) -> dict[str, Any] | None:
        try:
            signature = _signature(path)
        except OSError:
            return None
        cached = self._inbox.get(path)
        if cached is None or cached[0] != signature:
            tail = RolloutTail(path, thread_id_of(path), start=max(0, signature[0] - INBOX_TAIL_BYTES))
            state = tail.read()
            turn = state.turns[-1] if state.turns else None
            pending = next((d for d in reversed(state.decisions) if d.source == "asked" and d.chosen is None), None)
            cached = (signature, {
                "id": state.id,
                "cwd": state.cwd,
                "status": state.status,
                "updated_at": _iso(signature[1] / 1e9),
                "turn_ended_at": turn.ended_at if turn else "",
                "outcome": turn.outcome if turn else "",
                "next_kind": turn.next_kind if turn else "unknown",
                "next_text": turn.next_text if turn else "",
                "question": pending.question if pending else "",
                "attention_key": state.attention_key,
            })
            cached[1]["needs_you"] = needs_you(cached[1])
            self._inbox[path] = cached
        return {**cached[1], "project": self.project_name(cached[1]["cwd"]), "title": titles.get(thread_id_of(path), "")}

    def inbox_fingerprint(self, limit: int = 30) -> str:
        parts = []
        with self._lock:
            chats = self.chats(limit)
        for path in chats:
            try:
                parts.append(f"{path.name}:{_signature(path)}")
            except OSError:
                continue
        return "|".join(parts)

    def state(self, thread_id: str) -> ThreadState | None:
        with self._lock:
            return self._read_state(thread_id)

    def snapshot(self, thread_id: str) -> dict[str, Any] | None:
        """JSON-ready state, serialized before another thread can feed the same tail."""
        with self._lock:
            state = self._read_state(thread_id)
            return state.to_json() if state else None

    def _read_state(self, thread_id: str) -> ThreadState | None:
        path = self.find(thread_id)
        if path is None:
            return None
        tail = self._tails.get(thread_id)
        if tail is None or tail.path != path:
            tail = self._tails[thread_id] = RolloutTail(path, thread_id)
        self._tails.move_to_end(thread_id)
        while len(self._tails) > MAX_TAILS:
            self._tails.popitem(last=False)
        state = tail.read()
        state.title = self.titles().get(thread_id, state.title)
        state.project = self.project_name(state.cwd)
        return state
