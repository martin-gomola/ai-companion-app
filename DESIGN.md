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
- From 1280px wide, for example on a separate monitor, the inbox becomes a full-width board (see
  Board). Below 1280px it is the list described in Inbox.
- The page follows the system light or dark appearance until the user picks one with the sun/moon
  switch in the header. The choice is stored in this browser and applied before the first paint.
- iOS patterns are borrowed where they help scanning: large titles, inset grouped lists, segmented
  filters, disclosure rows, and system colors. Phone-only chrome (tab bars, bottom toolbars above a
  home indicator, swipe actions) is not used.

## Inbox

- The header is a full-width toolbar, as in the Codex window: the "Inbox" title (or the active
  filter's name) on the left, and one bordered group on the right that holds the live connection
  state and the theme switch. The product
  name lives in the window title and footer, not in a separate header line.
- Directly below sits the segmented summary: All, Needs you, Working, and New. It stays pinned while
  the list scrolls. Each segment shows its count and is also the filter for that status, so the
  header doubles as the overview. The selected segment is filled. Segments wrap to a second line
  rather than break a word.
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
- Clicking a card opens that chat in a panel on the right. The open chat is the priority, so the
  panel takes most of the width (content capped at the reading width) and the board collapses into
  the phone list beside it: a 320–400px column with sections stacked, empty sections omitted, and
  its own scroll. The panel shows the chat page content under its own title, subtitle, and Close
  button. The open chat is marked current with a 6% accent-tinted row and an accent title, scrolled into view.
  Closing the panel restores the columns. The panel is a bookmarkable `/?open=<id>` URL, browser back closes it, and
  Escape closes it and returns focus to the card. Modified clicks (new tab or window) still open the
  full chat page. Narrowing the window below 1280px with a panel open switches to the chat page.
## Chat page

- A sticky row with the back link on the left and the same live-state and theme group on the
  right. Below it, a large title (the chat name)
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
- What happened shows the latest `Recap:` (Chat so far) above the latest turn's outcome (Latest
  turn), each with a small label; with no recap it is the outcome alone, and while a turn runs it
  keeps showing the last recap.
- More, as disclosure rows: Earlier turns, Files changed, Activity (with Key steps and Everything
  filters), and Session details. Files changed is the session's final set of edited files, most
  recently changed first, without per-turn history (long chats made turn lists noise); it appears
  only when earlier turns edited files, because Changes and checks already lists the latest turn's
  files. Session details shows the latest reported
  token totals and last-request usage, model and effort from the latest turn, provider, branch, client, working directory, and report
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

- Palette: the companion sits next to Codex, so neutrals use the Codex catalog themes: GitHub
  Light (`#f6f8fa` page, `#ffffff` surfaces) and VS Code+ (`#171717` page, `#1e1e1e` surfaces).
  The accent is Slido Forest Green `#198038` (Slido Brand Guidelines 1.0): accent text in light
  and every filled control with white text (5.02:1). The guide has no dark theme, so dark accent
  text uses the Slido tertiary Green bright `#42a65f` (5.44:1 on the surface). New and passed
  results use Slido Teal (`#28726d` light, `#22aba2` dark) so they never read as the accent.
  Removed red marks failures and skill purple marks working. Danger text in dark uses `#f48771`
  while `#fa423e` stays the glyph fill. Forest Green on the grey fill is 4.47:1, so hover on
  accent-text buttons uses a 6% green tint instead. GitHub Light has no orange,
  so needs-you uses `#bc4c00`, GitHub's severe orange.
- Windows follow Codex: opaque, flat surfaces with a 1px hairline edge and no shadow, blur, or
  ambient backdrop. The toolbar is the surface color with a bottom border. Pages sit on the grey
  page color. On the board, the inbox is the grey sidebar and an open chat is the white main pane,
  separated by a 1px border. Increased contrast strengthens every separator and edge.
- The summary segments and the chat toolbar stay pinned over scrolling content.
- Status color roles: orange for needs you, purple for working, teal for new or passed results,
  red for failures and stopped turns, grey for history. Forest Green is the accent for links, the back link,
  selected segments, and Open in Codex. Color always accompanies a label or glyph.
- Pictograms carry the structure so a long chat stays scannable. Every section title starts with a
  tinted icon chip in its role color: What happened (green, message), Changes and checks (teal,
  terminal), Decisions (purple, branch), More (grey); inbox sections use their status color and
  glyph. Disclosure rows lead with a muted icon. Each decision leads with the chosen answer
  (medium weight); the question follows as muted context clamped to two lines (full text in the
  tooltip), then the reason, then a meta line whose purple You or Agent says who decided. No tinted
  answer block, and a leading Markdown heading marker is stripped from answers.
- No colored side stripes on cards, rows, or quotes: that idiom reads as generic generated UI. The
  status card is one surface: for needs you, working, and stopped it takes a 6% tint and a border
  in the status color, with no inner band or divider, so the header reads as part of the card. At
  6% every text and status ink stays at 4.5:1. Open in Codex is the only filled action; Dismissing
  the reminder is a muted 44px bell icon in the card header, as notification mutes work elsewhere:
  a struck-through bell dismisses, a plain bell restores. Its label and tooltip say it only affects
  this browser; after dismissing, a short note says the request is still open in Codex. On phones,
  disclosure-row values move under their label instead of squeezing it.
- Type: the native system font. Large titles for page names, semibold section text, regular body.
  Mono only for commands and paths. Section headers are bold sentence-case text with a muted count.
- Groups and cards use 10px corners and controls 8px; inner shapes stay concentric. Separators are
  inset to the text column. Filled actions (Open in Codex, selected segment and chip) are flat
  accent fills. Controls keep 44px targets even though Codex's own controls are smaller.
- Motion: only the working glyph loops (it is a progress indicator); the needs-you glyph and the
  live dot pulse three times, then rest. When a live update moves a chat to another section or
  reorders a section, a same-document view transition slides the visible rows to their new place;
  updates that change only text re-render without one, so frequent working updates never block
  clicks. Rows hidden in a scrolled column are left unnamed, because view transitions ignore
  ancestor clipping. Page changes (inbox to chat and back) fade the old page and rise the new one
  under a still toolbar; the board panel slides in from the right and out again. Disclosures
  open to their height, chat sections rise in (240ms, 40ms apart), and hover, press, and status
  colors ease over 120ms. Reduced motion skips every transition and animation.
- Readability: metadata is at least 13px (`--text-xs`); only uppercase labels use 12px
  (`--text-label`). The next step reads one size up (17px). Headings balance their lines,
  paragraphs avoid a lone last word, the next step and decision reasons keep a 68ch measure, and
  times, counts, and step totals use tabular figures.

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
