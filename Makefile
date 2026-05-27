# GEOX Earth Intelligence — Makefile
# DITEMPA BUKAN DIBERI

.PHONY: install test smoke build up down lint format clean security-audit forge

PYTHON := python3
PIP := pip
DOCKER := docker
COMPOSE := docker compose

install:
	$(PIP) install -e ".[dev]"

test:
	PYTHONPATH=src pytest tests/ -q --tb=short

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
include /root/arifOS/scripts/security_audit.mk

forge: security-audit
	@echo "GEOX Surgical Burn complete. Awaiting SOVEREIGN SEAL."
