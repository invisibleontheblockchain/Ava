# Public roadmap

Aligned with [BUILD.md](./BUILD.md) and Document 2 (48-week plan).

## Shipped (v1.0.0)

- Phase 1: Canvas DAG, SSE, checkpoints, 5 core blocks
- Phase 2: L2/L2.5 swarm, 10 blocks, memory, xlsx
- Phase 3: L1 planner, MCP/FastMCP, OAuth PKCE, Nango client, connectors
- Phase 4: Multi-model routing, artifacts, compaction, Y.js server, DLQ
- Phase 5: 17 blocks, EE gate, audit export, CLI, GAIA/DeepSearchQA harnesses

## Next (validation & hardening)

- [ ] CI green on `make test-phase1` … `test-phase5` with Docker
- [ ] Full Zustand ↔ Y.js bidirectional sync in web client
- [ ] Live Nango + Google Drive E2E (non-mock)
- [ ] Grafana dashboard JSON for OTel traces
- [ ] GAIA L3 ≥50% with real API keys

## Future

- ComfyUI self-hosted image pipeline
- Pandoc PDF export path
- DeepSearchQA full dataset integration
- GitHub Projects board (mirror this file)

Track detailed checkboxes in [BUILD.md](./BUILD.md).
