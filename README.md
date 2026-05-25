<p align="center">
  <img src="https://img.shields.io/badge/status-Phase%205%20Complete-6366f1?style=for-the-badge" alt="Status" />
  <img src="https://img.shields.io/badge/python-≥3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Next.js-15-000000?style=for-the-badge&logo=nextdotjs" alt="Next.js" />
  <img src="https://img.shields.io/badge/license-Apache%202.0-green?style=for-the-badge" alt="License" />
</p>

<h1 align="center">🤖 Ava</h1>

<p align="center">
  <strong>Open-source multi-agent orchestration platform with a visual DAG canvas.</strong><br/>
  Build, connect, and run complex AI workflows — visually.<br/><br/>
  <em>Drag blocks. Wire agents. Ship deliverables.</em>
</p>

---

## ✨ What is Ava?

Ava is a **visual AI workflow engine** that lets you orchestrate multi-agent pipelines on an infinite canvas. Instead of chatting with a single LLM, you build directed acyclic graphs (DAGs) of specialized blocks — web scrapers, prompts, reports, spreadsheets, presentations — and Ava's four-tier agent hierarchy executes them with real-time streaming output.

**Think:** Figma meets AI agents.

### What you can do today

- 🎨 **Visual Canvas** — Drag-and-drop 17 block types onto an infinite React Flow canvas
- 🔗 **Wire Pipelines** — Connect blocks into DAGs that execute in topological order
- 🤖 **Multi-Agent Swarms** — Fan out work to Researcher, Analyst, Writer, and Coder personas in parallel
- 📊 **Real Deliverables** — Auto-generate `.docx`, `.xlsx`, `.pptx`, dashboards, and sanitized HTML apps
- 🔌 **Connectors** — Pull data from Google Drive, GitHub, and Slack via MCP + OAuth
- 👁️ **Live Streaming** — Watch blocks light up with token-by-token output via SSE
- ⏸️ **Human-in-the-Loop** — Pause runs at gate blocks for review, then resume
- 🔄 **Crash Recovery** — Refresh and hit Resume — execution picks up from the last completed block
- 🧠 **Agent Memory** — Cross-run retrieval with pgvector embeddings
- 👥 **Real-time Collaboration** — Multi-user canvas editing via Y.js + WebSocket

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js 15 Frontend                       │
│         React Flow Canvas · Zustand · Y.js Collab            │
└────────────────────────┬────────────────────────────────────┘
                         │ REST + SSE
┌────────────────────────▼────────────────────────────────────┐
│                   FastAPI Gateway (:8000)                     │
│    10 Route Modules · CORS · OTel · Rate Limiting            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐  ┌─────────────┐ │
│  │   L1    │→ │    L2    │→ │   L2.5    │→ │     L3      │ │
│  │ Planner │  │Decomposer│  │  Personas │  │  Executors  │ │
│  │         │  │          │  │ (Send API)│  │ (17 blocks) │ │
│  └─────────┘  └──────────┘  └───────────┘  └─────────────┘ │
│                                                              │
│  LangGraph Checkpointing · LiteLLM Routing · ARQ Workers    │
├──────────────────────────────────────────────────────────────┤
│  PostgreSQL 16      │  Redis 7        │  Nango (OAuth)       │
│  pgvector · JSONB   │  ARQ · Pub/Sub  │  MCP Connectors      │
└──────────────────────────────────────────────────────────────┘
```

### Four-Tier Agent Hierarchy

| Tier | Role | What it does |
|------|------|-------------|
| **L1 Planner** | Intake & Planning | Takes a natural language brief → asks 0–3 clarifying questions → generates an execution plan → pauses for human confirmation |
| **L2 Decomposer** | Task DAG | Breaks the plan into a dependency graph of tasks using Kahn's algorithm, producing parallel batches |
| **L2.5 Personas** | Specialist Agents | Fans out tasks to `researcher`, `analyst`, `writer`, and `coder` persona agents via LangGraph's Send API |
| **L3 Executors** | Block Runtime | Executes each of the 17 block types — LLM calls, web scraping, artifact generation, connector fetches |

---

## 🧱 17 Block Types

| Block | Description | Phase |
|-------|-------------|-------|
| `prompt` | LLM completion with model routing | 1 |
| `web` | URL fetch + content extraction | 1 |
| `note` | Text output (optional `.pptx` export) | 1 |
| `table` | Structured data extraction | 1 |
| `list` | Enumerated outputs | 1 |
| `report` | Long-form `.docx` generation | 2 |
| `memo` | Short-form analysis documents | 2 |
| `file` | Generic file handling | 2 |
| `youtube` | YouTube transcript extraction | 2 |
| `image` | Image generation (Replicate) | 2 |
| `excel` | `.xlsx` spreadsheet generation | 5 |
| `presentation` | `.pptx` slide decks | 5 |
| `dashboard` | Observable Plot HTML dashboards | 5 |
| `app` | LLM-generated HTML micro-apps (sandboxed) | 5 |
| `code` | Code generation + execution | 5 |
| `connector` | External data via MCP + OAuth | 5 |
| `human_gate` | Pause for human approval | 5 |

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version |
|------------|---------|
| Python | ≥ 3.11 |
| Node.js | ≥ 20 |
| Docker & Docker Compose | Latest |
| PostgreSQL | 16+ (or use Docker) |
| Redis | 7+ (or use Docker) |

### 1. Clone & Configure

```bash
git clone git@github.com:invisibleontheblockchain/Ava.git
cd Ava
cp .env.example .env
```

Edit `.env` with your API keys. For keyless testing, ensure `MOCK_LLM=true` is set.

### 2. Start Infrastructure

```bash
# Option A: Docker (recommended)
docker compose up -d postgres redis

