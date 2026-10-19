"""Prim's algorithm (lazy, min-heap) with a step log. Owner: Arjun."""
from __future__ import annotations

import heapq
from time import perf_counter

from core.graph import Edge, Graph
from core.kruskal import MSTResult, Step


def prim(g: Graph, start: str | None = None) -> MSTResult:
    """Prim: grow one tree from `start` with a min-heap of crossing edges.

    O(E log V). If the graph is disconnected, the remaining vertices are used
    as further roots (in sorted order), giving a minimum spanning forest.
    Heap entries are (weight, u, v) so ties break by name.
    """
    if start is not None and start not in g.adj:
        raise KeyError(f"unknown start vertex {start!r}")
    t0 = perf_counter()
    tree: list[Edge] = []
    steps: list[Step] = []
    in_tree: set[str] = set()
    roots = 0
    for root in ([start] if start else []) + g.vertices:
        if root in in_tree:
            continue
        roots += 1
        in_tree.add(root)
        heap = [(w, root, v) for v, w in g.adj[root].items()]
        heapq.heapify(heap)
        while heap:
            w, u, v = heapq.heappop(heap)
            if v in in_tree:
                continue                      # stale entry: both ends in tree
            in_tree.add(v)
            e = Edge(u, v, w)
            tree.append(e)
            steps.append(Step(len(steps) + 1, e, "ACCEPT",
                              f"cheapest edge leaving tree, adds {v}"))
            for x, wx in g.adj[v].items():
                if x not in in_tree:
                    heapq.heappush(heap, (wx, v, x))
    ms = (perf_counter() - t0) * 1000
    return MSTResult("Prim", tree, sum(e.w for e in tree), steps, ms, start, roots)
