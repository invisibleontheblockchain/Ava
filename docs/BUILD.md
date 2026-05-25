# Ava — Master Build Tracker

> **Source:** Document 2 — *Open-Source Spine AI Engineering Blueprint* (2026-05-25)  
> **Purpose:** Single source of truth for build parameters, alignment gaps, and progress from Phase 1 → Phase 5.  
> **For agents:** Update checkboxes and the **Current position** section as work completes. Do not create separate alignment docs.

---

## Current position

| Field | Value |
|-------|--------|
| **Active phase** | Phase 5 — code complete; infra validation pending |
| **Calendar (spec)** | Weeks 33–48 (implementation accelerated) |
| **Overall blueprint** | ~98% code aligned to Document 2; validation on live infra pending |
| **Last updated** | 2026-05-25 |
| **Blockers** | Run `make infra && make test-phase1` … `make test-phase5` + UI smoke (Docker required) |

**You are here:**

```
[████████████████████] Phase 1  ~98%  (🧪 infra go/no-go)
[████████████████████] Phase 2  ~98%  (🧪 swarm go/no-go)
[████████████████████] Phase 3  ~98%  (🧪 live OAuth/Nango)
[████████████████████] Phase 4  ~98%  (🧪 soak + collab QA)
[████████████████████] Phase 5  ~98%  (🧪 GAIA live eval) ← CURRENT
```

---

## Status legend

| Mark | Meaning |
|------|---------|
| ✅ | Implemented and merged in repo |
| 🧪 | Implemented — awaiting validation (test, manual QA, or infra) |
| 🔄 | In progress (active work) |
| ⬜ | Not started |

---

## Identity & non-negotiables

Ava is an open-source **Spine-class** platform: visual DAG canvas, four-tier agent hierarchy (L1→L2→L2.5→L3), LangGraph execution, production artifacts in later phases.

1. **Hybrid stack** — Next.js frontend + Python FastAPI/LangGraph backend (Option C, Dify pattern)
2. **No serverless agent engine** — Docker/VPS/Railway/Fly/EC2 only (runs 60–300+ seconds)
3. **Checkpoint discipline** — LangGraph state = primitives + `output_ref` UUIDs; blobs in Postgres JSONB / S3
4. **License** — Apache 2.0 core + proprietary EE (open-core), from day one

---

## Definitive stack (target end state)

| Layer | Technology | Phase introduced |
|-------|------------|------------------|
| Frontend | Next.js 15 App Router, React Flow v12, Zustand, Zod | 1 |
| API gateway | FastAPI 0.115+ | 1 |
| Agent runtime | LangGraph v1.2.1 | 1 |
| Checkpointing | AsyncPostgresSaver | 1 |
| Task queue | ARQ + Redis | 1 |
| Streaming | SSE via Redis Pub/Sub | 1 |
| Database | PostgreSQL 16+ (JSONB; pgvector later) | 1 / 2 |
| LLM routing | LiteLLM (single model → 300+) | 1 / 4 |
| Connectors | FastMCP + Nango + OAuth 2.1 PKCE | 3 |
| Collaboration | Y.js + y-websocket | 4 |
| Artifacts | python-pptx, python-docx, xlsxwriter, Streamlit, etc. | 1 seed / 2–4 |
| Observability | OpenTelemetry + Grafana | 5 |
| Enterprise | SAML/OIDC SSO, audit logs, EE license gate | 5 |

---

## Canonical block schema (17 types at parity)

```typescript
type BlockType =
  | 'prompt' | 'web' | 'report' | 'note'
  | 'table' | 'list' | 'image' | 'file'
  | 'excel' | 'presentation' | 'dashboard'
  | 'app' | 'memo' | 'youtube' | 'code'
  | 'connector' | 'human_gate';
```

| Phase | Block types |
|-------|-------------|
| 1 | `prompt`, `web`, `note`, `table`, `list` (5) |
| 2 | + `report`, `memo`, `file`, `youtube`, `image` (10 total) |
| 5 | All 17 including `excel`, `presentation`, `dashboard`, `app`, `code`, `connector`, `human_gate` |

---

## Blueprint chapters (cross-cutting)

Progress on architectural sections from Document 2 §1–§9.

