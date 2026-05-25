.PHONY: infra api worker web test test-phase1 test-phase2 test-phase3 test-phase4 test-phase5 install setup

setup:
	cp -n .env.example .env 2>/dev/null || true
	cd apps/api && python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]" -q
	cd apps/web && npm install

infra:
	docker compose up -d postgres redis

api:
	cd apps/api && . .venv/bin/activate && \
		export $$(grep -v '^#' ../../.env 2>/dev/null | xargs) && \
		python -m ava_api.db migrate && \
		uvicorn ava_api.main:app --reload --host 0.0.0.0 --port 8000

worker:
	cd apps/api && . .venv/bin/activate && \
		export $$(grep -v '^#' ../../.env 2>/dev/null | xargs) && \
		arq ava_api.worker.WorkerSettings

web:
	cd apps/web && npm run dev

test:
	cd apps/api && . .venv/bin/activate && MOCK_LLM=true pytest -q

test-phase2: infra
	cd apps/api && . .venv/bin/activate && \
		export $$(grep -v '^#' ../../.env 2>/dev/null | xargs) && \
		export MOCK_LLM=true && \
		export DATABASE_URL=postgresql+asyncpg://ava:ava@localhost:5432/ava && \
		export LANGGRAPH_DATABASE_URL=postgresql://ava:ava@localhost:5432/ava && \
		export REDIS_URL=redis://localhost:6379/0 && \
		python ../../scripts/test_phase2.py

test-phase1: infra
	@echo "Waiting for postgres..."
	@sleep 3
	cd apps/api && . .venv/bin/activate && \
		export $$(grep -v '^#' ../../.env 2>/dev/null | xargs) && \
		export MOCK_LLM=true && \
		export DATABASE_URL=postgresql+asyncpg://ava:ava@localhost:5432/ava && \
		export LANGGRAPH_DATABASE_URL=postgresql://ava:ava@localhost:5432/ava && \
		export REDIS_URL=redis://localhost:6379/0 && \
		python ../../scripts/test_phase1.py

test-phase3: infra
	cd apps/api && . .venv/bin/activate && \
		export MOCK_LLM=true && \
		export DATABASE_URL=postgresql+asyncpg://ava:ava@localhost:5432/ava && \
		export REDIS_URL=redis://localhost:6379/0 && \
		python ../../scripts/test_phase3.py

test-phase4: infra
	cd apps/api && . .venv/bin/activate && \
		export MOCK_LLM=true && \
		export DATABASE_URL=postgresql+asyncpg://ava:ava@localhost:5432/ava && \
		export LANGGRAPH_DATABASE_URL=postgresql://ava:ava@localhost:5432/ava && \
		export REDIS_URL=redis://localhost:6379/0 && \
		python ../../scripts/test_phase4.py

test-phase5: infra
	cd apps/api && . .venv/bin/activate && \
		export MOCK_LLM=true && \
		python ../../scripts/test_phase5.py

load-test: infra
	cd apps/api && . .venv/bin/activate && \
		export MOCK_LLM=true && \
		python ../../scripts/load_test_swarm.py
