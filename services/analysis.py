"""Analysis service: runs every algorithm once and gathers the results.

Owner: Saiyam. networkx is imported lazily and only for the cross-check (FR-11).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from core import properties
from core.graph import Edge, Graph, fmt_weight
from core.kruskal import MSTResult, kruskal
from core.prim import prim


@dataclass
class Analysis:
    """Everything the four tabs need for one graph."""

    graph: Graph
    degrees: dict[str, int]
    components: list[list[str]]
    cycles: int
    kruskal: MSTResult
    prim: MSTResult
    cut_vertices: list[str]
    bridges: list[tuple[str, str]]
    mst_cut_vertices: list[str]
    mst_bridges: list[tuple[str, str]]
    full_total: float
    mst_total: float

    @property
    def saving(self) -> float:
        return self.full_total - self.mst_total

    @property
    def saving_pct(self) -> float:
        return 100 * self.saving / self.full_total if self.full_total else 0.0

    @property
    def connected(self) -> bool:
        return len(self.components) <= 1

    @property
    def same_total(self) -> bool:
        return abs(self.kruskal.total - self.prim.total) < 1e-9


def mst_graph(g: Graph, result: MSTResult) -> Graph:
    """The MST as a Graph on the same vertex set (isolated devices kept)."""
    return Graph(result.edges, vertices=g.vertices)


def analyze(g: Graph, start: str | None = None) -> Analysis:
    """Run properties, Kruskal, Prim and Tarjan on the full graph and the MST."""
    k = kruskal(g)
    p = prim(g, start)
    cv, br = g.cut_vertices_and_bridges()
    mcv, mbr = mst_graph(g, k).cut_vertices_and_bridges()
    return Analysis(
        graph=g, degrees=properties.degrees(g), components=properties.components(g),
        cycles=properties.independent_cycles(g), kruskal=k, prim=p,
        cut_vertices=cv, bridges=br, mst_cut_vertices=mcv, mst_bridges=mbr,
        full_total=g.total_weight(), mst_total=k.total,
    )


def comparison_rows(a: Analysis) -> list[dict[str, str]]:
    """Rows for the Compare tab: Kruskal vs Prim."""
    def order(r: MSTResult) -> str:
        return ", ".join(e.name for e in r.edges)
    return [
        {"Measure": "Total weight", "Kruskal": fmt_weight(a.kruskal.total), "Prim": fmt_weight(a.prim.total)},
        {"Measure": "Edges in tree", "Kruskal": str(len(a.kruskal.edges)), "Prim": str(len(a.prim.edges))},
        {"Measure": "Steps logged", "Kruskal": str(len(a.kruskal.steps)), "Prim": str(len(a.prim.steps))},
        {"Measure": "Run time (ms)", "Kruskal": f"{a.kruskal.runtime_ms:.3f}", "Prim": f"{a.prim.runtime_ms:.3f}"},
        {"Measure": "Edge order", "Kruskal": order(a.kruskal), "Prim": order(a.prim)},
    ]


def same_edge_set(a: Analysis) -> bool:
    return {e.key for e in a.kruskal.edges} == {e.key for e in a.prim.edges}


def networkx_check(g: Graph, a: Analysis) -> dict:
    """Compare our MST totals and structure with networkx (reference only)."""
    import networkx as nx

    G = nx.Graph()
    G.add_nodes_from(g.vertices)
    G.add_weighted_edges_from((e.u, e.v, e.w) for e in g.edges())
    ref = nx.minimum_spanning_tree(G, algorithm="kruskal")
    ref_total = sum(d["weight"] for _, _, d in ref.edges(data=True))
    return {
        "nx_total": ref_total,
        "kruskal_ok": abs(ref_total - a.kruskal.total) < 1e-9,
        "prim_ok": abs(ref_total - a.prim.total) < 1e-9,
        "components_ok": nx.number_connected_components(G) == len(a.components),
        "cut_vertices_ok": sorted(nx.articulation_points(G)) == a.cut_vertices,
        "bridges_ok": sorted(tuple(sorted(b)) for b in nx.bridges(G)) == a.bridges,
    }
