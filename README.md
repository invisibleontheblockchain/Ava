# Ava

Open-source multi-agent orchestration platform — visual DAG canvas for long-horizon knowledge work. Built from the [Spine AI Engineering Blueprint](docs/SPEC.md) (Document 2). **Progress tracker:** [docs/BUILD.md](docs/BUILD.md) · [docs/ROADMAP.md](docs/ROADMAP.md)

**Status:** Phases 1–5 implemented in code (v1.0.0). Validate locally with `make test-phase1` … `make test-phase5`. See [docs/BUILD.md](docs/BUILD.md).

## Architecture (Hybrid Option C)

| Layer | Stack |
|-------|--------|
| Frontend | Next.js 15, React Flow v12, Zustand, Zod |
| API gateway | FastAPI 0.115+ |
| Agent runtime | LangGraph v1.2 + AsyncPostgresSaver |
| Queue | ARQ + Redis |
| Streaming | SSE via Redis Pub/Sub |
| Database | PostgreSQL 16 |

**Deployment constraint:** Run the API and worker on persistent Docker/VPS — not Vercel serverless or Lambda (runs exceed 60–300s).

## Quick start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+
- `OPENAI_API_KEY` (or compatible LiteLLM provider)

### 1. Infrastructure

```bash
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

docker compose up -d postgres redis
```

### 2. API + worker (local dev)

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export $(grep -v '^#' ../../.env | xargs)
python -m ava_api.db migrate
uvicorn ava_api.main:app --reload --port 8000
# separate terminal:
arq ava_api.worker.WorkerSettings
```

### 3. Web UI

```bash
cd apps/web
npm install
npm run dev
```

Open http://localhost:3000 — create a **Web → Prompt → Note** pipeline and run it.

### Phase 1 go/no-go

```bash
make setup && make infra && make test-phase1   # automated (MOCK_LLM)
# Real LLM: OPENAI_API_KEY + MOCK_LLM=false, then make api + worker + web
```

- [ ] Web block scrapes a URL (mock when `MOCK_LLM=true`)
- [ ] Prompt block receives upstream context
- [ ] Note block shows final output
- [ ] Token output streams via SSE
- [ ] Resume from checkpoint (`POST /runs/{id}/resume` or UI **Resume**)

Track progress in [docs/BUILD.md](docs/BUILD.md) — update checkboxes as work completes.

## Repository layout

```
apps/
  api/     # FastAPI + LangGraph + ARQ worker
  web/     # Next.js + React Flow canvas
docs/
  BUILD.md # Master build tracker (Phases 1–5, update as you go)
```

## License

Apache 2.0 (core). Enterprise features will live under a separate EE license per blueprint §8.
