"use strict";

const $ = (id) => document.getElementById(id);
function readPreference(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}
const MAX_STEPS = 80;
const SECTION_LIMIT = 5;
const DECISION_PREVIEW_LIMIT = 3;
const NEW_WINDOW_MS = 24 * 60 * 60 * 1000;
const KEY_KINDS = new Set(["user", "answer", "question", "decision", "edit", "agent"]);
const ICONS = {
  turn: "i-turn", user: "i-user", message: "i-message", answer: "i-answer", thinking: "i-thinking",
  command: "i-command", edit: "i-edit", tool: "i-tool", agent: "i-agent", decision: "i-decision", question: "i-question",
};
const STATUS = {
  waiting: { label: "Needs you", icon: "i-question" },
  working: { label: "Working", icon: "i-working" },
  done: { label: "Done", icon: "i-answer" },
  interrupted: { label: "Stopped", icon: "i-stop" },
  idle: { label: "Not started", icon: "i-turn" },
  dismissed: { label: "Reminder dismissed", icon: "i-question" },
};
const SECTION_ICONS = { waiting: "i-question", working: "i-working", new: "i-answer", earlier: "i-turn" };
const NEXT_LABEL = { answer: "Answer", review: "Review", approve: "Approve", run: "Run", decide: "Decide", do: "To do" };
const STEP_LABEL = {
  command: "Ran a command", edit: "Edited files", tool: "Called a tool", thinking: "Reasoning", agent: "Delegated work",
  decision: "Made a decision", message: "Progress update", answer: "Wrote a response", question: "Asked a question",
};
const INBOX_FILTERS = {
  waiting: { label: "Needs you", empty: "No recent chats need you right now." },
  working: { label: "Working", empty: "No recent chats are currently working." },
  new: { label: "New results", empty: "No unseen results in the recent inbox from the last 24 hours." },
};
const SECTIONS = [
  { key: "waiting", label: "Needs you" },
  { key: "working", label: "Working" },
  { key: "new", label: "New results" },
  { key: "earlier", label: "Earlier" },
];

const params = new URLSearchParams(location.search);
const threadId = params.get("thread") || "";
const statusParam = params.get("status");
const inboxStatus = Object.hasOwn(INBOX_FILTERS, statusParam) ? statusParam : "";
const inboxReturn = inboxStatus ? `&status=${inboxStatus}` : "";
document.body.dataset.view = threadId ? "thread" : "inbox";
const board = matchMedia("(min-width: 1280px)");
const calm = matchMedia("(prefers-reduced-motion: reduce)");
let inboxData = null;
let inboxLayout = "";
let threadData = null;
let filter = "key";
let openId = "";
let threadSource = null;

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function icon(name) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("aria-hidden", "true");
  const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
  use.setAttribute("href", `#${name}`);
  svg.append(use);
  return svg;
}

// Every working glyph shares one phase, so live re-renders never restart the rotation.
function syncSpin(use) {
  use.style.animationDelay = `-${performance.now() % 1400}ms`;
}

const ROW_ICONS = {
  "files-summary": "i-edit", "session-files-summary": "i-edit", "decision-history-summary": "i-decision", "earlier-summary": "i-turn",
  "activity-summary": "i-thinking", "session-summary": "i-agent",
};

function tone(name, kind) {
  const chip = el("span", "tone");
  chip.dataset.tone = kind;
  chip.append(icon(name));
  return chip;
}

function rowLabel(id, text, value = "") {
  const target = $(id);
  if (!target.querySelector(".row-label")) {
    const lead = icon(ROW_ICONS[id]);
    lead.classList.add("row-icon");
    const chevron = icon("i-chevron");
    chevron.classList.add("disclosure-chevron");
    target.replaceChildren(lead, el("span", "row-label"), el("span", "row-value"), chevron);
  }
  const label = target.querySelector(".row-label");
  if (label.textContent !== text) label.textContent = text;
  const detail = target.querySelector(".row-value");
  if (detail.textContent !== value) detail.textContent = value;
}