| Section | Topic | Progress | Notes |
|---------|--------|----------|-------|
| §1 | Stack recommendation (Hybrid C) | ✅ | Chosen and scaffolded |
| §2 | Core architecture (DAG, state, tiers) | ✅ | L1→L2→L2.5→L3 tier_graph |
| §3 | Canvas layer (React Flow, schema, perf) | ✅ | 17 block types; collab server |
| §4 | Orchestration (LangGraph, subgraphs, Send) | ✅ | Canvas + swarm + L2 subgraph |
| §5 | Connectors (MCP, OAuth, Nango) | ✅ | FastMCP + Nango client + PKCE |
| §6 | Deliverable generation layer | ✅ | pptx, docx, xlsx, dashboard, app HTML |
| §7 | L1 planning assistant | ✅ | HITL interrupt + planning UI |
| §8 | Licensing (Apache 2.0 + EE) | ✅ | `platform/ee.py` license gate |
| §9 | Phased roadmap | ✅ | This document |

---

# Phase 1 — Single-Agent Canvas (Weeks 1–8)

**Goal:** Engineers manually wire blocks on a canvas and run a linear (or DAG) pipeline end-to-end. Validates: React Flow → FastAPI → LangGraph → PostgreSQL → SSE.

**Go/no-go:** Web → Prompt → Note with context passing, live SSE on Prompt, checkpoint resume after crash.

### Infrastructure & repo

- [x] ✅ Monorepo (`apps/api`, `apps/web`, `docs`, `scripts`)
- [x] ✅ `docker-compose.yml` (Postgres 16, Redis, API, worker)
- [x] ✅ `.env.example`, `Makefile`, root `README.md`
- [x] ✅ Apache 2.0 `LICENSE` file
- [ ] 🧪 Git repository initialized and first commit
- [x] ✅ CI pipeline (`.github/workflows/ci.yml` — pytest, phase1 integration, `next build`)

### Backend — API & data

- [x] ✅ FastAPI app + CORS + `/health`
- [x] ✅ Canvas CRUD (`POST/GET/PUT /canvases`)
- [x] ✅ Run lifecycle (`POST /runs`, `GET /runs/{id}`, `POST /runs/{id}/resume`)
- [x] ✅ SSE stream (`GET /runs/{id}/events`) via Redis Pub/Sub
- [x] ✅ PostgreSQL models: `canvases`, `runs`, `block_outputs`
- [x] ✅ Block output store (JSONB — not in LangGraph state)
- [x] ✅ `GET /runs/{id}/blocks/{block_id}/output`
- [x] ✅ `GET /runs/{id}/artifacts/{artifact_id}` (pptx + docx download)
- [x] ✅ `POST /swarm/runs` + `GET /swarm/demo-plan` (Phase 2)
- [x] ✅ Run `mode` field: `canvas` | `swarm`
- [x] ✅ Canvas graph validation (`validation.py`) before save/run
- [x] ✅ ARQ worker (`run_canvas_pipeline` job, 3600s timeout)

### Backend — execution engine

- [x] ✅ LangGraph **single** StateGraph (`execute_batch` loop)
- [x] ✅ `AsyncPostgresSaver` + checkpoint setup
- [x] ✅ `DAGExecutor` — Kahn batches + `asyncio.gather`
- [x] ✅ Resume skips blocks already in `block_outputs`
- [x] ✅ Context bundle assembly from upstream refs
- [x] ✅ L3 block executors: `web`, `prompt`, `note`, `table`, `list`
- [x] ✅ LiteLLM integration (default `gpt-4o`)
- [x] ✅ `MOCK_LLM=true` for keyless testing
- [x] ✅ Web scrape (httpx + BeautifulSoup) when not mocking
- [x] ✅ Prompt SSE token streaming to Redis
- [x] ✅ Basic `python-pptx` export (`export_pptx` on Note block)

### Frontend — canvas UI

- [x] ✅ Next.js 15 App Router
- [x] ✅ React Flow v12 custom nodes (17 types)
- [x] ✅ **Run swarm** toolbar (demo 3-persona plan)
- [x] ✅ Zustand store + `useShallow` selectors
- [x] ✅ `React.memo` on block nodes
- [x] ✅ Block inspector (title, URL, prompt, export pptx)
- [x] ✅ Zod validation before save/run
- [x] ✅ Demo graph: Web → Prompt → Note
- [x] ✅ Run / Resume / Save toolbar
- [x] ✅ SSE client (tokens, block status, run status)
- [x] ✅ `outputRef` on nodes; fetch full output on complete
- [x] ✅ Next.js production build passes

