# Verification records

Dated delivery checks for the [design contract](../DESIGN.md).

## Unified activity terminal verification on 2026-10-28

- Both themes passed fourteen viewport/text-scale checks, including 320px at 200% text. Verified
  initially expanded files and collapse/focus retention on updates. File-edit summaries were hidden
  when the file list supplied the same information.
- Exercised command-only, files-only, combined command/files, checks-only, empty, non-command prose,
  and a command already present in check results. The terminal remains visible for activity alone
  and hides when there is nothing to show. Duplicate check commands were suppressed.
- JavaScript syntax, whitespace, text contrast, UI delivery checks, and 17 repository tests passed.
  Safari, physical touch, and VoiceOver remain unverified.

## Activity badge verification on 2026-10-28

- Verified fourteen light/dark viewport and text-scale cases, including 320px with 200% text,
  without overflow. Checked seven step types, the working fallback, completed prose, missing-chat
  recovery, and recorded-activity keyboard focus/collapse retention across updates.
- Working fallback rotation retained its animation instance on updates and stopped with reduced
  motion. Command and working text/background pairs passed contrast checks. JavaScript syntax,
  whitespace, UI delivery checks, and 17 repository tests passed. Safari and VoiceOver were not tested.

## Pictogram and default-activity verification on 2026-10-28

- Verified initially expanded activity, user collapse retention through updates, keyboard focus,
  and 44px summary targets. Checked seven activity-kind icons, next-action icons, project/section
  labels, and all SVG references. Decorative label icons are hidden from assistive technology.
- Both themes rendered without horizontal overflow at 320, 390, 640, 768, 844 landscape, and 1280px,
  plus 200% text at 320px. JavaScript syntax, UI delivery, whitespace, and 17 repository tests passed.
  Safari, physical-device touch, and VoiceOver remain unverified.

## Readability follow-up verification on 2026-10-28

- Verified three-decision preview and counted older history with 0, 1, 3, 4, and longer decision
  collections. Unchanged updates preserved open options, keyboard focus, node identity, and selected
  answer text. New decisions moving a focused record into history and changed rationale also retained
  focus and disclosure state.
- Both themes passed overflow checks at 320, 390, 640, 768, 844 landscape, and 1280px, plus 200% text
  at 320px. Phone rationale measured 16px. Verified keyboard history/activity disclosures, focus
  retention, recorded command fidelity, and no stale activity from a previous turn.
- JavaScript syntax, whitespace, contrast checks, and 17 repository tests passed. Physical iOS,
  Safari, and VoiceOver remain unverified.

## Status glass verification on 2026-10-28

- Removed the status gradient. Chromium computed a uniform translucent surface with 18px backdrop
  blur in both themes; emulated Reduce Transparency produced the opaque surface with blur disabled.
- Rechecked the status layout/theme matrix, 200% text, keyboard disclosure/focus retention, working
  animation continuity, and reduced motion. Text contrast passed against the composed glass colors.
  Safari and physical-device appearance remain unverified.

## Status color and motion verification on 2026-10-28

- Both themes rendered at 320, 390, 640, 768, 844 landscape, and 1280px, plus 200% text at 320px,
  without horizontal overflow. Verified keyboard disclosure, visible focus, a 44px target, and
  disclosure/focus retention through a thread rerender.
- Working animation retains its running instance on updates. Verified session-expansion motion,
  reduced-motion suppression, waiting/done/stopped/idle variants, and missing usage versus zero.
  Value/label color pairs passed contrast checks; 14 repository tests passed. Physical iOS, Safari,
  and assistive-technology behavior remain outside this verification.

## Inbox color and motion verification on 2026-10-28

- Rendered light/dark inboxes at 320, 390, 640, 768, 844 landscape, and 1280px, plus 200% text at
  320px. No horizontal overflow or overlap between tile counts and pictograms was observed.
- Verified keyboard/pointer project disclosure, visible focus, expanded-state/focus retention across
  rerenders, and no replayed project entrances on unchanged data. The working tile retained the same
  running animation across updates. A simulated waiting state enabled the two-pulse attention cue.
- Confirmed expansion animation and changing working-icon transforms in normal motion; reduced
  motion removed both. New token foreground/background pairs passed 4.5:1 contrast checks, including
  the brighter working-gradient endpoint. Physical touch, Safari, and VoiceOver remain unverified.

## Decision bubble verification on 2026-10-28

- Rendered paired questions and recorded answers in Chromium in both themes at 320, 390, 768,
  844 landscape, and 1280px, plus 200% text at 320px. No horizontal overflow was observed.
- Verified native Other options disclosure by keyboard and pointer, visible focus, and a 44px
  minimum target. Fixtures covered long prose and URLs, both answer sources, absent answer text,
  pending-question exclusion, and an empty completed-decision section.
