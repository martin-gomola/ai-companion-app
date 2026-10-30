<div align="center">

# Your Turn

### Your agents are fast. You're the queue.

**An inbox that shows which Codex chat needs you, what it did, whether you can trust it, and what
to do next.**

![Local only](https://img.shields.io/badge/Runs-Local%20only-2f7a6b)
![Read-only](https://img.shields.io/badge/Access-Read--only-256356)
![Works with Codex](https://img.shields.io/badge/Works%20with-Codex-56645f)

[Start](#start-in-one-command) · [How it works](#how-it-works) · [Design](#design) ·
[Development](#development)

<img src="docs/images/desktop.png" width="800" alt="Your Turn inbox with a warm header scene, status tabs, and chats grouped into Needs you, Working, and New results">

<sub>Made-up demo chats from <code>make screenshots</code>, not real session data.</sub>

</div>

Coding agents are capable enough now that the slow part is the person running them. I run many
Codex chats in parallel; their answers are long, and with several open it is easy to miss the one
blocked on me. Your Turn answers four questions per chat, at a glance:

| Question | Where the answer is |
| --- | --- |
| Does it need me? | The status (Needs you, Working, or Done) and the Needs you count |
| What happened? | The recap and the files the chat changed |
| Can I trust it? | The checks it ran, with **Check failed** or **Edits unchecked** when they don't cover the latest edit |
| What do I do next? | The next step, with **Open in Codex** to act on it |

- **Local only.** The server listens on `127.0.0.1`. Nothing leaves your machine.
- **Read-only.** It reads the session files Codex already writes and never touches `~/.codex`.
- **No new workflow.** It never starts, answers, or approves anything; you act in Codex.

When an agent asks a question, its chat moves into Needs you within a second:

<img src="docs/images/demo.gif" width="800" alt="A working chat moves into Needs you when its question arrives, then opens beside the inbox with the question and an Open in Codex button">

## Start in one command

You need Codex (desktop app or CLI), Python 3.11+, and [`uv`](https://docs.astral.sh/uv/).

```sh
uvx --from git+https://github.com/martin-gomola/your-turn your-turn install
```

1. It installs the Codex plugin, then starts the inbox on [http://127.0.0.1:8787](http://127.0.0.1:8787).
2. Restart Codex. From then on, agents end each answer with an Outcome, a Next step, and a Recap,
   say which checks they ran, and log their decisions. That is what makes the recaps exact.

Your existing chats appear right away. Next time, run the same command with `serve` in place of
`install` to start only the inbox.

<details>
<summary>Only the inbox, or install from a clone</summary>

| You want | Do this |
| --- | --- |
| Only the inbox, no plugin | Run the command with `serve` instead of `install`. Recaps fall back to the first paragraph of each answer and a guessed next step. |
| The handoff format without the plugin | Paste [docs/agents-snippet.md](./docs/agents-snippet.md) into `~/.codex/AGENTS.md`. Decisions are then not logged. |
| To develop Your Turn | Clone the repo and run `make install`. The plugin then runs from your checkout, and the server starts in the background. If the clone is not at `~/dev/your-turn`, set `YOUR_TURN_REPO` in the environment Codex runs in. |

</details>

It also works in the Codex in-app browser, beside the chat:

<img src="docs/images/in-codex.png" width="800" alt="Mock Codex window with a chat on the left and Your Turn in the in-app browser on the right, showing the chat waiting for an answer and its passing check">

## How it works

Codex writes each chat to a session file under `~/.codex/sessions`. Your Turn follows those files
as they change and turns each chat into a short recap.

| Part | What it does |
| --- | --- |
| Inbox | Groups chats into Needs you, Working, New results, and Earlier. Each count is also a filter. |
| Chat page | The outcome, next step, changed files, checks, decisions, and full timeline. **Open in Codex** jumps to the chat. |
| Alerts | The tab title and favicon show the Needs you count. Desktop notifications are optional. |
| Quiet tag | A working chat silent for two minutes. It may be waiting on an approval or a long command. |
| Check tags | **Check failed** when the latest check failed. **Edits unchecked** when code changed with no test or lint after it. |
| Reminders | **Dismiss reminder** clears a chat from Needs you in this browser. It never answers anything in Codex. |

Recaps come from the agent's final answer:

| If the final answer has | Your Turn shows |
| --- | --- |
| `**Outcome:**`, `**Next step:**`, and `**Recap:**` lines | Those lines as written |
| No handoff lines | The first paragraph as the outcome, and a best-guess next step: Run, Review, or Answer |

The in-app Help page covers statuses, privacy, and troubleshooting.

### Settings

Set the history window in `config.toml` at the repository root, then run `make restart`:

```toml
history_days = 14
```

The inbox shows chats whose session file changed in that many days. Direct chat links still open
older chats.

### Limits

- Recaps are only as good as the agent's final answer. Older chats and agents that skip the handoff
  lines usually show an unknown next step.
- Codex does not log approval requests, so a chat blocked on one shows as Working, then Quiet. Quiet
  never counts toward Needs you, because a long-running command looks the same.

## Design

Every feature has to shorten one of the four questions above; anything else stays out. The UI
borrows from Google Inbox's highlights, Material's large top app bar, Stephen Few's glanceable
dashboards, and Google PAIR's guidance on showing when to trust an AI. The full contract is in
[DESIGN.md](./DESIGN.md).

## Development

| Command | Use it when |
| --- | --- |
| `make install` | First setup, or to update the plugin |
| `make up` | Start the server in the background (`PORT=...` to change from 8787) |
| `make status` | Check whether it is running |
| `make logs` | Follow the server log |
| `make restart` | Pick up code or config changes |
| `make down` | Stop the server |
| `make test` | Run the test suite |
| `make screenshots` | Regenerate the README images from demo chats (needs Google Chrome and ffmpeg) |

| Route | Returns |
| --- | --- |
| `GET /api/inbox` | Recent chats with status, outcome, next step, and check state |
| `GET /api/threads/<id>` | Snapshot of one chat |
| `GET /api/stream?thread=<id>` | Server-sent events when that chat changes; without `thread`, inbox events |

```text
src/yourturn/                 FastAPI server, rollout parser, and MCP server
src/yourturn/static/          Dashboard HTML, CSS tokens, and JavaScript
plugin/                       Codex plugin: manifest, MCP config, your-turn-handoff skill
tests/                        Parser and API tests
scripts/                      Demo-data screenshot and GIF generator for this README
docs/images/                  README images
```

Guides: [Design contract](./DESIGN.md) · [Handoff skill](./plugin/skills/your-turn-handoff/SKILL.md) ·
[Handoff format without the plugin](./docs/agents-snippet.md)

## License

[MIT](./LICENSE). Third-party icons and artwork notes are in [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md).
