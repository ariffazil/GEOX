# GEOX Earth Intelligence — Makefile
# DITEMPA BUKAN DIBERI

.PHONY: install test smoke build up down lint format clean security-audit forge

# Prefer GEOX venv; fall back to system python3 (VPS layout varies)
PYTHON := $(shell if [ -x /root/GEOX/.venv/bin/python3 ]; then echo /root/GEOX/.venv/bin/python3; elif [ -x /root/geox/.venv/bin/python3 ]; then echo /root/geox/.venv/bin/python3; else echo python3; fi)
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

# ── MCP Apps deploy + evidence seed (Batch C / E) ───────────────────────────
# DEMO LAS aliases are NOT committed (absolute-path symlinks break clean clones).
# They are recreated here from tracked fixtures. Clean clone path:
#   make deploy-apps   # or: make seed-demo-las && make seed-evidence
.PHONY: seed-evidence seed-demo-las deploy-apps readiness-test apps-catalog

# firstword = this Makefile (includes of forge.mk must not steal GEOX_ROOT)
GEOX_ROOT := $(abspath $(dir $(firstword $(MAKEFILE_LIST))))

seed-evidence:
	PYTHONPATH=src $(PYTHON) scripts/seed_demo_evidence.py

seed-demo-las:
	@mkdir -p $(GEOX_ROOT)/data/geox_las
	# Tracked fixtures only — recreate convenience aliases for local hydrate
	ln -sfn $(GEOX_ROOT)/fixtures/geox_smoke_test.las $(GEOX_ROOT)/data/geox_las/DEMO-KINABALU.las
	ln -sfn $(GEOX_ROOT)/fixtures/_DEMO_SYNTHETIC/DEMO_WELL_A_SANDAKAN.las $(GEOX_ROOT)/data/geox_las/DEMO_WELL_A.las
	ln -sfn $(GEOX_ROOT)/fixtures/_DEMO_SYNTHETIC/DEMO_WELL_B_SANDAKAN.las $(GEOX_ROOT)/data/geox_las/DEMO_WELL_B.las
	ln -sfn $(GEOX_ROOT)/fixtures/_DEMO_SYNTHETIC/DEMO_WELL_A_SANDAKAN.las $(GEOX_ROOT)/data/geox_las/DEMO_SANDAKAN_A.las
	ln -sfn $(GEOX_ROOT)/fixtures/_DEMO_SYNTHETIC/DEMO_WELL_B_SANDAKAN.las $(GEOX_ROOT)/data/geox_las/DEMO_SANDAKAN_B.las
	@if [ -f $(GEOX_ROOT)/data/geox_las/CHATGPT_VALIDATION_VOLVE_15_9_19.las ]; then \
	  ln -sfn $(GEOX_ROOT)/data/geox_las/CHATGPT_VALIDATION_VOLVE_15_9_19.las $(GEOX_ROOT)/data/geox_las/DEMO-VOLVE.las; \
	  ln -sfn $(GEOX_ROOT)/data/geox_las/CHATGPT_VALIDATION_VOLVE_15_9_19.las $(GEOX_ROOT)/data/geox_las/VOLVE_15_9_19.las; \
	fi
	@echo "✓ seed-demo-las — aliases under data/geox_las/ (not git-tracked)"

deploy-apps:
	@echo "→ Deploy WellDesk + active apps to public Caddy tree"
	mkdir -p /var/www/html/geox/apps
	rsync -a --delete apps/well-desk/ /var/www/html/geox/apps/well-desk/
	rsync -a apps/earth-volume/ /var/www/html/geox/apps/earth-volume/ 2>/dev/null || true
	rsync -a apps/judge-console/ /var/www/html/geox/apps/judge-console/ 2>/dev/null || true
	rsync -a apps/prospect-ui/ /var/www/html/geox/apps/prospect-ui/ 2>/dev/null || true
	rsync -a apps/geox-mcp-visual/ /var/www/html/geox/apps/geox-mcp-visual/ 2>/dev/null || true
	rsync -a apps/site/ /var/www/html/geox/apps/site/ 2>/dev/null || true
	cp -f apps/workbench-v1.html /var/www/html/geox/apps/workbench-v1.html 2>/dev/null || true
	cp -f apps/index.html /var/www/html/geox/apps/index.html
	rsync -a apps/well-desk/ /opt/geox/app/apps/well-desk/
	rsync -a resources/demo_wells.json /opt/geox/app/resources/demo_wells.json 2>/dev/null || mkdir -p /opt/geox/app/resources && cp resources/demo_wells.json /opt/geox/app/resources/
	$(MAKE) seed-demo-las
	chown -R www-data:www-data /var/www/html/geox/apps
	$(MAKE) seed-evidence
	systemctl restart geox-mcp
	@sleep 2
	@curl -sf http://127.0.0.1:8081/health | head -c 200; echo
	@echo "✓ deploy-apps complete"

readiness-test:
	PYTHONPATH=src $(PYTHON) -m pytest tests/test_mcp_apps_readiness.py tests/test_visual_image_publish.py tests/test_demo_well_hydrate.py -q --tb=line

apps-catalog:
	cp -f apps/index.html /var/www/html/geox/apps/index.html
	chown www-data:www-data /var/www/html/geox/apps/index.html
