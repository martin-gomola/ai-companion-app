"use strict";

const $ = (id) => document.getElementById(id);
function readPreference(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}
document.documentElement.dataset.theme = readPreference("theme") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
const MAX_STEPS = 80;
const PROJECT_PREVIEW_LIMIT = 3;
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
const NEXT_LABEL = { answer: "Answer", review: "Review", approve: "Approve", run: "Run", decide: "Decide", do: "To do" };
const INBOX_FILTERS = {
  waiting: { label: "Needs you", empty: "No recent chats need you right now." },
  working: { label: "Working", empty: "No recent chats are currently working." },
  new: { label: "New results", empty: "No unseen results in the recent inbox from the last 24 hours." },
};

const threadId = new URLSearchParams(location.search).get("thread") || "";
const statusParam = new URLSearchParams(location.search).get("status");
const inboxStatus = Object.hasOwn(INBOX_FILTERS, statusParam) ? statusParam : "";
const inboxReturn = inboxStatus ? `&status=${inboxStatus}` : "";
document.body.dataset.view = threadId ? "thread" : "inbox";
let latest = null;
let filter = "key";
const projectMotionStarted = new Map();

$("theme-toggle").addEventListener("click", () => {
  const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = theme;
  try { localStorage.setItem("theme", theme); } catch { /* Theme still works for this page. */ }
  const next = theme === "dark" ? "light" : "dark";
  $("theme-toggle").setAttribute("aria-label", `Switch to ${next} theme`);
  $("theme-toggle").title = `Switch to ${next} theme`;
  $("theme-toggle").querySelector("use").setAttribute("href", `#i-${next === "dark" ? "moon" : "sun"}`);
});

const currentTheme = document.documentElement.dataset.theme;
const nextTheme = currentTheme === "dark" ? "light" : "dark";
$("theme-toggle").setAttribute("aria-label", `Switch to ${nextTheme} theme`);
$("theme-toggle").title = `Switch to ${nextTheme} theme`;
$("theme-toggle").querySelector("use").setAttribute("href", `#i-${currentTheme === "dark" ? "sun" : "moon"}`);

$("hero-meta").querySelector("summary").addEventListener("click", () => {
  if (!$("hero-meta").open && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
    requestAnimationFrame(() => $("session-facts").animate([{ opacity: 0, transform: "translateY(-4px)" }, { opacity: 1, transform: "translateY(0)" }], { duration: 180, easing: "ease-out" }));
  }
});

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

function iconLabel(id, name, text) {
  const target = $(id);
  if (!target.classList.contains("icon-label")) {
    target.classList.add("icon-label");
    target.replaceChildren(icon(name), el("span", "icon-label-text"));
    if (target.tagName === "SUMMARY") {
      const chevron = icon("i-back");
      chevron.classList.add("disclosure-chevron");
      target.append(chevron);
    }
  }
  target.querySelector("svg use").setAttribute("href", `#${name}`);
  const label = target.querySelector(".icon-label-text");
  if (label.textContent !== text) label.textContent = text;
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
}

// Inbox

function needsAttention(chat) {
  return hasAttention(chat) && !reminderDismissed(chat);
}

function hasAttention(chat) {
  return chat.status === "waiting" || (chat.status === "done" && Object.hasOwn(NEXT_LABEL, chat.next_kind) && Boolean(chat.next_text));
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
  return !hasAttention(chat) && chat.status !== "working" && Date.now() - ended < NEW_WINDOW_MS && chat.turn_ended_at > seen.get(chat.id);
}

function matchesInboxStatus(chat, status) {
  return status === "waiting" ? needsAttention(chat) : status === "new" ? isNewResult(chat) : chat.status === status;
}

function tokenCount(value, compact = false) {
  return Number.isSafeInteger(value) && value >= 0 ? value.toLocaleString(compact ? "en-US" : undefined, compact ? { notation: "compact", maximumFractionDigits: 1 } : {}) : "Not reported";
}

