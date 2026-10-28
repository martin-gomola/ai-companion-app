# Design

## Authority and product

Active local design contract, revised 2026-10-28 from the user's supplied dashboard and component references.
The user explicitly replaced the previous teal, floating-card visual direction.

Codex Companion helps an engineer scan parallel chats, identify which need attention, read the latest
outcome and next step, then open that chat in Codex. It remains a read-only local dashboard.

## Reference adaptation and composition

The dashboard references established grouped work surfaces and semantic status colors. The later
productivity-composer references refine the material system: a cool neutral canvas, opaque paperlike
panels, fine edge definition, restrained elevation, compact controls, and a clear graphite action.
These mechanisms support the companion's inbox and read-only chat flow. The email-specific recipient,
formatting, attachment, and sending controls are reference content rather than companion requirements.

The prior inbox repeated a floating card for every chat, repeated the project name under each title,
and used uppercase status pills. Recoloring that structure would retain its visual noise.
The replacement gives each project one surface and separates its chats with quiet dividers.

## Flow and information hierarchy

- Inbox: header with theme switch and live connection; status shortcuts for Needs you, Working,
  and unseen New results from the last 24 hours; then collapsible project groups. A shortcut opens
  its chat directly when there is one match. Multiple matches use a bookmarkable status-filtered
  view with matching projects expanded, a selected shortcut, and All recent chats recovery.
  Empty status views explain that no chats match. Counts cover the recent inbox window: the server
  loads the 30 most recently updated chats, plus older chats from the last 14 days that still need
  the user. This is not a full-account attention audit.
  Needs you includes pending questions and finished replies with an explicit recorded next action.
  Reading a chat does not imply that the action was completed. These chats are not also counted as
  unseen New results; source execution status remains unchanged.
- Each project shows its name, chat count, highest-priority activity state, and disclosure indicator.
  Projects needing attention open initially. User disclosure choices and keyboard focus survive
  live inbox updates. Projects and chats prioritize waiting, working, unseen results, then history.
  The initial project preview contains three chats, or all active/unseen chats when there are more.
  Remaining older chats use an Earlier chats disclosure whose open state and focus survive updates.
- Chat rows show a circular status pictogram, title, time, short outcome/question, and plain status.
  Questions get two preview lines; other outcomes get one. Open the row for full available detail.
- Chat detail: back navigation and connection/theme controls, full-width title, one status component
  containing the latest update, labelled context metadata, recorded next action, and a compact
  Open in Codex link in its header; then changes/checks, decisions, earlier turns, and activity.
  Working state omits the redundant next-step placeholder. Loading and missing chats hide the handoff.
  Recorded options remain plain read-only lists, not apparent response buttons.
  While working, the main summary names the latest recorded step type rather than exposing shell
  commands. This line uses a compact pictogram badge: blue commands/updates, green file changes,
  amber questions, and purple reasoning/tools or an unreported step. The working fallback rotates
  its activity arc; a recorded command does not imply that command is still executing. Completed
  outcomes remain plain prose rather than inheriting the badge. Reduced motion removes the rotation.
  A Recorded activity disclosure contains the available source title, including command
  text. It uses only this turn's steps; a new turn must not display the previous turn's activity.
  Recorded activity starts expanded on page load. A user's collapse choice survives subsequent
  updates; new activity does not force the disclosure open again.
  One Activity and changes terminal below the status card combines recorded activity, changed files,
  and check results. Commands reuse the command/path/flag/string highlighting; other recorded activity
  uses readable plain text on that terminal surface. File lists start expanded and replace redundant
  Edited N files activity summaries. A command already listed as a check is not repeated above it.
  Commands wrap and use 16px monospace on phones; highlighting preserves recorded text as inert text.
- The status component's expandable system bar combines a project code pill, last-event age,
  reported session tokens, and context percentage. Its disclosure exposes exact input/cached/output/
  reasoning totals, last-request usage, model/effort, session provider, recorded branch, client, working
  directory, and report time. Counts come from the latest valid token_count snapshot, never a sum of
  snapshots. Cached input and reasoning are included in parent counts. Unknowns remain unreported;
  a reported zero remains zero. Context is the last reported request total relative to the model window.
  Model/effort follow the latest turn context; branch/client are recorded session metadata.
  The native disclosure keeps its open state and focus across live data updates.
  Session usage is reported telemetry rather than a bill or account-quota meter. Rate-limit snapshots
  found in rollouts are not presented as current account limits.
