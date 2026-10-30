# Handoff format without the plugin

The `your-turn` plugin ships a skill that asks Codex to start every final answer with `Outcome`
and `Next step` lines, plus a `Recap` line from the second turn on. If you do not want to install
the plugin, paste the block below into an `AGENTS.md` file instead. Use `~/.codex/AGENTS.md` for
all chats, or a repo's `AGENTS.md` for chats in that repo.

The block leaves out the plugin's decision logging, because the `log_decision` tool needs the
plugin's MCP server. Without it, Your Turn still shows the questions Codex asked you.

```markdown
## Your Turn handoff

I run several Codex chats at once and read the Your Turn inbox to see, for each one, whether it
needs me, what happened, whether I can trust it, and what to do next. Start every final answer with
these two lines:

**Outcome:** <one sentence: what is now true, or what you found>
**Next step:** <one of the forms below>

Next step forms:

- `none` when the task is finished and nothing is needed.
- `answer: <the question>` when you need information or a choice.
- `review: <what to look at>` when I should check a diff, report, or result.
- `approve: <the plan or action>` before you do something risky or irreversible.
- `run: <command>` when I have to run something you cannot.

From the second turn of a chat on, add a third line that recaps the whole chat, not just this
turn:

**Recap:** <one or two sentences: the chat's goal, what is settled, what is still open>

Do not repeat the next step in the recap. Then write the details as usual, but keep them short.
Do not repeat the outcome, and do not list changed files or test results.

Before you hand off, run the checks that cover your last code edit. If a check still fails, say so
in the outcome. If you cannot run a check, make the next step `run: <command>`.
```