function renderSessionInfo(thread, turn) {
  const usage = thread.token_usage || {};
  const last = thread.last_token_usage || {};
  const contextWindow = thread.context_window;
  const hasContext = Number.isSafeInteger(last.total_tokens) && last.total_tokens >= 0 && Number.isSafeInteger(contextWindow) && contextWindow > 0;
  $("hero-meta").hidden = false;
  $("session-project").textContent = thread.project || thread.cwd.split("/").pop() || "Unassigned";
  $("session-project").title = thread.cwd;
  $("session-updated").textContent = ago(thread.updated_at);
  $("session-updated").title = "Last recorded event";
  $("session-tokens").textContent = Number.isSafeInteger(usage.total_tokens) ? tokenCount(usage.total_tokens, true) : "—";
  $("session-tokens").title = `${tokenCount(usage.total_tokens)} reported session tokens`;
  $("session-context").textContent = hasContext ? `${Math.round(last.total_tokens / contextWindow * 100)}%` : "—";
  $("session-context-metric").title = hasContext ? `Last reported request: ${tokenCount(last.total_tokens)} / ${tokenCount(contextWindow)} tokens` : "Context usage not reported";
  const labels = {
    input_tokens: "Input", cached_input_tokens: "Cached input (included in input)",
    cache_write_input_tokens: "Cache-write input", output_tokens: "Output",
    reasoning_output_tokens: "Reasoning (included in output)", total_tokens: "Session total",
  };
  const facts = Object.entries(labels).filter(([key]) => Object.hasOwn(usage, key)).map(([key, label]) => [label, tokenCount(usage[key]), "usage"]);
  facts.push(
    ["Project", thread.project || thread.cwd.split("/").pop() || "Unassigned"],
    ["Last request tokens", tokenCount(last.total_tokens), "context"],
    ["Reported context window", contextWindow > 0 ? tokenCount(contextWindow) : "Not reported", "context"],
    ["Model (latest turn)", thread.model, "runtime"], ["Reasoning effort", thread.reasoning_effort, "runtime"],
    ["Session provider", thread.model_provider, "runtime"], ["Recorded Git branch", thread.git_branch],
    ["Session client", thread.cli_version], ["Working directory", thread.cwd],
    ["Turn", turn?.index ? String(turn.index) : ""],
  );
  if (thread.token_usage_at && !Number.isNaN(new Date(thread.token_usage_at).getTime())) facts.push(["Totals reported", new Date(thread.token_usage_at).toLocaleString()]);
  $("session-facts").replaceChildren(...facts.filter(([, value]) => value).map(([label, value, kind]) => {
    const field = el("div");
    field.dataset.kind = kind || "workspace";
    field.append(el("dt", "", label), el("dd", "", value));
    return field;
  }));
  $("session-note").textContent = Object.keys(usage).length ? "Reported session totals accumulate across requests. Cached input is included in input; reasoning is included in output. Context uses the last reported request and model window. Branch and client come from session metadata." : "Cumulative session usage has not been reported for this chat.";
}

function chatSummary(chat) {
  if (hasAttention(chat)) return chat.question || chat.next_text || chat.outcome;
  if (chat.next_kind !== "none" && chat.next_kind !== "unknown" && chat.next_text) return chat.next_text;
  return chat.outcome;
}

function renderRow(chat) {
  const state = attentionState(chat);
  const status = STATUS[state] || STATUS.idle;
  const item = el("li");
  const link = el("a", "row");
  link.href = `/?thread=${encodeURIComponent(chat.id)}${inboxReturn}`;
  link.dataset.status = state;
  const unread = isNewResult(chat);
  link.dataset.unread = String(unread);
  const badge = el("span", "row-icon");
  badge.append(icon(status.icon));
  const body = el("span", "row-body");
  const head = el("span", "row-head");
  head.append(el("span", "row-title", chatName(chat)), el("span", "row-time", ago(chat.updated_at)));
  body.append(head);
  const summary = chatSummary(chat);
  if (summary) body.append(el("span", "row-text", summary));
  const meta = el("span", "row-meta");
  meta.append(el("span", `tag tag--${state}`, status.label));
  if (unread) meta.append(el("span", "tag tag--new", "New"));
  body.append(meta);
  link.append(badge, body);
  item.append(link);
  return item;
}

