---
name: your-turn-handoff
description: End every turn with the Your Turn handoff (Outcome and Next step lines), run checks after your last code edit, and log real decisions with log_decision. Use for every task in Codex, so the user can see at a glance what happened and what they need to do.
metadata:
  version: "0.2.0"
---

# Your Turn handoff

The user runs several Codex chats at once and reads the Your Turn inbox to answer four questions
about each one: does it need me, what happened, can I trust it, and what do I do next. The inbox
shows two lines from your final answer, so start every final answer with them:

```
**Outcome:** <one sentence: what is now true, or what you found>
**Next step:** <one of the forms below>
```

`Next step` forms:

- `none` when the task is finished and nothing is needed.
- `answer: <the question>` when you need information or a choice.
- `review: <what to look at>` when the user should check a diff, report, or result.
- `approve: <the plan or action>` before you do something risky or irreversible.
- `run: <command>` when the user has to run something you cannot.

From the second turn of a chat on, add a third line that recaps the whole chat, not just this turn,
so the user can pick it up after time away:

```
**Recap:** <one or two sentences: the chat's goal, what is settled, what is still open>
```

Do not repeat the next step in the recap.

Then write the details as usual, but keep them short. Do not repeat the outcome. Do not list
changed files or test results; Your Turn reads them from the chat itself.

## Checks

Your Turn tags a chat **Edits unchecked** when code changed and no test, lint, type check, or build
ran after the last edit, and **Check failed** when a check's latest run failed. Before you hand off:

- After your last code edit, run the checks that cover it.
- If a check still fails, say so in the outcome.
- If you cannot run a check, make the next step `run: <command>`.

## Decisions

When you pick between real alternatives (approach, dependency, scope, root cause, fix), call the
`log_decision` tool from the `your-turn` server with `question`, `options`, `chosen`
(worded as in `options`) and a one-sentence `reason`. Skip routine steps.