function clock(iso) {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function ago(iso) {
  const seconds = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
  if (!Number.isFinite(seconds)) return "";
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`;
  if (seconds < 172800) return `${Math.round(seconds / 3600)}h ago`;
  return `${Math.round(seconds / 86400)}d ago`;
}

function chatName(chat) {
  return chat.title || `Untitled chat · ${chat.cwd.split("/").pop() || chat.id.slice(0, 8)}`;
}

function projectName(chat) {
  return chat.project || chat.cwd.split("/").pop() || "Unassigned";
}

const seen = {
  get: (id) => readPreference(`seen:${id}`) || "",
  set: (id, endedAt) => {
    try { if (endedAt) localStorage.setItem(`seen:${id}`, endedAt); } catch { /* Keep results unread if storage is unavailable. */ }
  },
};

function setConnection(state, text) {
  $("connection").dataset.state = state;
  $("connection-text").textContent = text;
}

function connect(url, event, render) {
  const source = new EventSource(url);
  source.onopen = () => setConnection("live", "Live");
  source.onerror = () => setConnection("offline", "Reconnecting");
  source.addEventListener(event, (message) => render(JSON.parse(message.data)));
  return source;
}

// Inbox

function needsAttention(chat) {
  return hasAttention(chat) && !reminderDismissed(chat);
}

function hasAttention(chat) {
  return Boolean(chat.needs_you);
}

function reminderDismissed(chat) {
  if (!chat.attention_key) return false;
  return readPreference(`reminder:v1:${chat.id}`) === chat.attention_key;
}

function attentionState(chat) {
  return hasAttention(chat) ? reminderDismissed(chat) ? "dismissed" : "waiting" : chat.status;
}

function isNewResult(chat) {
  const ended = new Date(chat.turn_ended_at).getTime();
  return !hasAttention(chat) && chat.status !== "working" && chat.status !== "interrupted" && Date.now() - ended < NEW_WINDOW_MS && chat.turn_ended_at > seen.get(chat.id);
}

function sectionOf(chat) {
  return needsAttention(chat) ? "waiting" : chat.status === "working" ? "working" : isNewResult(chat) ? "new" : "earlier";
}

function chatSummary(chat) {
  if (hasAttention(chat)) return chat.question || chat.next_text || chat.outcome;
  if (chat.next_kind !== "none" && chat.next_kind !== "unknown" && chat.next_text) return chat.next_text;
  return chat.outcome;
}

function renderRow(chat) {
  const state = attentionState(chat);
  const status = STATUS[state] || STATUS.idle;
  const unread = isNewResult(chat);
  const item = el("li");
  const link = el("a", "row");
  link.href = `/?thread=${encodeURIComponent(chat.id)}${inboxReturn}`;
  link.dataset.status = state;
  link.dataset.id = chat.id;
  link.dataset.unread = String(unread);
  if (chat.id === openId) link.setAttribute("aria-current", "true");
  const glyph = el("span", "glyph");
  glyph.append(icon(status.icon));
  if (state === "working") syncSpin(glyph.querySelector("use"));
  const body = el("span", "row-body");
  const head = el("span", "row-head");
  head.append(el("span", "row-title", chatName(chat)), el("span", "row-time", ago(chat.updated_at)));
  body.append(head);
  const summary = chatSummary(chat);
  if (summary) body.append(el("span", "row-text", summary));
  const meta = el("span", "row-meta");
  const action = chat.question ? "Answer" : NEXT_LABEL[chat.next_kind];
  const tag = state === "waiting" ? action || status.label : state === "done" || state === "idle" ? "" : status.label;
  if (tag) meta.append(el("span", `tag tag--${state}`, tag));
  if (unread) meta.append(el("span", "tag tag--new", "New"));
  meta.append(el("span", "row-project", projectName(chat)));
  body.append(meta);
  const chevron = icon("i-chevron");
  chevron.classList.add("row-chevron");
  link.append(glyph, body, chevron);
  item.append(link);
  return item;
}

function renderSection({ key, label }, chats) {
  const capped = !inboxStatus && !board.matches && key !== "earlier" && chats.length > SECTION_LIMIT;
  const wrap = el("section", "group");
  wrap.dataset.section = key;
  const title = el("h2", "group-title");
  title.id = `section-${key}`;
  title.append(tone(SECTION_ICONS[key], key === "earlier" ? "muted" : key), el("span", "", label), el("span", "group-count", String(chats.length)));
  wrap.setAttribute("aria-labelledby", title.id);
  const list = el("ol", "list");
  list.replaceChildren(...chats.slice(0, capped ? SECTION_LIMIT : chats.length).map(renderRow));
  if (chats.length === 0) list.append(el("li", "empty column-empty", "No chats"));
  if (capped) {
    const item = el("li");
    const more = el("a", "show-all");
    more.href = `/?status=${key}`;
    more.append(el("span", "", `Show all ${chats.length}`), icon("i-chevron"));
    item.append(more);
    list.append(item);
  }
  wrap.append(title, list);
  return wrap;
}

function groupChats(chats) {
  const groups = new Map(SECTIONS.map(({ key }) => [key, []]));
  for (const chat of chats) groups.get(sectionOf(chat)).push(chat);
  for (const list of groups.values()) list.sort((a, b) => b.updated_at.localeCompare(a.updated_at));
  return groups;
}

function layoutOf(groups) {
  return [...groups].map(([key, list]) => `${key}:${list.map((chat) => chat.id).join(",")}`).join("|");
}

// View transitions ignore ancestor clipping, so only rows visible in their scroller get a name;
// the rest cross-fade with the page instead of flying over other columns.
function nameVisibleRows(on) {
  const clips = [{ top: 0, left: 0, bottom: innerHeight, right: innerWidth }, $("sections").getBoundingClientRect()];
  for (const row of $("sections").querySelectorAll(".row")) {
    const item = row.parentElement;
    const box = item.getBoundingClientRect();
    const visible = [...clips, row.closest(".list").getBoundingClientRect()]
      .every((clip) => box.bottom > clip.top && box.top < clip.bottom && box.right > clip.left && box.left < clip.right);
    item.style.viewTransitionName = on && visible ? `row-${row.dataset.id.replace(/[^\w-]/g, "_")}` : "";
  }
}

function transition(update, { rows = true } = {}) {
  if (!document.startViewTransition || calm.matches || document.hidden || threadId) {
    update();
    return Promise.resolve();
  }
  nameVisibleRows(rows);
  const view = document.startViewTransition(() => {
    update();
    nameVisibleRows(rows);
  });
  const clear = () => nameVisibleRows(false);
  view.finished.then(clear, clear);
  return view.updateCallbackDone.catch(() => {});
}

function liveInbox(chats) {
  if (inboxLayout && layoutOf(groupChats(chats)) !== inboxLayout) transition(() => renderInbox(chats));
  else renderInbox(chats);
}

function renderInbox(chats) {
  inboxData = chats;
  const focusedHref = document.activeElement.closest(".row, .show-all")?.getAttribute("href");
  const groups = groupChats(chats);
  inboxLayout = layoutOf(groups);
  // The board keeps every column in place; the list, also used beside an open panel, drops empty sections.
  const columns = board.matches && !openId;
  const shown = SECTIONS.filter(({ key }) => inboxStatus ? key === inboxStatus && groups.get(key).length > 0 : columns || groups.get(key).length > 0);
  $("sections").replaceChildren(...shown.map((section) => renderSection(section, groups.get(section.key))));
  $("inbox-empty").hidden = chats.length > 0;
  $("filter-empty").hidden = !inboxStatus || shown.length > 0 || chats.length === 0;
  $("filter-empty").textContent = inboxStatus ? INBOX_FILTERS[inboxStatus].empty : "";
  for (const segment of document.querySelectorAll(".segment")) {
    const kind = segment.dataset.kind;
    const count = kind ? groups.get(kind).length : chats.length;
    segment.dataset.empty = String(count === 0);
    segment.querySelector(".segment-count").textContent = count;
    const label = kind ? INBOX_FILTERS[kind].label : "All recent chats";
    segment.setAttribute("aria-label", `${label}: ${count} ${count === 1 ? "chat" : "chats"}`);
    if (kind === inboxStatus) segment.setAttribute("aria-current", "page");
    else segment.removeAttribute("aria-current");
  }
  if (focusedHref) [...$("sections").querySelectorAll("a")].find((link) => link.getAttribute("href") === focusedHref)?.focus({ preventScroll: true });
  const needs = groups.get("waiting").length;
  document.title = needs ? `(${needs}) Codex companion` : "Codex companion";
}

// Thread

function tokenCount(value, compact = false) {
  return Number.isSafeInteger(value) && value >= 0 ? value.toLocaleString(compact ? "en-US" : undefined, compact ? { notation: "compact", maximumFractionDigits: 1 } : {}) : "Not reported";
}

function renderSessionInfo(thread, turn) {
  const usage = thread.token_usage || {};
  const last = thread.last_token_usage || {};
  const contextWindow = thread.context_window;
  const hasContext = Number.isSafeInteger(last.total_tokens) && last.total_tokens >= 0 && Number.isSafeInteger(contextWindow) && contextWindow > 0;
  const brief = [
    Number.isSafeInteger(usage.total_tokens) ? `${tokenCount(usage.total_tokens, true)} tokens` : "",
    hasContext ? `${Math.round(last.total_tokens / contextWindow * 100)}% context` : "",
  ].filter(Boolean).join(" · ");
  rowLabel("session-summary", "Session details", brief);
  const labels = {
    input_tokens: "Input", cached_input_tokens: "Cached input (included in input)",
    cache_write_input_tokens: "Cache-write input", output_tokens: "Output",
    reasoning_output_tokens: "Reasoning (included in output)", total_tokens: "Session total",
  };
  const facts = Object.entries(labels).filter(([key]) => Object.hasOwn(usage, key)).map(([key, label]) => [label, tokenCount(usage[key])]);
  facts.push(
    ["Project", projectName(thread)],
    ["Last request tokens", tokenCount(last.total_tokens)],
    ["Reported context window", contextWindow > 0 ? tokenCount(contextWindow) : "Not reported"],
    ["Model (latest turn)", thread.model], ["Reasoning effort", thread.reasoning_effort],
    ["Session provider", thread.model_provider], ["Recorded Git branch", thread.git_branch],
    ["Session client", thread.cli_version], ["Working directory", thread.cwd],
    ["Turn", turn?.index ? String(turn.index) : ""],
  );
  if (thread.token_usage_at && !Number.isNaN(new Date(thread.token_usage_at).getTime())) facts.push(["Totals reported", new Date(thread.token_usage_at).toLocaleString()]);
  $("session-facts").replaceChildren(...facts.filter(([, value]) => value).map(([label, value]) => {
    const field = el("div");
    field.append(el("dt", "", label), el("dd", "", value));
    return field;
  }));
  $("session-note").textContent = Object.keys(usage).length ? "Reported session totals accumulate across requests. Cached input is included in input; reasoning is included in output. Context uses the last reported request and model window. Branch and client come from session metadata." : "Cumulative session usage has not been reported for this chat.";
}

function setStatusText(content, command = false) {
  const target = $("status-text");
  const text = typeof content === "string" ? content : "";
  // Leave the selected text untouched when an unrelated value changes.
  if (target.textContent === text && Boolean(target.querySelector("code")) === command) return;
  target.replaceChildren(command ? commandCode(text) : el("p", "", text));
}

function renderStatus(thread, turn) {
  const chat = { ...thread, next_kind: turn?.next_kind, next_text: turn?.next_text };
  const state = attentionState(chat);
  const status = STATUS[state] || STATUS.idle;
  $("status-card").dataset.status = state;
  $("status-icon").setAttribute("href", `#${status.icon}`);
  if (state === "working") syncSpin($("status-icon"));
  $("status-title").textContent = status.label;
  $("open-codex").href = `codex://threads/${encodeURIComponent(thread.id)}`;
  $("open-codex").hidden = false;
  $("status-body").hidden = false;

  const pending = [...thread.decisions].reverse().find((d) => d.source === "asked" && d.chosen === null);
  let kind = turn ? turn.next_kind : "unknown";
  let label = NEXT_LABEL[kind] || "";
  if (thread.status === "working") {
    const step = [...thread.steps].reverse().find((step) => step.turn === turn?.index && !["turn", "user"].includes(step.kind));
    kind = "working";
    label = STEP_LABEL[step?.kind] || "";
    const listed = (step?.kind === "edit" && turn?.files.length > 0) || (step?.kind === "command" && turn?.checks.some((check) => check.command === step.title));
    if (listed) {
      setStatusText(`${label}, shown under Changes and checks.`);
      label = "";
    } else setStatusText(step?.title || "Working on your request.", step?.kind === "command" && Boolean(step.title));
  } else if (pending) {
    kind = "answer";
    label = NEXT_LABEL.answer;
    setStatusText(pending.question);
  } else if (kind === "none") {
    setStatusText("No further action was requested.");
  } else if (kind === "unknown") {
    setStatusText("No next action was recorded.");
  } else {
    setStatusText(turn.next_text);
  }
  $("status-body").dataset.kind = kind;
  $("next-kind").hidden = !label;
  $("next-kind").textContent = label;
  const options = pending && thread.status !== "working" ? pending.options : [];
  $("next-options").hidden = options.length === 0;
  $("next-options").replaceChildren(...options.map((option) => el("li", "", option)));

  $("reminder-toggle").hidden = !hasAttention(chat) || !thread.attention_key;
  const dismissed = reminderDismissed(chat);
  $("reminder-toggle").setAttribute("aria-label", dismissed ? "Restore reminder" : "Dismiss reminder");
  $("reminder-toggle").title = dismissed ? "Restore reminder" : "Dismiss reminder (this browser only; does not answer the request)";
  $("reminder-icon").setAttribute("href", dismissed ? "#i-bell" : "#i-bell-off");
  $("reminder-note").textContent = dismissed ? "Only in this browser. The request is still open in Codex." : "";

  const outcome = thread.status === "working" ? "" : turn?.outcome || "";
  $("outcome-wrap").hidden = !outcome;
  if ($("outcome").textContent !== outcome) $("outcome").textContent = outcome;
}

$("reminder-toggle").addEventListener("click", () => {
  if (!threadData || !threadData.attention_key) return;
  try {
    const key = `reminder:v1:${threadData.id}`;
    if (reminderDismissed(threadData)) localStorage.removeItem(key);
    else localStorage.setItem(key, threadData.attention_key);
    renderThread(threadData);
    if (inboxData) renderInbox(inboxData);
  } catch {
    $("reminder-note").textContent = "Could not save this preference. The reminder remains active.";
  }
});

function syncThemeToggle() {
  const dark = document.documentElement.dataset.theme === "dark";
  const label = `Switch to ${dark ? "light" : "dark"} theme`;
  $("theme-toggle").setAttribute("aria-label", label);
  $("theme-toggle").title = label;
  $("theme-toggle").querySelector("use").setAttribute("href", dark ? "#i-sun" : "#i-moon");
}

$("theme-toggle").addEventListener("click", () => {
  const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  try { localStorage.setItem("theme", theme); } catch { /* The choice still applies to this page. */ }
  document.documentElement.dataset.theme = theme;
  document.querySelector('meta[name="theme-color"]')?.setAttribute("content", theme === "dark" ? "#1e1e1e" : "#ffffff");
  syncThemeToggle();
});
document.addEventListener("themechange", syncThemeToggle);
syncThemeToggle();

window.addEventListener("storage", (event) => {
  if (event.key === null || event.key.startsWith("reminder:v1:")) {
    if (threadData) renderThread(threadData);
    if (inboxData) renderInbox(inboxData);
  }
});

function commandCode(command) {
  const code = el("code", "command");
  let commandStart = true;
  // Presentation hints only, not a shell parser; preserve every character as inert text.
  for (const token of command.match(/"(?:\\.|[^"\\])*"|'[^']*'|&&|\|\||[|;\n]|[^\s&|;]+|[&]|[^\S\n]+/g) || []) {
    let kind = "";
    if (/^(?:&&|\|\||[|;\n])$/.test(token)) {
      kind = "operator";
      commandStart = true;
    } else if (token.trim()) {
      if (/^["']/.test(token)) kind = "string";
      else if (token.startsWith("-")) kind = "flag";
      else if (token.includes("/") || /^[\w.-]+\.[a-zA-Z0-9]+$/.test(token)) kind = "path";
      else if (commandStart) kind = "executable";
      commandStart = false;
    }
    code.append(kind ? el("span", `command-${kind}`, token) : document.createTextNode(token));
  }
  return code;
}

function relativePath(path, cwd) {
  return cwd && path.startsWith(`${cwd}/`) ? path.slice(cwd.length + 1) : path;
}

function renderChanges(thread, turn) {
  const files = turn ? turn.files : [];
  const checks = turn ? turn.checks : [];
  $("changes").hidden = files.length === 0 && checks.length === 0;
  let warning = "";
  if (turn && turn.edited_after_check) warning = "Files changed after the last check ran.";
  else if (files.length && !checks.length) warning = "No tests or linters ran after these edits.";
  else if (checks.some((check) => check.exit_code === null)) warning = "Some checks have no recorded exit result.";
  $("check-warning").hidden = !warning;
  $("check-warning-text").textContent = warning;
  $("checks").replaceChildren(...checks.map((check) => {
    const state = check.exit_code === null ? "unknown" : check.exit_code === 0 ? "passed" : "failed";
    const item = el("li", "list-row check");
    item.dataset.state = state;
    const result = state === "unknown" ? "Exit not reported" : state === "passed" ? "Passed" : `Failed (exit ${check.exit_code})`;
    item.append(icon(state === "unknown" ? "i-question" : state === "passed" ? "i-answer" : "i-alert"), commandCode(check.command), el("span", "check-result", result));
    return item;
  }));
  $("files-wrap").hidden = files.length === 0;
  rowLabel("files-summary", `${files.length} ${files.length === 1 ? "file" : "files"} changed`);
  $("files").replaceChildren(...files.map((path) => fileItem(path, thread.cwd)));
}

function fileItem(path, cwd) {
  const relative = relativePath(path, cwd);
  const item = el("li");
  item.title = path;
  item.append(el("code", "", relative.split("/").pop()), el("span", "file-dir", relative.split("/").slice(0, -1).join("/")));
  return item;
}

// The session's final set of changed files, most recently changed first; shown only when earlier
// turns changed files too, since Changes and checks already lists the latest turn's files.
function renderSessionFiles(thread, turn) {
  const lastTurn = new Map();
  for (const each of thread.turns) for (const path of each.files) lastTurn.set(path, each.index);
  const earlier = thread.turns.some((each) => each !== turn && each.files.length > 0);
  $("session-files-wrap").hidden = !earlier;
  rowLabel("session-files-summary", "Files changed", `${lastTurn.size} ${lastTurn.size === 1 ? "file" : "files"}`);
  const paths = [...lastTurn].sort(([, a], [, b]) => b - a).map(([path]) => path);
  $("session-files").replaceChildren(...paths.map((path) => fileItem(path, thread.cwd)));
}

function renderDecisions(thread) {
  const decisions = thread.decisions.map((decision, index) => ({ decision, key: JSON.stringify([decision.at, decision.turn, decision.source, decision.question, index]) })).filter(({ decision }) => decision.chosen !== null).reverse();
  const existing = new Map([...$("decisions-wrap").querySelectorAll(".decision")].map((item) => [item.dataset.key, item]));
  const focused = document.activeElement.closest(".decision");
  const focusedKey = focused?.dataset.key;
  $("decisions-wrap").hidden = decisions.length === 0;
  const items = decisions.map(({ decision, key }) => {
    const item = existing.get(key) || el("li", "list-row decision");
    const record = JSON.stringify(decision);
    if (item.dataset.record === record) return item;
    const expanded = item.querySelector("details")?.open || false;
    item.dataset.key = key;
    item.dataset.record = record;
    const at = new Date(decision.at);
    const when = [decision.turn ? `Turn ${decision.turn}` : "", Number.isNaN(at.getTime()) ? "" : at.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })].filter(Boolean).join(" · ");
    const answer = el("div", "decision-answer");
    answer.append(el("p", "decision-role", decision.source === "agent" ? "Agent decision" : "Your answer"), el("p", "decision-answer-text", decision.chosen || "No answer text recorded."));
    item.replaceChildren(el("p", "decision-meta", ["Question", when].filter(Boolean).join(" · ")), el("h3", "", decision.question), answer);
    if (decision.reason) item.append(el("p", "reason", decision.reason));
    const alternatives = decision.options.filter((option) => option !== decision.chosen);
    if (alternatives.length) {
      const disclosure = el("details", "decision-alternatives");
      disclosure.open = expanded;
      const summary = el("summary");
      const chevron = icon("i-chevron");
      chevron.classList.add("disclosure-chevron");
      summary.append(el("span", "", `Other options (${alternatives.length})`), chevron);
      const options = el("ul", "decision-other-options");
      options.replaceChildren(...alternatives.map((option) => el("li", "", option)));
      disclosure.append(summary, options);
      item.append(disclosure);
    }
    return item;
  });
  const older = items.slice(DECISION_PREVIEW_LIMIT);
  $("decision-history").hidden = older.length === 0;
  rowLabel("decision-history-summary", "Earlier decisions", String(older.length));
  for (const [list, wanted] of [[$("decisions"), items.slice(0, DECISION_PREVIEW_LIMIT)], [$("earlier-decisions"), older]]) {
    const retained = new Set(wanted);
    for (const [index, item] of wanted.entries()) {
      if (list.children[index] !== item) list.insertBefore(item, list.children[index] || null);
    }
    for (const child of [...list.children]) if (!retained.has(child)) child.remove();
  }
  if (focusedKey && document.activeElement === document.body) {
    const item = items.find((item) => item.dataset.key === focusedKey);
    if (item?.closest(".decision-history")) $("decision-history").open = true;
    const target = item?.querySelector("summary") || item?.querySelector("h3") || $(decisions.length ? "decisions-title" : "status-title");
    if (!target.matches("summary")) target.tabIndex = -1;
    target.focus({ preventScroll: true });
  }
}

