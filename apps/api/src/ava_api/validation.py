from ava_api.schemas import CanvasGraph


class CanvasValidationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def validate_canvas_graph(graph: CanvasGraph) -> None:
    """Phase 1 validation before save/run."""
    if not graph.blocks:
        raise CanvasValidationError("Canvas must have at least one block")

    block_ids = {b.id for b in graph.blocks}
    for edge in graph.edges:
        if edge.source not in block_ids:
            raise CanvasValidationError(f"Edge source unknown: {edge.source}")
        if edge.target not in block_ids:
            raise CanvasValidationError(f"Edge target unknown: {edge.target}")

    from ava_api.executor.dag import build_digraph

    try:
        build_digraph(graph)
    except ValueError as e:
        raise CanvasValidationError(str(e)) from e

    for block in graph.blocks:
        if block.type == "web":
            url = (block.data.get("config") or {}).get("url") or block.data.get("prompt", "")
            if not url.startswith("http"):
                raise CanvasValidationError(
                    f"Web block '{block.id}' requires config.url starting with http"
                )