- The status panel uses a uniform frosted-glass surface with backdrop blur, a fine edge, and a quiet
  inner highlight, replacing the state-to-white fading gradient. The base surface stays opaque when
  blur is unsupported or reduced transparency is requested. Colored facts remain opaque for stable
  text contrast. It shares the inbox's entry motion. Its Working pictogram
  rotates continuously without restarting on updates; Needs you pulses twice on state entry.
  Expanded session facts use padded tiles: purple usage, blue context/workspace, and green runtime
  configuration. Color groups supplement explicit labels and do not imply task completion. Values
  use 14px monospace with wrapping; the grid reflows from three columns to one. User-triggered session
  expansion reveals its facts over 180ms; reduced motion removes all effects.
- Filtered-list navigation retains its originating status in chat links and the in-app Back link.
  The chat summary uses a status pictogram; context usage is labelled secondary text, never a task
  progress ring. The primary handoff explicitly opens the full chat in Codex because companion text
  is a bounded recap. Missing next actions are described without exposing answer-format mechanics.
  A missing check exit code is labelled Exit not reported and receives an uncertainty warning;
  it must not be presented as failed, passed, or still running without supporting evidence.
- A pending question appears in the next-step region rather than duplicating it as a decision.
- Completed decisions use a paired chat-bubble template: a left-aligned question, then a right-aligned
  recorded answer labelled Agent decision or Your answer. The answer contains its optional rationale
  and a collapsed disclosure for other options. Bubble direction groups the exchange; explicit labels
  identify the recorded roles without implying a live conversation. Regular-weight text wraps within
  padded, width-bounded bubbles. Historical alternatives must not resemble active choice buttons.
  Only three recent decisions are expanded initially; older decisions live in a counted native
  disclosure. Questions include the recorded turn and local timestamp when available. Decision keys
  use source identity and position in the append-only source list; unchanged records retain their DOM
  nodes and selected text. Other-options expansion and keyboard focus survive record updates and
  moves into earlier history. A focused decision moved into history keeps that history open.

## Canonical visual system

`src/codex_companion/static/tokens.css` owns all colors, typography, spacing, radii, and motion tokens.
`app.css` consumes those tokens. No new UI library, remote font, or image dependency is required.

- Light: cool grey canvas, white work surfaces, charcoal text, and established olive, purple, and amber
  semantic accents. Dark: graphite canvas, slate panels, high-contrast text, and the same status roles.
- Type: native system sans-serif with platform fallbacks; sentence-case headings, readable body, quieter
  unboxed metadata. Mono remains reserved for commands and file paths.
  Long instructions and decision questions use regular weight with a 1.6 line height; short headings
  and controls use medium weight. Avoid bold paragraph blocks.
- Surface boundaries come from tone, fine panel borders, and restrained elevation. Corners use 8px
  for controls, 12px for panels, and 16px for larger surfaces. Repeated chat rows have no shadow.
  Circular icons are supplementary to text status, never the sole status signal.
  Chat hover/focus surfaces retain 12px horizontal content padding. Their inset dividers align with
  the project header content. Preview and timestamp text target at least 7:1 contrast on row surfaces.
- The external Codex handoff uses the graphite action/on-action token family. Primary/green tokens
  continue to express selected states, unread results, recorded answers, and positive/navigation cues. The consolidated
  status component uses the standard work surface, with its status badge and handoff aligned in the header.
