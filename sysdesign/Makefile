# R26-SE-017 — Monorepo Makefile
# Usage:
#   make install   — install all Python packages
#   make db        — create/verify Neon tables
#   make dev       — start all 6 services + frontend (requires concurrently)
#   make agent1    — start Agent 1 only (port 8001)
#   make agent2    — start Agent 2 only (port 8002)
#   make agent3    — start Agent 3 only (port 8003)
#   make agent4    — start Agent 4 only (port 8004)
#   make srs       — start SRS Assembler only (port 8005)
#   make orchestrator — start Orchestrator only (port 8000)
#   make web       — start React frontend (port 5173)
#   make test      — run all Python tests

.PHONY: install db dev web agent1 agent2 agent3 agent4 srs orchestrator test

PYTHON = python
PIP    = pip

# ── Install ──────────────────────────────────────────────────────────────────
install:
	$(PIP) install -e packages/contracts
	$(PIP) install -e packages/shared
	$(PIP) install -r services/agent1-requirements/requirements_final.txt
	@echo "All packages installed."

# ── Database ─────────────────────────────────────────────────────────────────
db:
	$(PYTHON) infra/create_tables.py
	$(PYTHON) infra/verify_tables.py

# ── Individual services ───────────────────────────────────────────────────────
orchestrator:
	cd services/orchestrator && $(PYTHON) -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

agent1:
	cd services/agent1-requirements && $(PYTHON) -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

agent2:
	cd services/agent2-hld && $(PYTHON) -m uvicorn server:app --host 0.0.0.0 --port 8002 --reload

agent3:
	cd services/agent3-lld && $(PYTHON) -m uvicorn main:app --host 0.0.0.0 --port 8003 --reload

agent4:
	cd services/agent4-ui && $(PYTHON) -m uvicorn api:app --host 0.0.0.0 --port 8004 --reload

srs:
	cd services/srs-assembler && $(PYTHON) -m uvicorn main:app --host 0.0.0.0 --port 8005 --reload

# ── Frontend ──────────────────────────────────────────────────────────────────
web:
	cd apps/web && npm run dev

# ── Tests ─────────────────────────────────────────────────────────────────────
test:
	$(PYTHON) -m pytest services/agent2-hld/tests/ -v
	$(PYTHON) infra/verify_tables.py