- Physical iOS, Safari, and assistive-technology behavior were not checked for this change.
## Verification on 2026-10-28

- Repository suite: 12 tests passed. JavaScript syntax, whitespace, and UX delivery checks passed.
- Rendered Chromium inbox and waiting/detail layouts: 320, 390, 768, 844 landscape, and 1280px;
  light and dark themes had no horizontal overflow or normal-text contrast failures.
- Operated project collapse by keyboard, visible focus, live-update focus retention, theme switch,
  file disclosure, and activity filter selection. Activity filter targets measure 44px high.
- Verified empty inbox, a blocked SSE connection showing Reconnecting, long labels, 200% text,
  reduced motion, done/waiting/working/stopped summaries, passed/failed/stale checks, and missing-chat
  recovery. Temporary fixture content and browser emulation were removed after verification.
- Physical devices, Safari, and assistive-technology navigation were not tested.

## Task-flow review on 2026-10-28

- At 640px, the next project moved from y=2670 to y=771 after moving 19 older chats into a disclosure.
  All active and explicit action-needed chats remain in the initial list, including when there are
  more than three. History expansion and keyboard focus survived a complete inbox rerender.
- Native link navigation verified return from a chat to its originating status-filtered list.
- Fixtures verified recorded review requests count as Needs you, are not double-counted as New,
  and missing check exit results display uncertainty rather than a fabricated execution state.
- Inbox and expanded detail controls passed rendered text-contrast, no-overflow, and 44px target
  checks in both themes at 320, 390, 768, 844 landscape, and 1280px, plus 200% text at 320px.
- Before/after screenshots were captured at matching 640px widths. Touch-event synthesis was
  unsupported by the in-app browser; physical touch gestures, iOS/Safari, VoiceOver, and native
  Codex handoff execution remain unverified. No human usability study was conducted.

## Status consolidation and motion verification on 2026-10-28

- The observed 640px working view uses one 133px status component instead of separate panels
  spanning about 282px. Recorded questions and review instructions remain within the same component.
- Verified working, waiting, review, no-action, unknown-action, stopped, and missing-chat states;
  the handoff occurs once, in the header, and is hidden for unavailable chat data.
- Both themes passed contrast, target-size, and no-overflow checks at 320, 390, 768, 844 landscape,
  and 1280px, plus 200% text. Recorded options are static list items rather than response buttons.
- Project appearance was verified for first insertion and newly arriving projects, with no replay
  for unchanged projects on rerender. Explicitly collapsed projects stayed collapsed, while new
  attention-needed projects opened. Hover changed only the icon transform, leaving link bounds fixed.
- Reduced motion disabled entry animations, hover transforms, and transition duration. The motion
  behavior was checked through rendered styles and animation lifecycle, not a recorded video or
  human preference study. Native handoff and physical-device validation remain outside this evidence.

## Productivity-reference refinement on 2026-10-28

- Adapted the supplied composer references through material hierarchy: cooler neutral canvases,
  opaque work panels with fine borders and low elevation, native system type, tighter corners, and
  a graphite external-handoff action. Existing flow, data scope, and semantic status colors remain.
- Inbox and chat detail passed rendered text-contrast, no-overflow, and 44px target checks in both
  themes at 320, 390, 768, 844 landscape, and 1280px, plus 200% text. Selected status surfaces and
  status-badge boundaries were checked separately. Normal text remained above the 4.5:1 requirement.
- A matching 640px inbox baseline and updated light/dark previews were saved with this chat.
  These are reference adaptations; no pixel-for-pixel copy or native-device validation is claimed.

## Session system bar verification on 2026-10-28

- Inspected session_meta, turn_context, and token_count records from the local rollout before adding
  the supported fields. Input, cached input, cache-write input, output, reasoning output, and total
  are retained only as nonnegative integer counters; snapshots replace prior snapshots.
- Parser tests cover latest-snapshot behavior, explicit zero, missing/malformed counters, model/effort
  refresh, and retention of first-line session metadata during bounded inbox-tail reads.
- The expanded bar passed contrast, target-size, and no-overflow checks in both themes at 320, 390,
  768, 844 landscape, and 1280px. Long metadata and 200% text were checked. Disclosure state and
  keyboard focus survived a full thread rerender; unavailable usage remained distinct from zero.
- Native device, VoiceOver, billing reconciliation, and live account-limit integration remain outside
  this verification. The local server was relaunched with the updated parser before live checks.

## Attention-list redesign on 2026-10-29

- Before (a1ac78d) and after screenshots of the inbox, a Needs you filter, and waiting, working, and
  done chats were rendered in Chromium at 320, 390, and 430px in light and dark, plus 200% text at
  320px and a 1000px desktop window. Demo data added six extra Needs you chats to exercise the
  five-row section cap and Show all.
