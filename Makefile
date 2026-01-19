# AX POC Project Makefile
# Usage: make <target>

.PHONY: help install dev test lint build docker clean

# Default target
help:
	@echo "AX POC Project Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install      Install all dependencies"
	@echo "  make install-fe   Install frontend dependencies"
	@echo "  make install-be   Install backend dependencies"
	@echo "  make install-hooks Install pre-commit hooks"
	@echo ""
	@echo "Development:"
	@echo "  make dev          Start development servers"
	@echo "  make dev-fe       Start frontend dev server"
	@echo "  make dev-be       Start backend dev server"
	@echo ""
	@echo "Testing:"
	@echo "  make test         Run all tests"
	@echo "  make test-fe      Run frontend tests"
	@echo "  make test-be      Run backend tests"
	@echo "  make test-e2e     Run E2E tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint         Run all linters"
	@echo "  make lint-fe      Run frontend linter"
	@echo "  make lint-be      Run backend linter"
	@echo "  make format       Format all code"
	@echo ""
	@echo "Build:"
	@echo "  make build        Build all"
	@echo "  make build-fe     Build frontend"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up    Start all services"
	@echo "  make docker-down  Stop all services"
	@echo "  make docker-logs  Show logs"
	@echo "  make docker-build Build all images"
	@echo ""
	@echo "Utilities:"
	@echo "  make health       Check all service health"
	@echo "  make clean        Clean build artifacts"

# ============================================================
# Setup
# ============================================================

install: install-fe install-be install-hooks
	@echo "All dependencies installed"

install-fe:
	cd web-ui && npm ci

install-be:
	cd gateway-api && pip install -r requirements.txt

install-hooks:
	pip install pre-commit
	pre-commit install

# ============================================================
# Development
# ============================================================

dev:
	@echo "Starting development servers..."
	@echo "Frontend: http://localhost:5173"
	@echo "Backend: http://localhost:8000"
	@make -j2 dev-fe dev-be

dev-fe:
	cd web-ui && npm run dev

dev-be:
	cd gateway-api && uvicorn api_server:app --reload --host 0.0.0.0 --port 8000

# ============================================================
# Testing
# ============================================================

test: test-fe test-be
	@echo "All tests passed"

test-fe:
	cd web-ui && npm run test:run

test-be:
	cd gateway-api && pytest tests/ -v --tb=short -q

test-e2e:
	cd web-ui && npx playwright test

test-e2e-ui:
	cd web-ui && npx playwright test --ui

# ============================================================
# Code Quality
# ============================================================

lint: lint-fe lint-be
	@echo "All linting passed"

lint-fe:
	cd web-ui && npm run lint

lint-be:
	cd gateway-api && ruff check . --ignore E501

format:
	cd gateway-api && ruff format .
	cd web-ui && npm run lint -- --fix

# ============================================================
# Build
# ============================================================

build: build-fe
	@echo "Build complete"

build-fe:
	cd web-ui && npm run build

# ============================================================
# Docker
# ============================================================

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-build:
	docker-compose build

docker-restart:
	docker-compose restart

docker-clean:
	docker-compose down -v
	docker system prune -f

# ============================================================
# Utilities
# ============================================================

health:
	@echo "Checking service health..."
	@for port in 5002 5003 5004 5005 5006 5007 5008 5009 5010 5011 5012 5013 5014 5015 5016 5018 5019 5020 5021 8000; do \
		status=$$(curl -s http://localhost:$$port/health 2>/dev/null | grep -o '"status":"[^"]*"' | cut -d'"' -f4); \
		if [ "$$status" = "healthy" ]; then \
			echo "  Port $$port: healthy"; \
		else \
			echo "  Port $$port: unreachable"; \
		fi; \
	done

clean:
	rm -rf web-ui/dist
	rm -rf web-ui/node_modules/.cache
	rm -rf gateway-api/__pycache__
	rm -rf gateway-api/.pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean complete"

# ============================================================
# CI/CD Simulation
# ============================================================

ci: lint test build
	@echo "CI checks passed"

ci-quick: lint-fe lint-be
	@echo "Quick CI checks passed"
