"""Minimal stdio MCP server for the Codex plugin: decision logging.

`log_decision` stores nothing itself. Codex records every MCP call in the chat's rollout file,
and the companion reads decisions back from there, so they always belong to the right chat.
"""

from __future__ import annotations

import json
import sys
from typing import Any, TextIO

from codex_companion import __version__

PROTOCOL_VERSION = "2025-06-18"

TOOLS: list[dict[str, Any]] = [
    {
        "name": "log_decision",
        "description": (
            "Record a decision you made while working, so the user can see it on the companion's decision map. "
            "Call it when you pick between real alternatives (approach, library, scope, fix), not for routine steps."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The choice you faced, phrased as a question."},
                "options": {"type": "array", "items": {"type": "string"}, "description": "Alternatives considered."},
                "chosen": {"type": "string", "description": "The option you picked."},
                "reason": {"type": "string", "description": "One sentence on why."},
            },
            "required": ["question", "chosen"],
        },
        "annotations": {"readOnlyHint": True},
    },
]


def _call(name: str, args: dict[str, Any]) -> str:
    if name == "log_decision":
        return f"Recorded decision: {args.get('chosen', '')}"
    raise ValueError(f"unknown tool: {name}")


def handle(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    if "id" not in message:
        return None
    reply: dict[str, Any] = {"jsonrpc": "2.0", "id": message["id"]}
    params = message.get("params") or {}
    if method == "initialize":
        reply["result"] = {
            "protocolVersion": params.get("protocolVersion", PROTOCOL_VERSION),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "codex-companion", "version": __version__},
        }
    elif method == "ping":
        reply["result"] = {}
    elif method == "tools/list":
        reply["result"] = {"tools": TOOLS}
    elif method == "tools/call":
        try:
            text, error = _call(str(params.get("name")), params.get("arguments") or {}), False
        except ValueError as exc:
            text, error = str(exc), True
        reply["result"] = {"content": [{"type": "text", "text": text}], "isError": error}
    else:
        reply["error"] = {"code": -32601, "message": f"method not found: {method}"}
    return reply


def serve(stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> None:
    for line in stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        reply = handle(message) if isinstance(message, dict) else None
        if reply is not None:
            stdout.write(json.dumps(reply) + "\n")
            stdout.flush()
