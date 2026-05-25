from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ava_api.config import get_settings
from ava_api.db import init_tables
from ava_api.platform.connectors import seed_connectors
from ava_api.platform.observability import setup_tracing
from ava_api.platform.mcp_server import mount_mcp
from ava_api.routes import (
    audit,
    auth,
    bench,
    canvases,
    connectors,
    marketplace,
    outputs,
    planning,
    runs,
    swarm,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_tables()
    from ava_api.db import get_session_factory

    async with get_session_factory()() as session:
        await seed_connectors(session)
        await session.commit()
    yield


app = FastAPI(
    title="Ava API",
    version="1.0.0",
    description="Multi-agent DAG orchestration — Phases 1–5",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(canvases.router)
app.include_router(runs.router)
app.include_router(outputs.router)
app.include_router(swarm.router)
app.include_router(planning.router)
app.include_router(connectors.router)
app.include_router(auth.router)
app.include_router(marketplace.router)
app.include_router(bench.router)
app.include_router(audit.router)

mount_mcp(app)
setup_tracing(app)


@app.get("/health")
async def health():
    from ava_api.platform.ee import is_ee_enabled

    s = get_settings()
    return {
        "status": "ok",
        "phase": 5,
        "mock_llm": s.mock_llm,
        "model": s.litellm_model,
        "ee": is_ee_enabled(),
        "collab_ws": s.collab_ws_url,
    }