- No view had horizontal overflow or a control shorter than 44px, including at 200% text. Token
  contrast was computed: text roles are at least 4.5:1 on rows, grouped backgrounds, and pressed rows
  in both appearances; status glyph fills are at least 3:1 against their glyph and the row.
- The inbox at 390px fits five Needs you rows, Show all, Working, and New results in about 1240px,
  against about 1680px for the project-card layout with the same chats.
- The iOS Simulator is not installed, so Safari on iPhone, VoiceOver, and reduced transparency in
  WebKit were not checked.

## Board layout on 2026-10-29

- Rendered in Chromium at 1440x900 and 900x800 in light and dark, with the panel closed and open.
  No view scrolled the page or overflowed sideways, and no control was shorter than 44px.
- Opening a card set `?open=<id>` and marked one card current; opening another card switched the
  panel; Escape closed it and returned focus to the card; browser back reopened it. Narrowing the
  window to 700px or loading `?open=` below 900px moved to the chat page. A selected segment
  showed one column capped at the reading width.
- The list and chat page layouts at 320, 390, and 430px and 200% text were re-checked with no
  overflow or small targets. Safari, VoiceOver, and real multi-monitor setups were not checked.

## Liquid Glass material on 2026-10-29

- Text contrast was computed against glass composited over the darkest and lightest backdrop points
  and with the pressed overlay: every text role is at least 4.5:1 in both appearances. The accent,
  dark purple, and dark red were adjusted to reach that.
- List and chat views at 320, 390, and 430px, 200% text, and the board at 900 and 1440px showed no
  overflow or controls under 44px. With increased contrast emulated, cards rendered opaque with no
  backdrop blur. Reduced transparency and WebKit rendering of backdrop-filter were not emulated.

## Compact header and theme switch on 2026-10-29

- The inbox header is one row (title plus the live and theme capsule) above the summary, which saves
  about 38px against the previous three-row header at 390px. Rendered the inbox, a filter, and
  waiting, working, and done chats at 320, 390, and 430px in both themes, 200% text at 320px, and
  the board and panel at 900 and 1440px: no horizontal overflow and no controls under 44px.
  Summary labels no longer break mid-word at 320px.
- In Chromium the switch followed the system with nothing stored, flipped the theme on click and
  on Enter, kept the choice across a reload and against a system change, and updated its pictogram,
  accessible name, and `theme-color`. Increased contrast in the dark theme still rendered opaque
  cards. Safari and VoiceOver were not checked.

## Codex-matched palette on 2026-10-29

- Light uses the Codex GitHub Light theme and dark uses VS Code+. Contrast was computed for every
  text role against the page, composited glass, and the pressed overlay: all are at least 4.5:1.
  White text on the `#007acc` fill measures 4.51:1. `#007acc` as text would be 3.7:1, so dark links
  use `#3794ff`.
- List and chat views at 320, 390, and 430px in both themes, 200% text, and the board and panel at
  900 and 1440px showed no overflow or controls under 44px. Increased contrast in dark still
  rendered opaque cards. Side-by-side comparison with a running Codex window was not done.

## Board list beside an open chat on 2026-10-29

- With a chat open at 900 and 1440px in both themes, the board collapsed into one scrolling list
  column with no empty-section placeholders, the panel took the remaining width, and the open chat
  was tinted, marked current, and scrolled into view. Escape and Close restored the columns and
  returned focus to the card; browser back reopened the panel. No overflow or controls under 44px.

## Codex window style on 2026-10-29

- Glass, the ambient backdrop, and press scaling were replaced with flat surfaces and a hairline
  edge; the toolbar spans the window, and the open board panel is a white main pane beside the grey
  sidebar. Inbox, filter, and chat views at 320, 390, and 430px in both themes, 200% text, and the
  board and panel at 900 and 1440px showed no overflow or controls under 44px. Panel open, switch,
  Escape focus return, and browser back still passed; increased contrast still rendered opaque cards.

## Board breakpoint and column breathing room on 2026-10-29

- The board now starts at 1280px, where four columns are about 290px wide; at 1024px the inbox is
  the centered list. Board columns have 32px page margins, 20px gaps, and a stable scrollbar gutter
  with 8px between cards and the scrollbar. Board and panel at 1280 and 1440px, the list at 1024px,
  and phone widths in both themes showed no overflow or controls under 44px.

## Pictograms, status tint, and motion on 2026-10-29

- Section titles carry tinted icon chips, disclosure rows lead with icons, and the status card has a
  colored left edge and a 6% status tint. Computed contrast on the tinted card stays at least 4.5:1
  for ink, muted, and body text in both themes (worst: light waiting ink 4.63:1).
- With motion allowed, the needs-you glyph, the live dot, and the chat sections animate; with
  reduced motion emulated, no animations run and every section is fully opaque. Phone, 200% text,
  and board views showed no overflow or controls under 44px.