function renderEarlier(turns) {
  const earlier = turns.slice(0, -1).reverse();
  $("earlier-wrap").hidden = earlier.length === 0;
  rowLabel("earlier-summary", "Earlier turns", String(earlier.length));
  $("earlier").replaceChildren(...earlier.map((turn) => {
    const item = el("li", "turn-row");
    item.append(el("span", "turn-index", `Turn ${turn.index}`));
    const body = el("span", "turn-body");
    if (turn.prompt) body.append(el("span", "turn-prompt", turn.prompt));
    body.append(el("span", "", turn.outcome || STATUS[turn.status]?.label || turn.status));
    item.append(body);
    return item;
  }));
}

function renderTimeline(thread) {
  const steps = thread.steps
    .filter((step) => filter === "all" || KEY_KINDS.has(step.kind) || step.status !== "done")
    .reverse()
    .slice(0, MAX_STEPS);
  rowLabel("activity-summary", "Activity", `${thread.steps.length} ${thread.steps.length === 1 ? "step" : "steps"}`);
  $("timeline-empty").hidden = steps.length > 0;
  $("timeline").replaceChildren(...steps.map((step) => {
    const item = el("li", "step");
    item.dataset.kind = step.kind;
    item.dataset.status = step.status;
    const node = el("span", "step-node");
    node.append(icon(ICONS[step.kind] || "i-turn"));
    const card = el("div", "step-card");
    const head = el("div", "step-head");
    head.append(el("span", "step-title", step.title || step.kind));
    if (step.status === "failed") head.append(el("span", "tag tag--interrupted", "Failed"));
    card.append(head);
    const meta = [clock(step.at), step.detail].filter(Boolean).join(" · ");
    if (meta) card.append(el("span", "step-meta", meta));
    item.append(node, card);
    return item;
  }));
}

