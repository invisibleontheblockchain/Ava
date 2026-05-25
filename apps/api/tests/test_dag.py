import pytest

from ava_api.executor.dag import build_digraph, get_parallel_batches
from ava_api.schemas import CanvasBlock, CanvasEdge, CanvasGraph


def _block(bid: str, x: float = 0) -> CanvasBlock:
    return CanvasBlock(
        id=bid,
        type="prompt",
        position={"x": x, "y": 0},
        data={"title": bid},
        connections={"inputs": [], "outputs": []},
    )


def test_linear_pipeline_batches():
    graph = CanvasGraph(
        blocks=[_block("a", 0), _block("b", 100), _block("c", 200)],
        edges=[
            CanvasEdge(id="e1", source="a", target="b"),
            CanvasEdge(id="e2", source="b", target="c"),
        ],
    )
    g = build_digraph(graph)
    batches = get_parallel_batches(g)
    assert batches == [["a"], ["b"], ["c"]]


def test_parallel_branches_same_batch():
    graph = CanvasGraph(
        blocks=[_block("root"), _block("left", 100), _block("right", 200), _block("merge", 300)],
        edges=[
            CanvasEdge(id="e1", source="root", target="left"),
            CanvasEdge(id="e2", source="root", target="right"),
            CanvasEdge(id="e3", source="left", target="merge"),
            CanvasEdge(id="e4", source="right", target="merge"),
        ],
    )
    g = build_digraph(graph)
    batches = get_parallel_batches(g)
    assert batches[0] == ["root"]
    assert set(batches[1]) == {"left", "right"}
    assert batches[2] == ["merge"]