# Option B: Local services (Homebrew)
brew install postgresql@16 redis
brew services start postgresql@16
brew services start redis
createuser -s ava
createdb -O ava ava
psql -d ava -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 3. Install & Run

```bash
# One-command setup
make setup

# Terminal 1 — API server
make api

# Terminal 2 — Background worker (processes pipeline runs)
make worker

# Terminal 3 — Web UI
make web
```

Open **http://localhost:3000** — you'll see the canvas.

### 4. Verify Everything Works

```bash
# Run all phase tests sequentially
make test-phase1
make test-phase2
make test-phase3
make test-phase4
make test-phase5

# Load test — 10 concurrent swarm runs
make load-test
```

---

## 📁 Project Structure

```
Ava/
├── apps/
│   ├── api/                          # Python backend
│   │   ├── src/ava_api/
│   │   │   ├── agents/               # L1 planner, L2 decomposer, personas, swarm graph
│   │   │   ├── artifacts/            # PPTX, DOCX, XLSX, dashboard, app generators
│   │   │   ├── executor/             # Block executors, DAG runner, pipeline engine
│   │   │   ├── platform/             # LLM routing, memory, connectors, auth, storage
│   │   │   ├── routes/               # 10 FastAPI route modules
│   │   │   ├── benchmarks/           # GAIA & DeepSearchQA harnesses
│   │   │   ├── services/             # Run management, events, artifacts, plan→canvas
│   │   │   ├── cli/                  # Typer CLI (ava init/start/upgrade)
│   │   │   ├── main.py               # FastAPI app entrypoint
│   │   │   ├── worker.py             # ARQ worker config
│   │   │   ├── db.py                 # SQLAlchemy models + migrations
│   │   │   └── schemas.py            # Pydantic schemas (BlockType, ExecutionPlan, etc.)
│   │   └── tests/                    # Unit tests (pytest)
│   │
│   └── web/                          # Next.js 15 frontend
│       └── src/
│           ├── components/
│           │   ├── blocks/            # BaseBlock node renderer
│           │   ├── canvas/            # Workspace, toolbar, inspector, flow canvas
│           │   ├── planning/          # L1 planning chat panel
│           │   └── marketplace/       # Connector marketplace panel
│           ├── hooks/                 # useCollabSync (Y.js)
│           ├── lib/                   # API client, graph utils, types, validation
│           └── store/                 # Zustand canvas store
│
├── services/
│   └── collab/                       # Y.js WebSocket server for real-time collab
│
├── scripts/                          # Phase validation scripts + load tests
├── docs/                             # Architecture, spec, build guide, roadmap, RFC
├── infra/                            # Grafana provisioning
├── docker-compose.yml                # Dev infrastructure
├── docker-compose.prod.yml           # Production deployment
└── Makefile                          # All dev commands
```

---

## 🔌 API Reference