function renderInbox(chats) {
  latest = chats;
  const focused = document.activeElement;
  const focusedProject = focused.closest(".project-group")?.dataset.project;
  const focusedHref = focused.closest(".row")?.getAttribute("href");
  const focusedHistory = focused.matches(".project-history > summary");
  const shownChats = inboxStatus ? chats.filter((chat) => matchesInboxStatus(chat, inboxStatus)) : chats;
  const groups = new Map();
  for (const chat of shownChats) {
    const project = chat.project || "Unassigned";
    if (!groups.has(project)) groups.set(project, []);
    groups.get(project).push(chat);
  }
  const priority = (chat) => needsAttention(chat) ? 0 : chat.status === "working" ? 1 : isNewResult(chat) ? 2 : 3;
  const knownProjects = new Map([...$("project-groups").children].map((group) => [group.dataset.project, group.dataset.state]));
  for (const name of projectMotionStarted.keys()) if (!groups.has(name)) projectMotionStarted.delete(name);
  const expanded = new Set([...$("project-groups").querySelectorAll(".project-group[open]")].map((group) => group.dataset.project));
  const expandedHistory = new Set([...$("project-groups").querySelectorAll(".project-history[open]")].map((history) => history.closest(".project-group").dataset.project));
  $("inbox-empty").hidden = chats.length > 0;
  $("filter-empty").hidden = !inboxStatus || shownChats.length > 0 || chats.length === 0;
  $("filter-empty").textContent = inboxStatus ? INBOX_FILTERS[inboxStatus].empty : "";
  iconLabel("projects-title", inboxStatus ? STATUS[inboxStatus]?.icon || "i-answer" : "i-folder", inboxStatus ? INBOX_FILTERS[inboxStatus].label : "Projects");
  $("show-all-chats").hidden = !inboxStatus;
  const projects = [...groups.entries()].sort(([nameA, chatsA], [nameB, chatsB]) =>
    Math.min(...chatsA.map(priority)) - Math.min(...chatsB.map(priority)) || nameA.localeCompare(nameB),
  ).map(([name, projectChats]) => {
    projectChats.sort((a, b) => priority(a) - priority(b) || b.updated_at.localeCompare(a.updated_at));
    const waiting = projectChats.some(needsAttention);
    const state = waiting ? "waiting" : projectChats.some((chat) => chat.status === "working") ? "working" : projectChats.some(isNewResult) ? "new" : "";
    const group = el("details", "project-group");
    if (!knownProjects.has(name)) group.classList.add("is-entering");
    group.dataset.project = name;
    group.open = knownProjects.has(name) ? expanded.has(name) : Boolean(inboxStatus) || waiting;
    const heading = el("summary", "project-heading");
    const badge = el("span", "project-icon");
    const pictogram = icon(STATUS[state]?.icon || "i-folder");
    if (state === "waiting" || state === "working") {
      if (knownProjects.get(name) !== state || !projectMotionStarted.has(name)) projectMotionStarted.set(name, performance.now());
      // Preserve the cue's phase when live updates rebuild the header.
      pictogram.querySelector("use").style.animationDelay = `-${performance.now() - projectMotionStarted.get(name)}ms`;
    } else projectMotionStarted.delete(name);
    badge.append(pictogram);
    const identity = el("span", "project-identity");
    identity.append(el("span", "project-name", name), el("span", "project-count", `${projectChats.length} ${projectChats.length === 1 ? "chat" : "chats"}`));
    heading.append(badge, identity);
    if (state) heading.append(el("span", `project-state project-state--${state}`, state === "waiting" ? "Needs you" : state === "working" ? "Working" : "New results"));
    group.dataset.state = state;
    const previewLimit = Math.max(PROJECT_PREVIEW_LIMIT, projectChats.filter((chat) => priority(chat) < 3).length);
    const rows = el("ol", "rows");
    rows.replaceChildren(...projectChats.slice(0, previewLimit).map(renderRow));
    heading.addEventListener("click", () => {
      if (!group.open && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
        requestAnimationFrame(() => rows.animate([{ opacity: 0, transform: "translateY(-4px)" }, { opacity: 1, transform: "translateY(0)" }], { duration: 180, easing: "ease-out" }));
      }
    });
    group.append(heading, rows);
    const olderChats = projectChats.slice(previewLimit);
    if (olderChats.length) {
      const history = el("details", "project-history");
      history.open = expandedHistory.has(name);
      const summary = el("summary");
      summary.append(icon("i-back"), el("span", "", `${olderChats.length} earlier ${olderChats.length === 1 ? "chat" : "chats"}`));
      const olderRows = el("ol", "rows");
      olderRows.replaceChildren(...olderChats.map(renderRow));
      history.append(summary, olderRows);
      group.append(history);
    }
    return group;
  });
  $("project-groups").replaceChildren(...projects);
  if (focusedProject) {
    const group = projects.find((project) => project.dataset.project === focusedProject);
    const target = focusedHref ? [...(group?.querySelectorAll(".row") || [])].find((row) => row.getAttribute("href") === focusedHref) : focusedHistory ? group?.querySelector(".project-history > summary") : group?.querySelector(".project-heading");
    const history = target?.closest(".project-history");
    if (focusedHref && history) history.open = true;
    (target || group?.querySelector(".project-heading"))?.focus({ preventScroll: true });
  }
  const needs = chats.filter(needsAttention).length;
  for (const tile of document.querySelectorAll(".overview-card")) {
    const kind = tile.dataset.kind;
    const matches = chats.filter((chat) => matchesInboxStatus(chat, kind));
    tile.dataset.empty = String(matches.length === 0);
    tile.querySelector(".overview-value").textContent = matches.length;
    tile.href = inboxStatus !== kind && matches.length === 1 ? `/?thread=${encodeURIComponent(matches[0].id)}${inboxReturn}` : `/?status=${kind}`;
    tile.setAttribute("aria-label", `${INBOX_FILTERS[kind].label}: ${matches.length} ${matches.length === 1 ? "chat" : "chats"}`);
    if (inboxStatus === kind) tile.setAttribute("aria-current", "page");
    else tile.removeAttribute("aria-current");
  }
  $("project-total").textContent = inboxStatus ? `${shownChats.length} ${shownChats.length === 1 ? "match" : "matches"}` : `${groups.size} ${groups.size === 1 ? "project" : "projects"} · ${shownChats.length} recent ${shownChats.length === 1 ? "chat" : "chats"}`;
  document.title = needs ? `(${needs}) Codex companion` : "Codex companion";
}

