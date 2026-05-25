# Ava Architecture

Ava implements Document 2 Option C: **Next.js** canvas + **FastAPI/LangGraph** agent runtime.

## Tiers

| Tier | Module | Role |
|------|--------|------|
| L1 | `agents/l1_planner.py` | NL brief → clarifications → plan → HITL confirm |
| L2 | `agents/l2_subgraph.py`, `l2_decomposer.py` | Plan → parallel task batches |
| L2.5 | `agents/personas.py`, `swarm_graph.py` | Persona agents via LangGraph Send API |
| L3 | `executor/blocks.py` | 17 block executors |

## Platform services

- `platform/routing.py` — LiteLLM multi-model + ensemble
- `platform/memory.py` — agent memory (JSON embeddings; pgvector-ready)
- `platform/connectors.py` — MCP registry + mock OAuth
- `platform/compaction.py` — long-run context compaction
- `platform/reliability.py` — DLQ + circuit breaker
- `platform/ee.py` — Enterprise license gate

## Data

PostgreSQL: canvases, runs, block_outputs, planning_sessions, connectors, audit_logs, agent_memory.

LangGraph checkpoints: AsyncPostgresSaver (primitives + output refs only).

## Self-host

```bash
ava init && ava start --production
```

See [BUILD.md](./BUILD.md) for phase checklist.