function renderThread(thread) {
  const title = threadId ? $("title") : $("panel-title");
  const subtitle = threadId ? $("subtitle") : $("panel-subtitle");
  if (!thread) {
    threadData = null;
    title.textContent = "Chat not found";
    if (threadId) document.title = "Chat not found · Codex companion";
    subtitle.hidden = true;
    $("status-card").dataset.status = "idle";
    $("status-icon").setAttribute("href", "#i-alert");
    $("status-title").textContent = "No rollout file for this chat";
    $("status-body").hidden = false;
    $("status-body").dataset.kind = "none";
    $("next-kind").hidden = true;
    setStatusText("It may have been archived. Go back to the inbox.");
    for (const id of ["open-codex", "next-options", "reminder-toggle", "outcome-wrap", "changes", "decisions-wrap", "more"]) $(id).hidden = true;
    return;
  }
  threadData = thread;
  const turn = thread.turns[thread.turns.length - 1];
  title.textContent = chatName(thread);
  if (threadId) document.title = `${chatName(thread)} · Codex companion`;
  subtitle.hidden = false;
  subtitle.textContent = `${projectName(thread)} · ${ago(thread.updated_at)}`;
  subtitle.title = `${thread.cwd} · last recorded event`;
  $("more").hidden = false;
  renderStatus(thread, turn);
  renderChanges(thread, turn);
  renderDecisions(thread);
  renderEarlier(thread.turns);
  renderSessionFiles(thread, turn);
  renderTimeline(thread);
  renderSessionInfo(thread, turn);
  if (turn && turn.ended_at) seen.set(thread.id, turn.ended_at);
}

