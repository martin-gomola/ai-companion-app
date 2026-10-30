PORT ?= 8787
STATE_DIR ?= $(HOME)/.your-turn
PID_FILE := $(STATE_DIR)/server.pid
LOG_FILE := $(STATE_DIR)/server.log
URL := http://127.0.0.1:$(PORT)
MARKETPLACE := your-turn
PLUGIN := your-turn@$(MARKETPLACE)

.PHONY: install up down restart status logs test screenshots

install:
	@command -v uv >/dev/null || { echo "uv is required: https://docs.astral.sh/uv/"; exit 1; }
	@command -v codex >/dev/null || { echo "Codex CLI is required to install the plugin"; exit 1; }
	@uv sync --quiet
	@codex plugin marketplace list 2>/dev/null | grep -q "^$(MARKETPLACE) " || codex plugin marketplace add "$(CURDIR)"
	@codex plugin add $(PLUGIN)
	@$(MAKE) --no-print-directory up
	@echo "Installed $(PLUGIN). Restart Codex so it loads the skill and MCP server."

up:
	@mkdir -p "$(STATE_DIR)"
	@if [ -f "$(PID_FILE)" ] && kill -0 "$$(cat "$(PID_FILE)")" 2>/dev/null; then \
		echo "Already running on $(URL) (pid $$(cat "$(PID_FILE)"))"; exit 0; \
	fi; \
	if lsof -nP -iTCP:$(PORT) -sTCP:LISTEN >/dev/null 2>&1; then \
		curl -fsS -o /dev/null "$(URL)/api/inbox" 2>/dev/null && { echo "Your Turn is already running on $(URL)"; exit 0; }; \
		echo "Port $(PORT) is in use by another process. Try: make up PORT=8788"; exit 1; \
	fi; \
	uv sync --quiet || exit 1; \
	nohup .venv/bin/yourturn serve --port $(PORT) >"$(LOG_FILE)" 2>&1 & \
	echo $$! >"$(PID_FILE)"; \
	for _ in 1 2 3 4 5 6 7 8 9 10; do \
		curl -fsS -o /dev/null "$(URL)/" 2>/dev/null && { echo "Your Turn on $(URL)"; exit 0; }; \
		sleep 0.5; \
	done; \
	echo "Your Turn did not start. Last log lines:"; tail -n 20 "$(LOG_FILE)"; exit 1

down:
	@if [ -f "$(PID_FILE)" ] && pid="$$(cat "$(PID_FILE)")" && kill "$$pid" 2>/dev/null; then \
		for _ in 1 2 3 4 5 6 7 8 9 10; do kill -0 "$$pid" 2>/dev/null || break; sleep 0.3; done; \
		echo "Stopped Your Turn (pid $$pid)"; \
	else \
		echo "Your Turn is not running"; \
	fi; \
	rm -f "$(PID_FILE)"

restart: down up

status:
	@if [ -f "$(PID_FILE)" ] && kill -0 "$$(cat "$(PID_FILE)")" 2>/dev/null; then \
		echo "Running on $(URL) (pid $$(cat "$(PID_FILE)"))"; \
	else \
		echo "Not running"; \
	fi

logs:
	@tail -n 50 -f "$(LOG_FILE)"

test:
	@uv run pytest -q

screenshots:
	@uv sync --quiet
	@uvx --with playwright python scripts/readme_screenshots.py