- Changes and checks use a scoped dark terminal surface in both app themes, inspired by
  [Sonokai Andromeda](https://github.com/sainnhe/sonokai/blob/master/autoload/sonokai.vim).
  Terminal tokens live in tokens.css: green executables/success, cyan paths and filenames, purple
  flags, yellow quoted text/unreported results, and red operators/failures. Muted directory text uses
  a brighter adaptation for contrast. Highlighting is a presentation hint, not shell parsing; every
  source character remains selectable inert text. Commands wrap; result labels preserve status
  meaning without relying on color. The file disclosure remains a native keyboard-accessible control.
- Status shortcuts use amber, purple, and green surfaces with contrasting role-specific text, including
  zero-count states. A nonempty Working tile uses a stronger purple gradient. Selected filters retain
  a filled state; tile labels are never underlined. Empty badges use outlined dashed frames and counts
  rather than suggesting active work. Status icons remain visible at the narrowest supported width.
- The inbox has a quiet blue canvas gradient. Project headers use a state-tinted wash; ordinary folder
  badges use blue outlined rounded squares. Active badges keep their established status colors.
- Inbox uses a 320ms appearance for newly inserted projects and staggered status-tile entrances,
  a small pictogram hover response for fine pointers, and 120ms disclosure-chevron transitions.
  User-triggered project expansion reveals its chat list over 180ms. Working tile pictograms rotate
  while nonempty; attention pictograms pulse twice. Existing project cards do not replay their
  appearance on live updates. Reduced motion removes animations and hover transforms.
- Project attention badges use the question pictogram and two gentle pulses on state entry (2.4s).
  Working badges use the activity pictogram and rotate while active (1.4s per cycle). Their phase survives live
  rerenders; unchanged states do not restart the cue. Text, badge frames, and click targets stay fixed.
- Icon hierarchy follows attention: waiting uses filled amber, working filled purple, and unseen
  results filled green. Completed history, ordinary project folders, and zero-count shortcuts use
  neutral outlined circles. Labels and distinct symbols carry the same meaning without color.
  Strong badge glyphs use the surface token as their contrasting foreground in each theme.
  Selected shortcut badges retain a contrasting ring against the selected tile background.
  A filled new-result badge means an unread response, not verified success or approval.

## Responsive and accessibility contract

- Supported layout: 320px through desktop, reading column capped at 52rem.
- The inbox uses a compact single-row header. The product caption sits inline on wide screens and
  is omitted in compact panes. Theme and connection share one utility frame with equal 44px heights;
  the theme glyph is 16px, with a 44px hit area. Enlarged text may wrap instead of clipping controls.
- Overview tiles reflow with available text space. Headers and project labels wrap without hiding
  controls. Chat titles occupy the full header width on detail pages.
- No fixed overlay or competing scroll region. The page owns scrolling.
- Native details provide keyboard disclosure. Links navigate; the theme switch is a named button.
  Visible focus and controls at least 2.75rem tall remain required.
- Reuse the SVG sprite for section/action labels: projects, recorded activity, changes/checks,
  decisions, earlier turns, activity history, and next actions. Latest-step and recorded-activity
  symbols follow the recorded kind. Question, agent, and user symbols distinguish decision roles.
  Text labels remain visible; supplementary icons are hidden from assistive technology. Native
  disclosures retain a separate rotating chevron, and label updates preserve their focusable node.
- Normal text requires 4.5:1 contrast; large text and essential non-text indicators require 3:1.
  Faint tokens are decoration only. Reduced motion disables animation and transition effects.
- Reachable states: loading, live/offline, empty inbox, long labels, waiting/working/done/stopped,
  missing chat, known/unknown next steps, passed/failed/stale checks, and expanded disclosures.
- At phone widths, explanatory text in decision rationale, historical options/turns, next steps,
  and the session note uses 16px with relaxed line height. Short labels and timestamps stay compact.

## Delivery checks

Run the repository tests, JavaScript syntax and whitespace checks, and the ux-design delivery helper.
Render inbox and representative finished/waiting chats in both themes at phone, intermediate,
landscape, and desktop sizes. Inspect text contrast, overflow, focus, collapse behavior, 200% text,
reduced motion, empty/long-content fixtures, and offline feedback.

Current verification evidence and any gaps are reported with the implementation delivery. Browser
checks provide evidence for the tested Chromium engine, not physical-device or Safari certification.

Dated verification records live in [docs/verification.md](./docs/verification.md).
