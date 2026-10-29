---
name: companion-handoff
description: End every turn with the companion handoff (Outcome and Next step lines) and log real decisions with log_decision. Use for every task in Codex, so the user can see at a glance what happened and what they need to do.
---

# Companion handoff

The user runs several Codex chats at once and reads the Codex Companion inbox to see which chats
need them. The inbox shows two lines from your final answer, so start every final answer with them:

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
changed files or test results; the companion reads them from the chat itself.

## Decisions

When you pick between real alternatives (approach, dependency, scope, root cause, fix), call the
`log_decision` tool from the `codex-companion` server with `question`, `options`, `chosen`
(worded as in `options`) and a one-sentence `reason`. Skip routine steps.
