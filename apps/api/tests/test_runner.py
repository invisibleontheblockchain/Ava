import uuid

from ava_api.executor.dag import build_digraph, get_parallel_batches
from ava_api.executor.runner import DAGExecutor
from ava_api.schemas import CanvasBlock, CanvasEdge, CanvasGraph


def test_dag_executor_batch_topology():
    """Unit test — batch structure without DB."""
    graph = CanvasGraph(
        blocks=[
            CanvasBlock(
                id="a",
                type="web",
                data={"title": "a", "config": {"url": "https://example.com"}},
            ),
            CanvasBlock(
                id="b",
                type="prompt",
                data={"title": "b", "prompt": "go"},
            ),
            CanvasBlock(
                id="c",
                type="note",
                data={"title": "c"},
            ),
        ],
        edges=[
            CanvasEdge(id="e1", source="a", target="b"),
            CanvasEdge(id="e2", source="b", target="c"),
        ],
    )
    digraph = build_digraph(graph)
    batches = get_parallel_batches(digraph)
    assert batches == [["a"], ["b"], ["c"]]

    executor = DAGExecutor(graph, uuid.uuid4())
    assert len(executor.batches) == 3