// Thread

function renderHero(thread, turn) {
  const hero = document.querySelector(".hero");
  const state = attentionState({ ...thread, next_kind: turn?.next_kind, next_text: turn?.next_text });
  hero.dataset.status = state;
  const status = STATUS[state] || STATUS.idle;
  $("hero-status-icon").setAttribute("href", `#${status.icon}`);
  $("hero-title").textContent = status.label;
  const working = thread.status === "working";
  const step = [...thread.steps].reverse().find((step) => step.turn === turn?.index && !["turn", "user"].includes(step.kind));
  const activityLabels = { command: "Latest step: command", edit: "Latest step: file changes", tool: "Latest step: tool call", thinking: "Latest step: reasoning", agent: "Latest step: delegated work", decision: "Latest step: decision", message: "Latest step: progress update", answer: "Latest step: response", question: "Latest step: question" };
  const text = working ? activityLabels[step?.kind] || "Working on your request." : turn && turn.outcome;
  $("hero-text").textContent = text || "No outcome yet.";
  const activityBadge = document.querySelector(".latest-step");
  activityBadge.dataset.active = String(working);
  activityBadge.dataset.kind = working && Object.hasOwn(activityLabels, step?.kind) ? step.kind : "working";
  $("latest-step-icon").setAttribute("href", `#${working ? ICONS[step?.kind] || "i-working" : "i-message"}`);
  $("recorded-activity-icon").setAttribute("href", `#${ICONS[step?.kind] || "i-tool"}`);
  const activityText = step?.title || "";
  const commandActivity = step?.kind === "command";
  const activityAlreadyListed = (step?.kind === "edit" && turn?.files.length > 0) || (commandActivity && turn?.checks.some((check) => check.command === activityText));
  $("hero-activity").hidden = !working || !activityText || activityAlreadyListed;
  $("hero-activity-text").classList.toggle("terminal", commandActivity);
  // Leave the selected text untouched when an unrelated session metric changes.
  if ($("hero-activity-text").textContent !== activityText || Boolean($("hero-activity-text").querySelector("code")) !== commandActivity) {
    $("hero-activity-text").replaceChildren(commandActivity ? commandCode(activityText) : el("p", "", activityText));
  }
  renderSessionInfo(thread, turn);
}

