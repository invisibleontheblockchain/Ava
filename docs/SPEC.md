# Document 2 — Engineering Blueprint (Reference)

Canonical requirements from *Open-Source Spine AI Engineering Blueprint* (2026-05-25). Implementation tracker: [BUILD.md](./BUILD.md).

## Non-negotiables

1. **Hybrid Option C** — Next.js + FastAPI/LangGraph
2. **No serverless agent engine** — persistent Docker/VPS workers (60–300s+ runs)
3. **Checkpoint discipline** — LangGraph state = primitives + `output_ref`; blobs in Postgres/S3
4. **Apache 2.0 core + EE** open-core licensing

## Four-tier agents

| Tier | Responsibility |
|------|----------------|
| L1 | NL intake, 0–3 clarifications, Plan JSON, `interrupt_before` HITL |
| L2 | Plan → task DAG (nested LangGraph subgraph) |
| L2.5 | Persona subgraphs (Researcher, Analyst, Writer, Coder) + Send API |
| L3 | 17 block executors |

## 17 block types

`prompt`, `web`, `report`, `note`, `table`, `list`, `image`, `file`, `excel`, `presentation`, `dashboard`, `app`, `memo`, `youtube`, `code`, `connector`, `human_gate`

## Phase stack (Tables 11–15)

| Phase | Weeks | Key stack |
|-------|-------|-----------|
| 1 | 1–8 | React Flow, FastAPI, LangGraph single graph, ARQ, SSE, LiteLLM, 5 blocks |
| 2 | 9–16 | L2/L2.5 subgraphs, Send API, 10 blocks, pgvector memory, xlsxwriter |
| 3 | 17–24 | L1 HITL, FastMCP, OAuth PKCE, **Nango** vault, Drive/GitHub/Slack |
| 4 | 25–32 | Full artifacts, LiteLLM routing + rate limits, Y.js + awareness, 60+ min runs |
| 5 | 33–48 | 17 blocks, SSO, audit, marketplace, Typer CLI, GAIA ≥50%, Grafana |

## Connectors (§5)

- FastMCP Streamable HTTP — `tools` / `resources` / `prompts`
- Nango self-hosted — OAuth lifecycle, token refresh, MCP routing
- Connector registry — Postgres + `server/discover` on startup

## Deliverables (§6)

Artifacts return `artifact_id` + **presigned S3/R2 URL** on `BlockOutput.artifact_url`.

## CLI (Phase 5)

Commands: `ava init`, `ava start`, `ava upgrade` (spec names `spine` in PDF; Ava uses `ava`).
