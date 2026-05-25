from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ava_api.db import CanvasModel, get_db
from ava_api.schemas import CanvasGraph, CanvasResponse, CreateCanvasRequest
from ava_api.validation import CanvasValidationError, validate_canvas_graph

router = APIRouter(prefix="/canvases", tags=["canvases"])


@router.post("", response_model=CanvasResponse)
async def create_canvas(body: CreateCanvasRequest, db: AsyncSession = Depends(get_db)):
    graph = body.graph or CanvasGraph(blocks=[], edges=[])
    row = CanvasModel(name=body.name, graph=graph.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return CanvasResponse(id=row.id, name=row.name, graph=CanvasGraph.model_validate(row.graph))


@router.get("/{canvas_id}", response_model=CanvasResponse)
async def get_canvas(canvas_id: UUID, db: AsyncSession = Depends(get_db)):
    row = await db.get(CanvasModel, canvas_id)
    if not row:
        raise HTTPException(404, "Canvas not found")
    return CanvasResponse(id=row.id, name=row.name, graph=CanvasGraph.model_validate(row.graph))


@router.put("/{canvas_id}", response_model=CanvasResponse)
async def update_canvas(
    canvas_id: UUID,
    graph: CanvasGraph = Body(...),
    db: AsyncSession = Depends(get_db),
):
    row = await db.get(CanvasModel, canvas_id)
    if not row:
        raise HTTPException(404, "Canvas not found")
    try:
        validate_canvas_graph(graph)
    except CanvasValidationError as e:
        raise HTTPException(400, e.message) from e
    row.graph = graph.model_dump()
    await db.commit()
    await db.refresh(row)
    return CanvasResponse(id=row.id, name=row.name, graph=CanvasGraph.model_validate(row.graph))
