# Story Specification: Codex Companion Task Dashboard

## 1. User Story
**As a** software engineer using Codex,  
**I want** a dedicated status dashboard with task controls and live status updates,  
**So that** I can track and manage my Codex tasks from one place.

### Version 1 scope

Version 1 supports Codex tasks only. Task status, progress, logs, and available actions must come from the Codex integration. Other coding assistants and general-purpose agent orchestrators are outside this version's scope.

---

## 2. Mockup & Layout Reference
```
+-------------------------------------------------------------------------+
|  Codex Task Dashboard                                  [ CODEX LIVE ] |
|  Live tracking for your Codex tasks                                     |
|                                                                         |
|  +--------------------+   +--------------------+   +--------------------+  |
|  | Executing        1 |   | Queued           1 |   | Completed        1 |  |
|  +--------------------+   +--------------------+   +--------------------+  |
|                                                                         |
|  TASKS                                                                  |
|  +-------------------------------------------------------------------+  |
|  | Generating API Route Handlers                        [ RUNNING ]  |  |
|  | [=========================>---------------] 65%                    |  |
|  | Target: server/routes/api.js                          Elapsed: 42s|  |
|  | > Codex: Compiling schemas and generating scaffolding...          |  |
|  |                                                                   |  |
|  | [ PAUSE ]  [ CANCEL ]                                             |  |
|  +-------------------------------------------------------------------+  |
+-------------------------------------------------------------------------+
```

---

## 3. Functional Requirements

### 3.1 Visual Summary & Metric Counters
* **Dynamic Grid Counter Cards:** The top of the dashboard must display three high-level Codex task metrics:
  * **Executing:** Number of Codex tasks currently running.
  * **Queued:** Number of Codex tasks waiting to run.
  * **Completed:** Number of Codex tasks completed in the current session.
* **Clear Status Indicators:** Show each metric's state with an icon and text. Do not rely on color alone or use a colored border on only one side of a card.

### 3.2 Task Telemetry Stream
* **Individual Status Pills:** Every Codex task card must show a title and a state pill (`RUNNING`, `QUEUED`, `COMPLETED`, `PAUSED`, `CANCELED`).
* **Fluid Progress Trackers:** Running tasks require an animated, proportional width element utilizing standard CSS easing curves to represent compilation steps smoothly.
* **Low-Level Log Output:** Running Codex tasks must show their latest available log or status message in a monospace area.
* **Metadata Footers:** Subtext bounds must dynamically show targeted output destinations (e.g., file paths) and precise relative timing indicators.

### 3.3 Interactive Task Management Controls
* **Action Buttons:** Every task entry must provide functional interactive handles based on its current operational state:
  * **Running Tasks:** Must display a **Pause** button and a **Cancel** button. Cancel uses the destructive action token.
  * **Paused Tasks:** The **Pause** button transitions to a **Resume** button.
  * **Queued Tasks:** Must display a **Cancel** button to remove the task from the Codex queue before execution.
* **Immediate UI Feedback:** After Codex confirms an action, update the status badge and task card to reflect the new state. Do not show a successful state change if the Codex action fails.

---

## 4. API & Integration Endpoints

The dashboard communicates with a local backend that reads task data from Codex and forwards supported task actions. These routes are the dashboard-to-backend contract; the backend must use the Codex integration rather than a generic multi-agent framework.

### 4.1 Get All Tasks
* **Endpoint:** `GET /api/tasks`
* **Description:** Retrieves the latest Codex task list for the counters and task details.
* **Response Schema (200 OK):**
```json
[
  {
    "id": "task-101",
    "title": "Generating API Route Handlers",
    "status": "RUNNING",
    "progress": 65,
    "target": "server/routes/api.js",
    "elapsedSeconds": 42,
    "latestLog": "Compiling schemas and generating Express router scaffolding..."
  }
]
```

### 4.2 Modify Task State (Pause/Resume/Cancel)
* **Endpoint:** `POST /api/tasks/:id/action`
* **Description:** Requests the specified action for a Codex task.
* **Request Payload Structure:**
```json
{
  "action": "PAUSE" // Options: "PAUSE", "RESUME", "CANCEL"
}
```
* **Response Schema (200 OK):**
```json
{
  "id": "task-101",
  "status": "PAUSED",
  "message": "Codex task paused."
}
```

---

## 5. Technical Constraints & Architecture

* **Deployment Structure:** The dashboard uses `index.html` and the shared token-generated CSS-variable layer, imported once.
* **Design Engine:** Semantic HTML structures styled with the shared CSS variables.
* **Visual Palette:** Use the shared design tokens and CSS-variable layer for color, type, spacing, and motion. Do not define a page-specific palette or hardcode visual values.
* **Live Sync:** The client uses fetch requests to the `/api` routes. If live Codex data is unavailable, the interface must show that state clearly instead of presenting simulated task data as live.
* **Responsive and Accessible UI:** Start with the phone layout, use semantic HTML, and provide the required interaction states and keyboard access for every control.

---

## 6. Acceptance Criteria

| Criteria ID | Scenario | Given | When | Then |
| --- | --- | --- | --- | --- |
| **AC-01** | Initial UI Initialization | The browser requests the dashboard | The dashboard loads with Codex data available | The UI displays Codex task counts and task details with their current states. |
| **AC-02** | Pause and Resume a Codex Task | A Codex task is `RUNNING` | The user pauses it, then resumes it | The UI reflects each confirmed Codex state change and shows the appropriate next action. |
| **AC-03** | Cancel a Codex Task | A Codex task is `RUNNING` or `QUEUED` | The user cancels it | The UI reflects the cancellation after Codex confirms it. |
| **AC-04** | Codex Action Failure | A task action is unavailable or fails in Codex | The user tries to pause, resume, or cancel | The UI keeps the last confirmed task state and displays an actionable error. |
| **AC-05** | Fluid Layout Adaptation | The dashboard is shown in a narrow side-dock or split window | The viewport narrows | Content reflows without clipping or breaking the layout. |
