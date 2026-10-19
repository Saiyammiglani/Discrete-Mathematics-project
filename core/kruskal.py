"""Union-find and Kruskal's algorithm with a step log. Owner: Saiyam."""
from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter

from core.graph import Edge, Graph


@dataclass
class Step:
    """One decision of an MST algorithm."""

    step: int
    edge: Edge
    action: str   # "ACCEPT" or "REJECT"
    reason: str


@dataclass
class MSTResult:
    """Minimum spanning tree (or forest) with its step log."""

    algorithm: str
    edges: list[Edge]
    total: float
    steps: list[Step]
    runtime_ms: float = 0.0
    start: str | None = None
    forest_components: int = 1


class UnionFind:
    """Disjoint-set forest with path compression and union by rank."""

    def __init__(self, items):
        self.parent = {x: x for x in items}
        self.rank = {x: 0 for x in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def _tree_path(tree: dict[str, list[str]], s: str, t: str) -> list[str]:
    """Path s -> t inside the partial tree (exists when Kruskal rejects)."""
    parent = {s: None}
    stack = [s]
    while stack:
        u = stack.pop()
        if u == t:
            break
        for v in tree.get(u, ()):
            if v not in parent:
                parent[v] = u
                stack.append(v)
    out, x = [], t
    while x is not None:
        out.append(x)
        x = parent[x]
    return out[::-1]


def kruskal(g: Graph) -> MSTResult:
    """Kruskal: sort edges, add each unless it closes a cycle. O(E log E).

    Ties are broken by edge name so output is repeatable. For a disconnected
    graph the result is a minimum spanning forest.
    """
    t0 = perf_counter()
    uf = UnionFind(g.vertices)
    tree: list[Edge] = []
    steps: list[Step] = []
    nbrs: dict[str, list[str]] = {}
    n_comp = len(g.components())
    target = len(g.vertices) - n_comp
    for e in sorted(g.edges(), key=lambda e: (e.w, e.u, e.v)):
        if len(tree) == target:
            break
        if uf.union(e.u, e.v):
            tree.append(e)
            nbrs.setdefault(e.u, []).append(e.v)
            nbrs.setdefault(e.v, []).append(e.u)
            steps.append(Step(len(steps) + 1, e, "ACCEPT", "joins two separate trees"))
        else:
            cyc = "–".join(_tree_path(nbrs, e.u, e.v) + [e.u])
            steps.append(Step(len(steps) + 1, e, "REJECT", f"cycle {cyc}"))
    ms = (perf_counter() - t0) * 1000
    return MSTResult("Kruskal", tree, sum(e.w for e in tree), steps, ms, None, n_comp)
