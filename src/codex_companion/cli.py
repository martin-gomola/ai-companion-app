"""`codex-companion serve` runs the dashboard; `codex-companion mcp` is the plugin's MCP server."""

from __future__ import annotations

import argparse
import os
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="codex-companion")
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve", help="Run the dashboard on localhost")
    serve.add_argument("--port", type=int, default=8787)
    serve.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")))
    commands.add_parser("mcp", help="Run the stdio MCP server used by the Codex plugin")
    args = parser.parse_args(argv)

    if args.command == "mcp":
        from codex_companion.mcp import serve as serve_mcp

        serve_mcp()
        return

    import uvicorn

    from codex_companion.app import create_app

    print(f"Codex companion on http://127.0.0.1:{args.port}")
    uvicorn.run(create_app(args.codex_home), host="127.0.0.1", port=args.port, log_level="warning")
