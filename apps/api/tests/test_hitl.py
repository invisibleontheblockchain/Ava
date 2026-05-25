from langgraph.checkpoint.memory import MemorySaver

from ava_api.agents.l1_planner import compile_l1_graph


async def test_l1_graph_compiles_with_interrupt():
    graph = await compile_l1_graph(checkpointer=MemorySaver())
    assert graph is not None
