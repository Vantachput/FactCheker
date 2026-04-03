# ==============================================================================
# Makefile — FactChecker Task Runner
# ==============================================================================
# Працює на Linux/macOS нативно. На Windows — через Git Bash або 'make' з choco.
#
# Використання:
#   make dev        — запустити бота локально
#   make test       — запустити тести
#   make lint       — перевірити стиль коду
#   make backup     — зробити бекап БД
#   make deploy     — задеплоїти оновлення на prod (Linux)
#   make help       — показати всі команди
# ==============================================================================

.PHONY: help dev test lint lint-fix format docs profile backup deploy restart status logs

PYTHON     := .venv/bin/python
PIP        := .venv/bin/pip
VENV_WIN   := .venv\Scripts\python.exe
DB_FILE    := bot_data.db
BACKUP_DIR := backups

# ---------------------------------------------------------------------------- #
#  Дефолтна ціль
# ---------------------------------------------------------------------------- #
help:
	@echo ""
	@echo "  FactChecker — available commands:"
	@echo ""
	@echo "  DEV"
	@echo "    make dev          Start bot in development mode"
	@echo "    make test         Run all unit tests"
	@echo "    make lint         Check code style (ruff)"
	@echo "    make lint-fix     Auto-fix linting issues"
	@echo "    make format       Format code (ruff format)"
	@echo "    make docs         Build Sphinx docs (Ukrainian)"
	@echo "    make profile      Run performance profiling suite"
	@echo ""
	@echo "  PRODUCTION (Linux)"
	@echo "    make backup       Backup SQLite database"
	@echo "    make deploy       Pull latest code & restart service"
	@echo "    make restart      Restart systemd service"
	@echo "    make status       Show service status"
	@echo "    make logs         Tail service logs"
	@echo ""

# ---------------------------------------------------------------------------- #
#  DEV — локальний запуск
# ---------------------------------------------------------------------------- #
dev:
	@echo ">>> Starting FactChecker bot (dev mode)..."
	$(PYTHON) main.py

test:
	@echo ">>> Running tests..."
	$(PYTHON) -m pytest tests/ -v --tb=short

test-cov:
	@echo ">>> Running tests with coverage..."
	$(PYTHON) -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

lint:
	@echo ">>> Linting with ruff..."
	$(PYTHON) -m ruff check .

lint-fix:
	@echo ">>> Auto-fixing lint issues..."
	$(PYTHON) -m ruff check --fix .

format:
	@echo ">>> Formatting code..."
	$(PYTHON) -m ruff format .

docs:
	@echo ">>> Building Sphinx documentation (Ukrainian)..."
	cd docs && $(PYTHON) -m sphinx -b html source build/html/uk
	@echo ">>> Docs ready at: docs/build/html/uk/index.html"

profile:
	@echo ">>> Running FactChecker Performance Profiling Suite..."
	$(PYTHON) profiling/run_profiling.py
	@echo ">>> Profiling complete."

# ---------------------------------------------------------------------------- #
#  PRODUCTION (Linux only)
# ---------------------------------------------------------------------------- #
backup:
	@mkdir -p $(BACKUP_DIR)
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	sqlite3 $(DB_FILE) ".backup $(BACKUP_DIR)/bot_data_$$TIMESTAMP.db"; \
	echo ">>> Backup saved: $(BACKUP_DIR)/bot_data_$$TIMESTAMP.db"

deploy:
	@echo ">>> Pulling latest code..."
	git pull origin main
	@echo ">>> Updating dependencies..."
	$(PIP) install -r requirements.txt
	@echo ">>> Restarting service..."
	sudo systemctl restart factchecker.service
	@sleep 3
	sudo systemctl status factchecker.service --no-pager

restart:
	sudo systemctl restart factchecker.service

status:
	sudo systemctl status factchecker.service --no-pager

logs:
	sudo journalctl -u factchecker.service -f