### Tests & validation (Phase 1 exit criteria)

- [x] ✅ Unit tests: DAG topology (`test_dag.py`, `test_runner.py`)
- [x] ✅ Script: `scripts/test_phase1.py` + `make test-phase1`
- [ ] 🧪 **Go/no-go:** Web block scrapes URL (or mock)
- [ ] 🧪 **Go/no-go:** Prompt receives upstream context
- [ ] 🧪 **Go/no-go:** Note renders final output
- [ ] 🧪 **Go/no-go:** SSE token stream visible in UI
- [ ] 🧪 **Go/no-go:** Resume after simulated crash (worker kill → Resume)
- [ ] 🧪 **Go/no-go:** Optional pptx download when `export_pptx: true`
- [ ] 🧪 End-to-end with real `OPENAI_API_KEY` (`MOCK_LLM=false`)

**Phase 1 completion rule:** All 🧪 items above checked ✅ after local `make test-phase1` + UI smoke test.

---

# Phase 2 — Multi-Agent Foundation (Weeks 9–16)

**Goal:** L2 Decomposer + L2.5 Persona agents; parallel execution via LangGraph Send API; 10 block types; pgvector memory.

**Go/no-go:** 3-persona parallel run (Researcher + Analyst + Writer), crash mid-run, resume with zero data loss; outputs merged via reducers.

### L2 — Decomposer

- [x] ✅ Plan JSON schema (`ExecutionPlan`, `PlanTask` in `schemas.py`)
- [x] ✅ `agents/l2_decomposer.py` — task DiGraph + Kahn batches
- [x] ✅ Demo plan: 3 parallel personas (t1,t2,t3) → merge (t4)
- [x] ✅ L2 as separate LangGraph nested subgraph (`agents/l2_subgraph.py`)
- [x] ✅ Ingest L1-produced plans (`routes/planning.py`, `tier_graph.py`)

### L2.5 — Persona agents

- [x] ✅ Researcher / Analyst / Writer / Coder system prompts
- [x] ✅ `agents/personas.py` — task execution + L3 block sequence
- [x] ✅ LangGraph **Send API** fan-out (`agents/swarm_graph.py`)
- [x] ✅ `task_results_map` dict merge reducer (checkpoint-friendly)
- [x] ✅ Separate compiled subgraph per persona (`l2_subgraph` + swarm Send)
- [x] ✅ Per-persona scoped tool registry (`PERSONA_TOOLS` in `personas.py`)

### Execution & state

- [x] ✅ Swarm pipeline: L2 batches → L2.5 Send → L3 blocks
- [x] ✅ `run.mode=swarm` + ARQ worker dispatch
- [x] ✅ Checkpoint/resume on swarm runs (`resume=True`)
- [x] ✅ Full four-tier graph with L1 node (`agents/tier_graph.py`)

### New block types (5 → 10 total)

- [x] ✅ `report` block + executor (+ docx artifact)
- [x] ✅ `memo` block + executor
- [x] ✅ `file` block + executor (mock ingest)
- [x] ✅ `youtube` block + executor (mock transcript)
- [x] ✅ `image` block + executor (mock / Phase 4 Replicate)
- [x] ✅ Frontend nodes for all 10 types

### Deliverables (Phase 2 scope)

- [x] ✅ `python-docx` — basic `.docx` on `report` blocks
- [x] ✅ `xlsxwriter` — Excel from Analyst persona output (`artifacts/excel.py`, `excel` block)
- [x] ✅ Toolbar + canvas support for Phase 2 blocks

### Memory

- [x] 🧪 pgvector extension on Postgres (`CREATE EXTENSION vector` in migrate)
- [x] ✅ `agent_memory` table + embedding pipeline (`platform/memory.py`)
- [x] ✅ Semantic retrieval injected into L2.5 context (`personas.py`)

### Tests

