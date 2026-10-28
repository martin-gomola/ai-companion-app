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
