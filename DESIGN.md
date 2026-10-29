# Design

## Authority and product

Active local design contract, revised 2026-10-29. It replaces the earlier project-card dashboard
with an attention list adapted from iOS grouped lists. The earlier direction is recorded in
[docs/verification.md](./docs/verification.md).

Codex Companion helps an engineer who runs several Codex chats see which chats need them, what each
one produced, and what to do next, then open that chat in Codex. It is a read-only local web page,
usually open in a narrow browser window beside the Codex app. It is not a native app and has no
Codex controls.

## Environment

- A browser pane from 320px wide to desktop, reading column capped at 52rem. Pointer, keyboard, and
  touch all work; nothing depends on hover.
- From 900px wide, for example on a separate monitor, the inbox becomes a full-width board (see
  Board). Below 900px it is the list described in Inbox.
- The page follows the system light or dark appearance. There is no in-page theme switch.
- iOS patterns are borrowed where they help scanning: large titles, inset grouped lists, segmented
  filters, disclosure rows, and system colors. Phone-only chrome (tab bars, bottom toolbars above a
  home indicator, swipe actions) is not used.

## Inbox

- A sticky translucent header holds the large "Inbox" title, the live connection state, and a
  segmented summary: All, Needs you, Working, and New. Each segment shows its count and is also the
  filter for that status, so the header doubles as the overview. The selected segment is filled.
  Filters are bookmarkable `/?status=` links.
- The All view is one inset grouped list split into sections, in this order: Needs you, Working,
  New results, then Earlier. Empty sections are omitted. Needs you, Working, and New results show at
  most five chats each; a longer section ends with a "Show all N" row that opens its filter. Earlier
  lists the rest of the recent window.
- A filtered view shows every matching chat in one section, with an explanatory empty state.
- Counts cover the inbox window: the 30 most recently updated chats, plus older chats from the last
  14 days that still need the user. This is not a full-account attention audit.
- Needs you means a pending question, or a finished turn that recorded an action for the user. The
  server computes this as `needs_you`. Reading a chat does not complete the action. A dismissed
  reminder moves the chat to Earlier with a "Reminder dismissed" tag in this browser only.
- New results are unseen finished turns from the last 24 hours that do not need the user. Stopped
  turns are never new results.
- A row shows a circular status glyph, the chat title, its age, a short request or outcome (two
  lines when it needs the user, one otherwise), and a meta line with the action tag (Answer, Run,
  Review, ...), New when unseen, and the project name. A chevron marks it as navigation. Rows are at
  least 44px tall and the whole row is the link.
- Filtered chat links keep their return scope; the chat page's back link returns to it.

## Board

- The same header, summary segments, and sections, laid out as a read-only kanban: one column each
  for Needs you, Working, New results, and Earlier, always in that order and always present, with an
  empty placeholder when a column has no chats. Columns show every chat as a separate card and
  scroll on their own; the page itself does not scroll. Cards cannot be dragged: a chat's column
  follows its state in Codex.
- A selected segment narrows the board to that one column.
- Clicking a card opens that chat in a panel on the right while the board stays visible. The panel
  shows the chat page content under its own title, subtitle, and Close button. The open card is
  marked as current. The panel is a bookmarkable `/?open=<id>` URL, browser back closes it, and
  Escape closes it and returns focus to the card. Modified clicks (new tab or window) still open the
  full chat page. Narrowing the window below 900px with a panel open switches to the chat page.
- With the panel open, columns keep a minimum width and the board scrolls sideways when needed.

## Chat page

- A sticky header with the back link and the live state. Below it, a large title (the chat name)
  and a subtitle with the project and the time of the last recorded event.
- The status card comes first. Its header shows the status glyph and label and the "Open in Codex"
  action, the only filled accent button on the page. Its body depends on state:
  - Needs you: the action label and the request, with recorded options as a plain read-only list,
    then the reminder control and its note ("Only affects this browser's inbox").
  - Working: this turn's latest recorded step, as its kind (Ran a command, Edited files, ...) and
    its source title, with commands in mono. The glyph rotates. A recorded command does not mean
    it is still running, and a new turn never shows the previous turn's step.
  - Done: "No further action was requested", or "No next action was recorded" when the answer
    skipped the handoff format.
  - Loading and missing chats hide the handoff.
