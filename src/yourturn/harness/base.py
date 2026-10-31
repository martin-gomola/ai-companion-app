"""Normalized, harness-agnostic session events and the adapter protocols. No I/O here."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol, TypeAlias, runtime_checkable

from yourturn.model import Capabilities, Handoff, SessionRef

# All events are keyword-only so field order never matters to adapters or tests.


@dataclass(frozen=True, slots=True, kw_only=True)
class Meta:
    """Session header: identity, environment and optional git info."""

    ts: datetime | None = None
    session_id: str | None = None
    cwd: str | None = None
    model: str | None = None
    harness: str | None = None
    originator: str | None = None
    cli_version: str | None = None
    git_branch: str | None = None
    git_commit: str | None = None
    git_repo_url: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class TurnStarted:
    """A new agent turn began."""

    ts: datetime | None = None
    turn_id: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class TurnEnded:
    """An agent turn finished (completed, interrupted, failed...)."""

    ts: datetime | None = None
    turn_id: str | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class UserMessage:
    """A prompt from the user."""

    ts: datetime | None = None
    text: str = ""


@dataclass(frozen=True, slots=True, kw_only=True)
class AgentMessage:
    """A message from the agent to the user."""

    ts: datetime | None = None
    text: str = ""


@dataclass(frozen=True, slots=True, kw_only=True)
class CommandRun:
    """A shell command the agent ran. `exit_code` is None while running or unknown."""

    ts: datetime | None = None
    command: str = ""
    exit_code: int | None = None
    duration_ms: int | None = None
    output_tail: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class FilesEdited:
    """One edit/patch application touching `paths`. `ok` is None when the outcome is unknown."""

    ts: datetime | None = None
    paths: tuple[str, ...] = ()
    added: int | None = None
    removed: int | None = None
    ok: bool | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ToolCall:
    """Any other tool invocation (MCP, web search, ...)."""

    ts: datetime | None = None
    name: str = ""
    arguments: str | None = None
    ok: bool | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class Usage:
    """Cumulative token usage as reported by the harness."""

    ts: datetime | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    total_tokens: int = 0


Event: TypeAlias = (
    Meta
    | TurnStarted
    | TurnEnded
    | UserMessage
    | AgentMessage
    | CommandRun
    | FilesEdited
    | ToolCall
    | Usage
)

EVENT_TYPES: tuple[type, ...] = (
    Meta,
    TurnStarted,
    TurnEnded,
    UserMessage,
    AgentMessage,
    CommandRun,
    FilesEdited,
    ToolCall,
    Usage,
)


@runtime_checkable
class EventCursor(Protocol):
    """Incremental reader over one session source.

    `read_new()` returns only events appended since the previous call and must leave a
    partial trailing line unconsumed (it is picked up once complete). `offset` is the
    position (e.g. byte offset) just past the last fully consumed record.
    """

    @property
    def ref(self) -> SessionRef: ...

    @property
    def offset(self) -> int: ...

    def read_new(self) -> list[Event]: ...

    def reset(self) -> None:
        """Rewind to the start so the next `read_new()` replays everything."""
        ...


@runtime_checkable
class HarnessAdapter(Protocol):
    """One harness (codex, claude, cursor): finds sessions, opens cursors, builds handoffs."""

    name: str
    capabilities: Capabilities

    def discover(self, root: Path | None = None) -> Iterable[SessionRef]:
        """Yield sessions under `root` (or the harness's default location)."""
        ...

    def open(self, ref: SessionRef) -> EventCursor:
        """Return a fresh cursor positioned at the start of the session."""
        ...

    def handoff(self, ref: SessionRef, cwd: str | None) -> Handoff:
        """Describe how to resume / open the session; pure, no process spawning."""
        ...
