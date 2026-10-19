"""Graph properties: degree, BFS components, path, cycles. Owner: Tanish."""
from __future__ import annotations

from collections import deque

from core.graph import Graph


def degrees(g: Graph) -> dict[str, int]:
    """deg(v) = number of links at v. O(V)."""
    return {x: len(g.adj[x]) for x in g.vertices}


def handshaking_holds(g: Graph) -> bool:
    """Handshaking Lemma: the sum of degrees equals 2|E|."""
    return sum(degrees(g).values()) == 2 * len(g.edges())


def hubs(g: Graph) -> list[str]:
    """Vertices with the highest degree (ties all returned, sorted)."""
    d = degrees(g)
    if not d:
        return []
    top = max(d.values())
    return [x for x, k in d.items() if k == top]


def components(g: Graph) -> list[list[str]]:
    """Connected components by BFS from each unvisited vertex. O(V + E).

    Each component is sorted; components are ordered by their first vertex.
    """
    seen: set[str] = set()
    out: list[list[str]] = []
    for s in g.vertices:
        if s in seen:
            continue
        seen.add(s)
        comp, q = [], deque([s])
        while q:
            u = q.popleft()
            comp.append(u)
            for v in sorted(g.adj[u]):
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        out.append(sorted(comp))
    return out


def is_connected(g: Graph) -> bool:
    return len(components(g)) <= 1


def path(g: Graph, s: str, t: str) -> list[str] | None:
    """Fewest-hop path s -> t by BFS with parent pointers, or None."""
    if s not in g.adj or t not in g.adj:
        raise KeyError("unknown vertex")
    parent: dict[str, str | None] = {s: None}
    q = deque([s])
    while q:
        u = q.popleft()
        if u == t:
            break
        for v in sorted(g.adj[u]):
            if v not in parent:
                parent[v] = u
                q.append(v)
    if t not in parent:
        return None
    out, x = [], t
    while x is not None:
        out.append(x)
        x = parent[x]
    return out[::-1]


def independent_cycles(g: Graph) -> int:
    """Cyclomatic number |E| - |V| + C."""
    return len(g.edges()) - len(g.vertices) + len(components(g))


def has_cycle(g: Graph) -> bool:
    """A graph is acyclic exactly when |E| = |V| - C."""
    return independent_cycles(g) > 0