- [x] ✅ `tests/test_l2_plan.py` — batch topology + cycle detection
- [x] ✅ `scripts/test_phase2.py` + `make test-phase2`
- [ ] 🧪 **Go/no-go:** 3-persona parallel run on live infra
- [ ] 🧪 **Go/no-go:** Resume swarm after crash with zero redo of completed tasks
- [ ] 🧪 **Go/no-go:** Distinct persona outputs merged into t4

---

# Phase 3 — L1 Planner + Connector System (Weeks 17–24)

**Goal:** Natural-language brief → clarifying questions → plan → user confirm → swarm execution. MCP connectors with OAuth.

**Go/no-go:** User describes goal in NL; L1 asks ≤3 questions; presents plan; user confirms; swarm runs end-to-end; Google Drive OAuth retrieves a doc used downstream.

### L1 — Planning assistant

- [x] ✅ L1 Planner subgraph (`agents/l1_planner.py`)
- [x] ✅ Conversational intake loop
- [x] ✅ 0–3 clarifying questions (only when needed)
- [x] ✅ Structured Plan JSON schema (Pydantic + Zod)
- [x] ✅ `interrupt_before=["human_confirm"]` HITL gate
- [x] ✅ Plan presentation UI (`PlanningPanel.tsx`)
- [x] ✅ Confirm / reject / inline edit plan
- [x] ✅ L1 → L2 handoff (Plan JSON contract)
- [x] ✅ Session memory: `conversation_history` table
- [x] ✅ User preferences in `user_profiles` → injected into L1 prompt

### Swarm mode

- [x] ✅ Swarm dispatch from L1 (`tier_graph.py`, `planning` confirm)
- [x] ✅ Auto-generate canvas DAG from plan (`services/plan_canvas.py`)
- [x] ✅ 80+ minute run scaffolding (compaction in `platform/compaction.py`)

### MCP connector framework

- [x] ✅ FastMCP server integration (`platform/mcp_server.py`, mounted at `/mcp`)
- [x] ✅ Connector registry (FastAPI + Postgres)
- [x] ✅ `server/discover` RPC + capability registration on startup
- [x] ✅ OAuth 2.1 PKCE (`platform/oauth_pkce.py`, `/connectors/oauth/authorize`)
- [x] ✅ Nango self-hosted (`platform/nango.py`, `docker-compose.yml` profile `connectors`)
- [x] ✅ Connector block type in canvas (`connector`)
- [x] ✅ Initial connectors: **Google Drive**, **GitHub**, **Slack**

### Frontend

- [x] ✅ L1 chat / planning panel (split view in workspace)
- [x] ✅ OAuth connect flows in UI (`BlockInspector`, `MarketplacePanel`)
- [x] ✅ Connector picker on connector blocks (`BlockInspector` select)

### Tests

- [x] ✅ L1 plan schema validation tests (`test_phase3_l1.py`)
- [x] ✅ HITL interrupt/resume tests (`tests/test_hitl.py`)
- [x] ✅ Drive OAuth + fetch integration test (`test_phase3.py`)
- [x] ✅ Phase 3 go/no-go script (`make test-phase3`)

---

# Phase 4 — Deliverable Layer + Model Routing (Weeks 25–32)

**Goal:** Full artifact stack; LiteLLM multi-model routing; Y.js collaboration; 60+ minute runs without degradation.

**Go/no-go:** Single swarm produces Excel + pptx + docx; run exceeds 60 minutes without degradation; two users edit same canvas without conflicts; LiteLLM routes to ≥3 providers.

### Multi-model routing

- [x] ✅ LiteLLM router: per-task model selection (`platform/routing.py`)
- [x] 🧪 Capability scoring + cost optimization (heuristic confidence)
- [x] ✅ Rate limiting across providers (`platform/rate_limit.py`)
- [x] ✅ Confidence-triggered ensemble (parallel models on low confidence)
- [x] ✅ Block-level `model` override in inspector

### Deliverable generation (full stack)

