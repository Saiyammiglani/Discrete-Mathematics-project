"""Graph model: Edge and Graph (adjacency list + adjacency matrix).

Pure Python, no UI imports. Links are undirected and carry one positive cost.
Owner: Tanish.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


def fmt_weight(w: float) -> str:
    """Show whole numbers without a trailing '.0' (3.0 -> '3', 2.5 -> '2.5')."""
    return str(int(w)) if float(w).is_integer() else str(w)


@dataclass(frozen=True)
class Edge:
    """An undirected link u-v with cost w."""

    u: str
    v: str
    w: float

    @staticmethod
    def of(u: str, v: str, w: float) -> "Edge":
        """Build an edge with endpoints in sorted order (canonical form)."""
        return Edge(u, v, w) if u <= v else Edge(v, u, w)

    @property
    def key(self) -> tuple[str, str]:
        """Order-independent identity of the link."""
        return (self.u, self.v) if self.u <= self.v else (self.v, self.u)

    @property
    def name(self) -> str:
        """Readable name such as 'CR–SA'; also the tie-break key."""
        a, b = self.key
        return f"{a}–{b}"


class Graph:
    """Weighted undirected graph stored as a dict of dicts, O(V + E) memory."""

    def __init__(self, edges=(), vertices=()):
        self.adj: dict[str, dict[str, float]] = {}
        for x in vertices:
            self.add_vertex(x)
        for e in edges:
            if isinstance(e, Edge):
                self.add_edge(e.u, e.v, e.w)
            else:
                self.add_edge(*e)

    # ---- construction -------------------------------------------------
    def add_vertex(self, x: str) -> None:
        self.adj.setdefault(x, {})

    def add_edge(self, u: str, v: str, w: float) -> None:
        """Add a link. Rejects self-loops and non-positive/non-finite costs.

        If the pair already exists the cheaper cost is kept.
        """
        if u == v:
            raise ValueError(f"self-loop {u}–{v} is not allowed")
        w = float(w)
        if not math.isfinite(w) or w <= 0:
            raise ValueError(f"weight of {u}–{v} must be a positive number")
        self.add_vertex(u)
        self.add_vertex(v)
        old = self.adj[u].get(v)
        if old is None or w < old:
            self.adj[u][v] = w
            self.adj[v][u] = w

    def remove_edge(self, u: str, v: str) -> None:
        self.adj[u].pop(v)
        self.adj[v].pop(u)

    def remove_vertex(self, x: str) -> None:
        for y in list(self.adj[x]):
            del self.adj[y][x]
        del self.adj[x]

    def copy(self) -> "Graph":
        g = Graph()
        g.adj = {x: dict(nb) for x, nb in self.adj.items()}
        return g

    # ---- basic queries ------------------------------------------------
    @property
    def vertices(self) -> list[str]:
        return sorted(self.adj)

    def edges(self) -> list[Edge]:
        """All links in canonical form, sorted by (weight, name)."""
        out = [Edge(u, v, w) for u, nb in self.adj.items() for v, w in nb.items() if u < v]
        return sorted(out, key=lambda e: (e.w, e.u, e.v))

    def has_edge(self, u: str, v: str) -> bool:
        return v in self.adj.get(u, {})

    def weight(self, u: str, v: str) -> float:
        return self.adj[u][v]

    def total_weight(self) -> float:
        return sum(e.w for e in self.edges())

    def __len__(self) -> int:
        return len(self.adj)

    # ---- representations ----------------------------------------------
    def adjacency_matrix(self) -> tuple[list[str], list[list[float]]]:
        """(vertices, V x V matrix); 0 means no link. O(V^2), for display only."""
        vs = self.vertices
        idx = {x: i for i, x in enumerate(vs)}
        m = [[0.0] * len(vs) for _ in vs]
        for u, nb in self.adj.items():
            for v, w in nb.items():
                m[idx[u]][idx[v]] = w
        return vs, m

    # ---- property shortcuts (implemented in core.properties / vulnerability)
    def degrees(self) -> dict[str, int]:
        from core.properties import degrees
        return degrees(self)

    def components(self) -> list[list[str]]:
        from core.properties import components
        return components(self)

    def path(self, s: str, t: str) -> list[str] | None:
        from core.properties import path
        return path(self, s, t)

    def has_cycle(self) -> bool:
        from core.properties import has_cycle
        return has_cycle(self)

    def independent_cycles(self) -> int:
        from core.properties import independent_cycles
        return independent_cycles(self)

    def cut_vertices_and_bridges(self) -> tuple[list[str], list[tuple[str, str]]]:
        from core.vulnerability import cut_vertices_and_bridges
        return cut_vertices_and_bridges(self)
