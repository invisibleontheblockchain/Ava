"""DAG topology — Kahn's algorithm for parallel execution batches (Phase 1+)."""

from __future__ import annotations

import networkx as nx

from ava_api.schemas import CanvasBlock, CanvasEdge, CanvasGraph


def build_digraph(graph: CanvasGraph) -> nx.DiGraph:
    g = nx.DiGraph()
    for block in graph.blocks:
        g.add_node(block.id, block=block)
    for edge in graph.edges:
        g.add_edge(edge.source, edge.target)
    if not nx.is_directed_acyclic_graph(g):
        raise ValueError("Canvas graph contains a cycle — DAG required.")
    return g


def get_parallel_batches(digraph: nx.DiGraph) -> list[list[str]]:
    """Kahn's algorithm — nodes with in-degree 0 execute in the same batch."""
    in_degree = {n: digraph.in_degree(n) for n in digraph.nodes}
    ready = [n for n, d in in_degree.items() if d == 0]
    batches: list[list[str]] = []
    while ready:
        batches.append(list(ready))
        next_ready: list[str] = []
        for node in ready:
            for successor in digraph.successors(node):
                in_degree[successor] -= 1
                if in_degree[successor] == 0:
                    next_ready.append(successor)
        ready = next_ready
    if sum(len(b) for b in batches) != len(digraph.nodes):
        raise ValueError("Graph has nodes not reachable in topological order.")
    return batches


def block_by_id(graph: CanvasGraph) -> dict[str, CanvasBlock]:
    return {b.id: b for b in graph.blocks}


def upstream_ids(block: CanvasBlock, graph: CanvasGraph) -> list[str]:
    inputs = block.connections.get("inputs") or []
    if inputs:
        return inputs
    return [e.source for e in graph.edges if e.target == block.id]