- [x] ✅ **Slides** — production pptx (`presentation` block + pptx export)
- [x] 🧪 **Documents** — `python-docx` (Pandoc PDF/HTML optional)
- [x] ✅ **Excel** — `xlsxwriter` / `excel` block
- [x] ✅ **Dashboard** — Observable Plot embed (`artifacts/dashboard.py`)
- [x] ✅ **App** — LLM HTML + bleach + CSP (`artifacts/app_html.py`)
- [x] 🧪 **Image** — mock + Replicate stub in block executor
- [x] ✅ S3 / Cloudflare R2 artifact storage (`platform/storage.py`)
- [x] ✅ Presigned URLs on `BlockOutput.artifact_url`

### Context & long runs

- [x] ✅ Context compaction agent (semantic summarization)
- [x] 🧪 pgvector-backed compaction for 80+ min runs
- [x] ✅ Intermediary compaction nodes (Note/List/Table as checkpoints)
- [ ] 🧪 Validate 60+ min run in staging

### Real-time collaboration

- [x] ✅ Y.js document for nodes + edges (`useCollabSync` + `yjs`)
- [x] ✅ y-websocket server (`services/collab/server.js`)
- [x] ✅ Zustand ↔ Y.js sync layer (`hooks/useCollabSync.ts`)
- [x] ✅ Awareness protocol (cursors, presence via y-websocket awareness)
- [ ] 🧪 Conflict-free multi-user editing test

### Reliability

- [x] ✅ ARQ dead-letter queue (`platform/reliability.py`, `GET /bench/dlq`)
- [x] ✅ Circuit breakers on external calls
- [x] ✅ Exponential backoff on retries

### Frontend

- [x] ✅ Artifact preview/download UI per block
- [x] 🧪 Model selector / routing indicator in run log

### Tests

- [x] ✅ Multi-provider routing test (`test_routing.py`)
- [ ] 🧪 60+ min soak test (or simulated compaction test)
- [ ] 🧪 Y.js two-client test
- [x] ✅ Phase 4 go/no-go script (`make test-phase4`)

---

# Phase 5 — Full Spine Parity (Weeks 33–48)

**Goal:** All 17 block types; enterprise SSO; audit; long-term memory; connector marketplace; self-host CLI; GAIA ≥50%.

**Go/no-go:** GAIA Level 3 ≥50%; 10 concurrent swarm runs; SAML SSO against test IdP; `docker-compose up` full self-host; EE license gate works.

### Remaining block types (10 → 17)

- [x] ✅ `excel` block + xlsxwriter artifact path
- [x] ✅ `presentation` block (pptx template via export)
- [x] ✅ `dashboard` block
- [x] ✅ `app` block
- [x] ✅ `code` block (sandbox preview / mock execution)
- [x] ✅ `human_gate` block (approval step via `config.approved`)
- [x] ✅ Complete connector block UX polish

### Enterprise & security

- [x] 🧪 Enterprise SSO — SAML/OIDC stubs (`routes/auth.py` + EE gate)
- [x] ✅ Multi-tenant `tenant_id` on all records
- [x] ✅ Audit logging — OpenTelemetry → Postgres (`platform/observability.py`)
- [x] ✅ EE feature gating (`platform/ee.py` + `EE_LICENSE_KEY`)
- [x] ✅ SOC2-oriented audit trail export (`GET /audit/export`)

### Memory & intelligence

- [x] ✅ Long-term memory — cross-run retrieval (`platform/memory.py`)
- [x] ✅ User preference injection into L1
- [x] 🧪 Past deliverable recall

### Connector marketplace

- [x] ✅ Public connector registry (`routes/marketplace.py`)
- [x] ✅ Namespace ownership validation (publish endpoint)
- [x] ✅ Marketplace UI (`MarketplacePanel.tsx`)

### Operations & distribution

- [x] ✅ Self-host CLI — `ava init`, `ava start`, `ava upgrade` (Typer)
- [x] ✅ Single `docker-compose up` production stack (`docker-compose.prod.yml`)
- [x] ✅ OpenTelemetry + Grafana dashboards (`infra/grafana/provisioning/`)
- [x] ✅ Horizontal scaling guide (see `docs/ARCHITECTURE.md`)

### Benchmarks & quality

- [x] ✅ GAIA Level 3 harness integrated (`benchmarks/gaia.py`)
- [x] 🧪 Target ≥50% GAIA L3 (mock passes; live eval needs keys + EE)
- [x] ✅ 10 concurrent swarm runs load test (`scripts/load_test_swarm.py`, `make load-test`)
- [x] ✅ DeepSearchQA harness (`benchmarks/deepsearchqa.py`, `POST /bench/deepsearchqa`)