- What happened: the latest turn's outcome, when there is one.
- Changes and checks, as grouped rows: a warning row when files changed after the last check, when
  edits had no check, or when a check has no exit code; one row per check with its command and
  Passed, Failed (exit N), or Exit not reported; and a files row that expands to paths relative to
  the working directory. A missing exit code is never shown as passed, failed, or running.
- Commands and paths use mono and wrap. Command highlighting (executable, path, flag, string,
  operator) is a presentation hint, not shell parsing; every character stays selectable inert text.
- Decisions, as grouped rows: the question, the recorded answer labelled Agent decision or Your
  answer, the optional reason, the recorded turn and local time when available, and a collapsed
  Other options disclosure that must not resemble choice buttons. Three recent decisions show
  directly; older ones sit behind a counted disclosure row. A pending question appears in the status
  card, not here.
- More, as disclosure rows: Earlier turns, Activity (with Key steps and Everything filters), and
  Session details. Session details shows the latest reported token totals and last-request usage,
  model and effort from the latest turn, provider, branch, client, working directory, and report
  time. Counts come from the latest token_count snapshot, never a sum; cached input and reasoning
  are included in their parent counts; context is the last request total relative to the model
  window. Unknowns stay "Not reported" and a reported zero stays zero. Usage is telemetry, not a
  bill or an account quota; rate-limit snapshots are not shown as current account limits.
- Disclosure open state, selected text, and keyboard focus survive live updates. Decision records
  are keyed by source identity and position and keep their DOM nodes while unchanged; a focused
  decision that moves into history keeps that history open.

## Visual system

`src/codex_companion/static/tokens.css` owns every color, type size, spacing, radius, and motion
value; `app.css` only consumes tokens. No UI library, remote font, or image dependency.

- Material: Liquid Glass. A fixed, soft ambient backdrop (blue, pink, and mint glows in light;
  deep navy, plum, and teal in dark) sits behind translucent glass layers: lists, cards, summary
  segments, and capsule controls (back, live state, Close, secondary buttons, chips). Glass uses
  backdrop blur and saturation, a bright inner top edge, and a soft drop shadow. Text contrast is
  computed against glass composited over the darkest and lightest backdrop points.
- Reduced transparency and increased contrast replace glass and backdrop with opaque surfaces;
  increased contrast also strengthens separators and edges. Without backdrop-filter support glass
  becomes nearly opaque.
- The summary segments and the chat back bar float over scrolling content; the bar uses a soft
  fade instead of a hard edge.
- Status color roles: orange for needs you, purple for working, green for new or passed results,
  red for failures and stopped turns, grey for history. Blue is the accent for links, the back link,
  selected segments, and Open in Codex. Color always accompanies a label or glyph.
- Type: the native system font. Large titles for page names, semibold section text, regular body.
  Mono only for commands and paths. Section headers are bold sentence-case text with a muted count.
- Groups and cards use 22px corners; controls are capsules; inner shapes stay concentric.
  Separators are inset to the text column. Filled actions (Open in Codex, selected segment and
  chip) carry a light top edge and an accent glow; status glyphs have a subtle top gloss.
- Motion: the working glyph rotates continuously without restarting on updates, and capsule
  controls shrink slightly while pressed. Reduced motion removes both.

## Accessibility

- Normal text at least 4.5:1, large text and essential glyphs at least 3:1.
- Every control at least 44px tall; links navigate and buttons act. Native details provide
  disclosure with visible focus. Decorative glyphs are hidden from assistive technology; status is
  always also text.
- Text scales to 200% without clipping or horizontal scrolling at 320px. Below 480px, explanatory
  text (requests, outcomes, reasons, commands) uses 16px; short labels and times stay compact.
- In the list and chat page layouts the page owns scrolling: no fixed overlays or nested scroll
  regions besides the sticky header. Only the board scrolls by column and panel.
- Reachable states: loading, live and reconnecting, empty inbox, empty filter, long titles,
  waiting, working, done, stopped, dismissed, missing chat, known and unknown next steps, passed,
  failed, unreported, and stale checks.

## Delivery checks

Run the repository tests and the JavaScript syntax check. Render the inbox and representative
waiting, working, and done chats in both appearances at 320, 390, 430, and 768px, plus 200% text.
Inspect contrast, overflow, focus, disclosure retention, reduced motion, long content, empty states,
and offline feedback.

Current verification evidence and any gaps are reported with the implementation delivery. Browser
checks provide evidence for the tested Chromium engine, not Safari certification.

Dated verification records live in [docs/verification.md](./docs/verification.md).