function renderNext(thread, turn) {
  const pending = [...thread.decisions].reverse().find((d) => d.source === "asked" && d.chosen === null);
  let kind = turn ? turn.next_kind : "unknown";
  let text = turn ? turn.next_text : "";
  if (thread.status === "working") {
    kind = "working";
    text = "";
  } else if (pending) {
    kind = "answer";
    text = pending.question;
  } else if (kind === "none") {
    text = "No further action was requested.";
  } else if (kind === "unknown") {
    text = "No next action was recorded.";
  }
  $("next").hidden = kind === "working";
  $("next").dataset.kind = kind;
  $("next-kind").hidden = !NEXT_LABEL[kind];
  const actionIcon = { answer: "i-question", review: "i-message", approve: "i-answer", run: "i-command", decide: "i-decision", do: "i-tool" };
  iconLabel("next-kind", actionIcon[kind] || "i-question", NEXT_LABEL[kind] || "");
  $("next-text").textContent = text;
  const options = pending ? pending.options : [];
  $("next-options").hidden = options.length === 0;
  $("next-options").replaceChildren(...options.map((option) => el("li", "", option)));
  $("open-codex").href = `codex://threads/${encodeURIComponent(thread.id)}`;
  $("open-codex").hidden = false;
  const chat = { ...thread, next_kind: turn?.next_kind, next_text: turn?.next_text };
  $("reminder-controls").hidden = !hasAttention(chat) || !thread.attention_key;
  const dismissed = reminderDismissed(chat);
  $("reminder-toggle").textContent = dismissed ? "Restore reminder" : "Dismiss reminder";
  $("reminder-note").textContent = dismissed ? "Dismissed in this browser. The request remains open in Codex." : "Only affects this browser’s inbox. Does not answer or approve the request.";
}

$("reminder-toggle").addEventListener("click", () => {
  if (!latest || !latest.attention_key) return;
  try {
    const key = `reminder:v1:${latest.id}`;
    if (reminderDismissed(latest)) localStorage.removeItem(key);
    else localStorage.setItem(key, latest.attention_key);
    renderThread(latest);
  } catch {
    $("reminder-note").textContent = "Could not save this preference. The reminder remains active.";
  }
});

window.addEventListener("storage", (event) => {
  if (latest && (event.key === null || event.key.startsWith("reminder:v1:"))) {
    if (threadId) renderThread(latest);
    else renderInbox(latest);
  }
});

function commandCode(command) {
  const code = el("code", "terminal-command");
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
    code.append(kind ? el("span", `terminal-${kind}`, token) : document.createTextNode(token));
  }
  return code;
}

function renderChanges(turn) {
  const files = turn ? turn.files : [];
  const checks = turn ? turn.checks : [];
  $("changes").hidden = files.length === 0 && checks.length === 0 && $("hero-activity").hidden;
  let warning = "";
  if (turn && turn.edited_after_check) warning = "Files changed after the last check ran.";
  else if (files.length && !checks.length) warning = "No tests or linters ran after these edits.";
  else if (checks.some((check) => check.exit_code === null)) warning = "Some checks have no recorded exit result.";
  $("check-warning").hidden = !warning;
  $("check-warning-text").textContent = warning;
  $("checks").replaceChildren(...checks.map((check) => {
    const state = check.exit_code === null ? "unknown" : check.exit_code === 0 ? "passed" : "failed";
    const item = el("li", "check");
    item.dataset.state = state;
    item.append(icon(state === "unknown" ? "i-question" : state === "passed" ? "i-answer" : "i-alert"), commandCode(check.command), el("span", "check-exit", state === "unknown" ? "Exit not reported" : `exit ${check.exit_code}`));
    return item;
  }));
  $("files-wrap").hidden = files.length === 0;
  iconLabel("files-summary", "i-edit", `${files.length} ${files.length === 1 ? "file" : "files"} changed`);
  $("files").replaceChildren(...files.map((path) => {
    const item = el("li");
    item.append(el("code", "", path.split("/").pop()), el("span", "file-dir", path.split("/").slice(0, -1).join("/")));
    return item;
  }));
}

