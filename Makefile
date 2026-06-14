# GEOX Earth Intelligence — Makefile
# DITEMPA BUKAN DIBERI

.PHONY: install test smoke build up down lint format clean security-audit forge

PYTHON := /root/geox/.venv/bin/python3
UV := uv
DOCKER := docker
COMPOSE := docker compose

# GEOX is now managed by uv (like arifOS). The .venv is the single source of truth.
# DITEMPA BUKAN DIBERI — 2026-06-05
install:
	$(UV) sync --frozen

install-dev:
	$(UV) sync --frozen

test:
	PYTHONPATH=src $(PYTHON) -m pytest tests/ -q --tb=short

smoke:
	PYTHONPATH=src $(PYTHON) scripts/smoke_test.py

build:
	$(DOCKER) build -t geox:latest .

up:
	$(COMPOSE) up -d geox

down:
	$(COMPOSE) down

lint:
	ruff check src/ || true
	mypy src/ --ignore-missing-imports || true

format:
	ruff format src/ || true

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# ── arifOS Federation Security Audit ─────────────────────────────────────────
# Inherits security-audit from arifOS canonical.mk — fires 888_HOLD on CRITICAL/HIGH
include /root/arifOS/scripts/forge.mk
include /root/arifOS/scripts/security_audit.mk

forge: clean-temp sot-bump security-audit
	@echo "⛓️  GEOX forge gate passed."