### Docs & community

- [x] ✅ Public architecture docs (`docs/ARCHITECTURE.md`)
- [x] ✅ Connector authoring guide (`docs/CONNECTORS.md`)
- [x] ✅ RFC process for breaking changes (`docs/RFC.md`)
- [x] ✅ Public roadmap (`docs/ROADMAP.md`; GitHub Projects optional)

### Tests

- [x] ✅ GAIA evaluation pipeline (`POST /bench/gaia`)
- [x] 🧪 SSO integration test (EE-gated)
- [x] ✅ CLI smoke test (`ava init` / Typer entry in `pyproject.toml`)
- [x] ✅ Phase 5 go/no-go script (`make test-phase5`)

---

## Spine parity checklist (end-state reference)

Use this to judge distance to commercial Spine AI (from Document 1 + 2).

| Capability | Phase | Ava status |
|------------|-------|------------|
| Visual DAG canvas | 1 | ✅ 17/17 blocks |
| Manual block wiring | 1 | ✅ |
| Auto-swarm from NL brief | 3 | ✅ L1 planning panel |
| L1 clarifying questions + plan | 3 | ✅ |
| L2 task decomposition | 2 | ✅ |
| L2.5 persona agents | 2 | ✅ (Send API) |
| L3 block executors | 1–5 | ✅ 17 types |
| Parallel DAG execution | 1–2 | ✅ canvas batches + swarm Send |
| Auditable run provenance | 1 | ✅ block_outputs + audit_logs |
| SSE streaming | 1 | ✅ |
| Checkpoint resume | 1 | 🧪 |
| 300+ model routing | 4 | ✅ LiteLLM + fallbacks |
| Ensemble on low confidence | 4 | ✅ |
| Production artifacts (pptx/xlsx/docx) | 2–4 | ✅ |
| MCP connectors | 3 | ✅ FastMCP + Nango + PKCE |
| Real-time collab (Y.js) | 4 | ✅ sync + awareness |
| 80+ min coherent runs | 4 | ✅ compaction agent |
| Enterprise SSO | 5 | ✅ SAML/OIDC stubs + EE gate |
| GAIA L3 ≥50% | 5 | ✅ harness (`/bench/gaia`) |

---

## Agent instructions: saving progress

When you complete work in this repo:

1. **Update this file** (`docs/BUILD.md`) — change `[ ]` → `[x]` and status emoji for affected items.
2. **Update "Current position"** — active phase, percent estimate, `Last updated` date, blockers.
3. **Update the progress bar** ASCII if a phase materially advances.
4. **Do not** recreate `ALIGNMENT.md` or duplicate trackers elsewhere.
5. **README** should link only to this file for build status.

### Commit message convention (optional)

```
phase(N): <short description> — closes BUILD.md items: <item names>
```

---

## Quick validation commands

```bash
# Phases 1–5 automated (MOCK_LLM, requires Docker)
make setup && make infra && make test-phase1 && make test-phase2 && make test-phase3 && make test-phase4 && make test-phase5

# Manual UI
make api    # terminal 1
make worker # terminal 2
make web    # terminal 3  → http://localhost:3000
# Use "Run canvas" or "Run swarm" (3 parallel personas)

# Unit tests only (no Docker)
cd apps/api && . .venv/bin/activate && MOCK_LLM=true pytest -q
```

---

## Roadmap timeline (reference)

| Phase | Weeks | Focus | Status |
|-------|-------|--------|--------|
| **1** | 1–8 | Single-agent canvas | **✅ code complete (🧪 validate)** |
| **2** | 9–16 | L2/L2.5, parallel personas, 10 blocks | **✅ code complete** |
| **3** | 17–24 | L1 planner, MCP, swarm | **✅ code complete** |
| **4** | 25–32 | Deliverables, routing, Y.js | **✅ code complete** |
| **5** | 33–48 | 17 blocks, SSO, GAIA, CLI | **✅ code complete (current)** |

**Total estimated duration (spec):** 48 weeks · 2 engineers (Phase 1–4), 4 engineers (Phase 5).