All endpoints are served from `http://localhost:8000`.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check + phase info |
| `/canvases` | POST | Create a new canvas |
| `/canvases/{id}` | GET / PUT | Retrieve or update canvas graph |
| `/runs` | POST | Start a pipeline run for a canvas |
| `/runs/{id}` | GET | Get run status |
| `/runs/{id}/resume` | POST | Resume a paused/crashed run |
| `/runs/{id}/events` | GET (SSE) | Real-time streaming events |
| `/runs/{id}/blocks/{block_id}/output` | GET | Get block output |
| `/runs/{id}/artifacts/{artifact_id}` | GET | Download generated artifact |
| `/swarm/runs` | POST | Start a multi-persona swarm run |
| `/planning/sessions` | POST | Start L1 planning from a brief |
| `/planning/sessions/{id}/confirm` | POST | Confirm plan and start execution |
| `/connectors` | GET | List available connectors |
| `/connectors/fetch` | POST | Fetch data from a connector |
| `/marketplace/connectors` | GET | Browse connector catalog |
| `/bench/gaia` | POST | Run GAIA benchmark |
| `/bench/dlq` | GET | Inspect dead-letter queue |
| `/mcp` | — | MCP Streamable HTTP endpoint |

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | PostgreSQL async URL (`postgresql+asyncpg://...`) |
| `LANGGRAPH_DATABASE_URL` | Yes | — | PostgreSQL sync URL (for LangGraph checkpointing) |
| `REDIS_URL` | Yes | — | Redis URL for task queue + SSE pub/sub |
| `OPENAI_API_KEY` | No* | — | LLM provider key (*not needed if `MOCK_LLM=true`) |
| `MOCK_LLM` | No | `false` | Use mock LLM responses (no API key needed) |
| `LITELLM_MODEL` | No | `gpt-4o` | Default LLM model for routing |
| `ARTIFACTS_DIR` | No | `data/artifacts` | Local artifact storage path |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Allowed CORS origins |
| `STORAGE_BACKEND` | No | `local` | `local` or `s3` for artifact storage |
| `EE_LICENSE_KEY` | No | — | Unlock enterprise features (SSO, audit export) |
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | API URL for the frontend |

See [`.env.example`](.env.example) for the complete list.

---

## 🧪 Testing

```bash
# Unit tests (no Docker required)
cd apps/api && source .venv/bin/activate
MOCK_LLM=true pytest -q

# Integration tests (require Docker infra)
make test-phase1    # Canvas DAG pipeline + block execution
make test-phase2    # Multi-persona swarm fan-out
make test-phase3    # L1 planning + connectors
make test-phase4    # Routing, artifacts, compaction
make test-phase5    # Marketplace, auth, GAIA stub

# Load testing
make load-test      # 10 concurrent swarm runs
```

---

## 🐳 Production Deployment

```bash
# Build and run all services
docker compose -f docker-compose.prod.yml up -d

# Or use the CLI
pip install ava-api
ava init
ava start --production
```

The production compose file includes the API, worker, web frontend, PostgreSQL, Redis, and Nango for connectors.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, data flow, and component relationships |
| [SPEC.md](docs/SPEC.md) | Full engineering specification (Spine Blueprint) |
| [BUILD.md](docs/BUILD.md) | Detailed build & deployment instructions |
| [CONNECTORS.md](docs/CONNECTORS.md) | MCP connector development guide |
| [ROADMAP.md](docs/ROADMAP.md) | Current status and upcoming milestones |
| [RFC.md](docs/RFC.md) | RFC process for schema and API changes |

---

## 🗺️ Roadmap

- [x] Phase 1 — Canvas DAG pipeline with 5 block types
- [x] Phase 2 — Multi-persona swarm execution (Send API)
- [x] Phase 3 — L1 planning + MCP connectors + OAuth
- [x] Phase 4 — Model routing, artifact generation, context compaction
- [x] Phase 5 — 17 block types, marketplace, benchmarks, auth
- [ ] CI pipeline green on all phases
- [ ] Full Zustand ↔ Y.js bidirectional sync
- [ ] Live Nango + Google Drive E2E
- [ ] Grafana dashboards for OTel traces
- [ ] GAIA Level 3 ≥ 50% with real API keys
- [ ] ComfyUI self-hosted image pipeline
- [ ] Pandoc PDF export

---

## 🤝 Contributing

Contributions are welcome! Please read the [RFC process](docs/RFC.md) before proposing changes to public APIs, block schemas, or checkpoint formats.

```bash
# Setup dev environment
make setup

# Run linting
cd apps/api && source .venv/bin/activate
ruff check src/ tests/

# Run tests
MOCK_LLM=true pytest -q
```

---

## 📄 License

[Apache License 2.0](LICENSE) — Core platform is fully open source.

Enterprise features (SSO, audit export, advanced connectors) are gated behind an optional `EE_LICENSE_KEY`.

---

<p align="center">
  <sub>Built with ❤️ by the Ava contributors</sub>
</p>