// Board panel

function panelUrl(id) {
  const query = new URLSearchParams();
  if (inboxStatus) query.set("status", inboxStatus);
  if (id) query.set("open", id);
  const text = query.toString();
  return text ? `/?${text}` : "/";
}

function cardFor(id) {
  return [...$("sections").querySelectorAll(".row")].find((row) => new URLSearchParams(row.search).get("thread") === id);
}

function resetThread() {
  $("panel-title").textContent = "Loading…";
  $("panel-subtitle").textContent = "";
  $("status-card").dataset.status = "idle";
  $("status-icon").setAttribute("href", "#i-turn");
  $("status-title").textContent = "Loading…";
  for (const id of ["status-body", "open-codex", "outcome-wrap", "changes", "decisions-wrap", "more"]) $(id).hidden = true;
  for (const details of $("thread-view").querySelectorAll("details")) details.open = false;
  $("thread-view").scrollTop = 0;
}

function showPanel(id) {
  if (id === openId) return Promise.resolve();
  threadSource?.close();
  threadSource = null;
  threadData = null;
  openId = id;
  return transition(() => {
    document.body.dataset.panel = id ? "open" : "closed";
    $("thread-view").hidden = !id;
    if (inboxData) renderInbox(inboxData);
    if (!id) return;
    cardFor(id)?.scrollIntoView({ block: "nearest" });
    resetThread();
    threadSource = connect(`/api/stream?thread=${encodeURIComponent(id)}`, "thread", renderThread);
  }, { rows: false });
}