## Status title bar instead of side stripes on 2026-10-29

- The status card's left edge and full-card tint are replaced by a tinted title bar, a status-colored
  hairline under it, and a status-colored card border; the agent decision and the board's open row
  lose their side stripes for 6% tinted blocks. Computed contrast: light waiting ink on the 8% bar
  4.52:1, waiting ink and muted text on the 6% accent row at least 4.5:1, dark accent on the dark
  row at least 4.5:1; the delivery validator passed. Phone, 200% text, and board views in both
  themes showed no overflow or controls under 44px; 31 tests pass.

## One-surface status card and a quiet dismiss on 2026-10-29

- The status card's tinted title band and inner divider are gone: the whole card carries the 6%
  status tint and status border. Dismiss reminder is a muted underlined text button (44px target)
  instead of a bordered button; the panel Close button keeps its bordered style. Muted text on the
  6% tints and white on the hovered Open in Codex fill stay at least 4.5:1; the validator passed.
  Phone, 200% text, and board views in both themes showed no overflow or controls under 44px; 31
  tests pass.

## Bell icon for dismissing the reminder on 2026-10-29

- Dismiss reminder moved from a text button in the card body to a 44px bell icon in the status
  header, with an accessible label and tooltip that switch to Restore reminder. At 320, 390, and
  1440px in both themes, clicking the bell dismissed the reminder, kept focus on it, showed the
  browser-only note, and a second click restored it; no overflow or controls under 44px.

## Smooth live updates, page transitions, and readability on 2026-10-29

- In Chrome at 390 and 1440px, a live update that moved a working chat to Needs you started one
  view transition, named only visible rows (6 and 8), and cleared the names afterwards; an update
  with the same layout started none. Opening and closing the board panel each ran one transition
  with no row names, and Escape still returned focus to the row. A disclosure was mid-height 60ms
  after opening and full height at 500ms. Inbox to chat and back each revealed with the `page`
  view transition type.
- With reduced motion emulated: no view transitions on the panel or page changes, disclosures
  opened at full height, and no animations were running.
- Metadata at 13px and the 17px next step showed no overflow or controls under 44px at 320, 390,
  and 430px in both themes, at 200% text, or on the board at 1024, 1280, and 1440px; 31 tests pass.

## Slido Forest Green accent on 2026-10-29

- The blue accent is replaced by Slido Forest Green `#198038` (dark text `#42a65f`), and new or
  passed results move to Slido Teal so they stay distinct from the accent. Computed contrast:
  Forest Green on white 5.02:1, white on Forest Green 5.02:1 (6.1:1 on hover), Forest Green on
  its 6% tint 4.62:1, dark `#42a65f` on the surface 5.44:1, teal 5.65:1 light and 5.89:1 dark,
  and status inks on the selected-row green tint at least 4.64:1. Forest Green on the grey fill is
  4.47:1, so the bordered button hover uses the green tint. Phone, 200% text, and board views in
  both themes showed no overflow or controls under 44px; 31 tests pass.

## Session-wide Files changed on 2026-10-29

- A two-turn demo chat showed Files changed with 3 files, newest first (`db.ts` Turns 1, 2;
  `migrate.ts` Turn 2; `schema.sql` Turn 1) at 390px light and 320px dark, with no overflow or
  controls under 44px. A chat whose edits were all in its latest turn hid the row. 31 tests pass.
- Turn numbers were removed from Files changed: the two-turn demo lists `db.ts`, `migrate.ts`,
  and `schema.sql` with only their folders, most recently changed first, at 390px light and 320px
  dark with no overflow; the single-turn chat still hides the row. 31 tests pass.

## Recap on the chat page on 2026-10-29

- A finished two-turn demo chat showed Chat so far and Latest turn with a separator (390px light,
  320px dark); a chat running its third turn showed only the previous recap; a chat without a
  recap showed the outcome alone, unchanged. No overflow or controls under 44px; 31 tests pass.

## Lighter decisions on 2026-10-29

- Decisions lead with the answer, then the muted two-line question, the reason, and the You or
  Agent meta line; a `## My request: stop` answer rendered as `My request: stop`. At 430px light
  and 320px dark there was no overflow or control under 44px; the purple role is 5.0:1 light and
  at least 4.5:1 dark; the board views passed; 31 tests pass.

## README screenshots after the redesign on 2026-10-29

- `make screenshots` now renders a 1440px light board with the Fix plant search ranking chat open,
  plus 420px dark captures of the inbox, a waiting chat, and a finished chat with Files changed
  expanded. The demo chats cover all four inbox sections, the reminder bell, a recap, files from
  two turns, and decisions by you and by the agent.
- The script binds a free port and exits if its server stops. A port already in use made the
  earlier run capture a different local app. Each phone capture uses a fresh browser context,
  because opening a chat marks its result as seen.