function renderDecisions(thread) {
  const decisions = thread.decisions.map((decision, index) => ({ decision, key: JSON.stringify([decision.at, decision.turn, decision.source, decision.question, index]) })).filter(({ decision }) => decision.chosen !== null).reverse();
  const existing = new Map([...$("decisions-wrap").querySelectorAll(".decision")].map((item) => [item.dataset.key, item]));
  const focused = document.activeElement.closest(".decision");
  const focusedKey = focused?.dataset.key;
  $("decisions-wrap").hidden = decisions.length === 0;
  const items = decisions.map(({ decision, key }) => {
    const item = existing.get(key) || el("li", "decision");
    const record = JSON.stringify(decision);
    if (item.dataset.record === record) return item;
    const expanded = item.querySelector("details")?.open || false;
    item.dataset.key = key;
    item.dataset.record = record;
    const question = el("div", "decision-bubble decision-question");
    const at = new Date(decision.at);
    const when = [decision.turn ? `Turn ${decision.turn}` : "", Number.isNaN(at.getTime()) ? "" : at.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })].filter(Boolean).join(" · ");
    const questionLabel = el("p", "decision-meta icon-label");
    questionLabel.append(icon("i-question"), el("span", "", ["Question", when].filter(Boolean).join(" · ")));
    question.append(questionLabel, el("h3", "", decision.question));
    const answer = el("div", "decision-bubble decision-answer");
    const answerLabel = el("p", "decision-meta icon-label");
    answerLabel.append(icon(decision.source === "agent" ? "i-agent" : "i-user"), el("span", "", decision.source === "agent" ? "Agent decision" : "Your answer"));
    answer.append(answerLabel, el("p", "decision-answer-text", decision.chosen || "No answer text recorded."));
    if (decision.reason) answer.append(el("p", "reason", decision.reason));
    const alternatives = decision.options.filter((option) => option !== decision.chosen);
    if (alternatives.length) {
      const disclosure = el("details", "decision-alternatives");
      disclosure.open = expanded;
      const summary = el("summary");
      summary.append(icon("i-back"), el("span", "", "Other options"));
      const options = el("ul", "decision-other-options");
      options.replaceChildren(...alternatives.map((option) => el("li", "", option)));
      disclosure.append(summary, options);
      answer.append(disclosure);
    }
    item.replaceChildren(question, answer);
    return item;
  });
  const older = items.slice(DECISION_PREVIEW_LIMIT);
  $("decision-history").hidden = older.length === 0;
  iconLabel("decision-history-summary", "i-decision", `${older.length} earlier ${older.length === 1 ? "decision" : "decisions"}`);
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
    const target = item?.querySelector("summary") || item?.querySelector("h3") || $(decisions.length ? "decisions-title" : "hero-title");
    if (!target.matches("summary")) target.tabIndex = -1;
    target.focus({ preventScroll: true });
  }
}

function renderEarlier(turns) {
  const earlier = turns.slice(0, -1).reverse();
  $("earlier-wrap").hidden = earlier.length === 0;
  iconLabel("earlier-summary", "i-turn", `Earlier turns (${earlier.length})`);
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
  iconLabel("activity-summary", "i-message", `Activity (${thread.steps.length} steps)`);
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
  if (!thread) {
    latest = null;
    $("title").textContent = "Chat not found";
    document.title = "Chat not found · Codex companion";
    document.querySelector(".hero").dataset.status = "idle";
    $("hero-title").textContent = "No rollout file for this chat";
    $("hero-text").textContent = "It may have been archived. Go back to the inbox.";
    document.querySelector(".latest-step").dataset.active = "false";
    $("hero-meta").hidden = true;
    $("hero-activity").hidden = true;
    $("hero-status-icon").setAttribute("href", "#i-turn");
    $("latest-step-icon").setAttribute("href", "#i-alert");
    for (const id of ["open-codex", "next", "changes", "decisions-wrap", "earlier-wrap", "activity-wrap"]) $(id).hidden = true;
    return;
  }
  $("next").hidden = false;
  $("activity-wrap").hidden = false;
  latest = thread;
  const turn = thread.turns[thread.turns.length - 1];
  $("title").textContent = chatName(thread);
  document.title = `${chatName(thread)} · Codex companion`;
  renderHero(thread, turn);
  renderNext(thread, turn);
  renderChanges(turn);
  renderDecisions(thread);
  renderEarlier(thread.turns);
  renderTimeline(thread);
  if (turn && turn.ended_at) seen.set(thread.id, turn.ended_at);
}

for (const chip of document.querySelectorAll(".chip")) {
  chip.addEventListener("click", () => {
    filter = chip.dataset.filter;
    for (const other of document.querySelectorAll(".chip")) other.setAttribute("aria-pressed", String(other === chip));
    if (latest) renderTimeline(latest);
  });
}

if (threadId) {
  $("thread-view").hidden = false;
  $("back").hidden = false;
  $("back").href = inboxStatus ? `/?status=${inboxStatus}` : "/";
  $("back-label").textContent = inboxStatus ? INBOX_FILTERS[inboxStatus].label : "Inbox";
  $("eyebrow").hidden = true;
  connect(`/api/stream?thread=${encodeURIComponent(threadId)}`, "thread", renderThread);
} else {
  $("inbox-view").hidden = false;
  connect("/api/stream", "inbox", renderInbox);
}