function closePanel() {
  const id = openId;
  history.pushState(null, "", panelUrl(""));
  showPanel("").then(() => cardFor(id)?.focus());
}

if (!threadId) {
  $("sections").addEventListener("click", (event) => {
    const link = event.target.closest(".row");
    if (!link || !board.matches || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    const id = new URLSearchParams(link.search).get("thread");
    if (id !== openId) history.pushState(null, "", panelUrl(id));
    showPanel(id);
  });
  $("panel-close").addEventListener("click", closePanel);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && openId) closePanel();
  });
  window.addEventListener("popstate", () => showPanel(board.matches ? new URLSearchParams(location.search).get("open") || "" : ""));
  board.addEventListener("change", () => {
    if (!board.matches && openId) location.assign(`/?thread=${encodeURIComponent(openId)}${inboxReturn}`);
    else if (inboxData) renderInbox(inboxData);
  });
}

for (const chip of document.querySelectorAll(".chip")) {
  chip.addEventListener("click", () => {
    filter = chip.dataset.filter;
    for (const other of document.querySelectorAll(".chip")) other.setAttribute("aria-pressed", String(other === chip));
    if (threadData) renderTimeline(threadData);
  });
}

if (threadId) {
  $("thread-view").hidden = false;
  $("back").hidden = false;
  $("back").href = inboxStatus ? `/?status=${inboxStatus}` : "/";
  $("back-label").textContent = inboxStatus ? INBOX_FILTERS[inboxStatus].label : "Inbox";
  $("inbox-title").hidden = true;
  $("thread-heading").hidden = false;
  connect(`/api/stream?thread=${encodeURIComponent(threadId)}`, "thread", renderThread);
} else {
  $("inbox-view").hidden = false;
  $("panel-head").hidden = false;
  if (inboxStatus) $("inbox-title").textContent = INBOX_FILTERS[inboxStatus].label;
  connect("/api/stream", "inbox", liveInbox);
  const open = params.get("open");
  if (open && board.matches) showPanel(open);
  else if (open) location.replace(`/?thread=${encodeURIComponent(open)}${inboxReturn}`);
}
