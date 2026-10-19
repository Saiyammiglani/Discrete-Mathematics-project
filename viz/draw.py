"""Matplotlib drawings of the network and its MST. Owner: Arjun.

Uses matplotlib's object API (Figure), never pyplot, so no global state leaks
between Streamlit reruns.
"""
from __future__ import annotations

from matplotlib.figure import Figure

from core.graph import Graph, fmt_weight

BLUE, GREY, RED, ORANGE, GREEN = "#1f6feb", "#9aa4b2", "#d1242f", "#e8890c", "#1a7f37"
MAX_DRAW_NODES = 200


def layout(g: Graph, pos: dict | None = None) -> dict[str, tuple[float, float]]:
    """Fixed hand-placed positions for samples, seeded spring layout otherwise."""
    if pos and set(pos) == set(g.vertices):
        return pos
    import networkx as nx

    G = nx.Graph()
    G.add_nodes_from(g.vertices)
    G.add_edges_from((e.u, e.v) for e in g.edges())
    return {k: tuple(v) for k, v in nx.spring_layout(G, seed=42, weight=None).items()}


def draw_graph(g: Graph, pos: dict, *, tree=(), current=None, rejected=(),
               bridges=(), cut_vertices=(), show_unused: bool = True,
               title: str = "", dpi: int = 150) -> Figure:
    """Draw the graph. Edge/vertex roles are given as collections of keys.

    tree: MST (or accepted) edges, thick blue. current: one edge key shown green.
    rejected: edges shown dashed red. bridges: red. cut_vertices: orange nodes.
    show_unused=False hides links that are not in the tree.
    """
    tree = {tuple(sorted(k)) for k in tree}
    rejected = {tuple(sorted(k)) for k in rejected}
    bridges = {tuple(sorted(k)) for k in bridges}
    cur = tuple(sorted(current)) if current else None
    fig = Figure(figsize=(6.4, 4.8), dpi=dpi)
    ax = fig.add_subplot(111)
    ax.set_axis_off()
    if title:
        ax.set_title(title, fontsize=11)
    for e in g.edges():
        k = e.key
        if k == cur:
            style = dict(color=GREEN, lw=4.5, ls="-", z=3)
        elif k in bridges:
            style = dict(color=RED, lw=3, ls="-", z=2)
        elif k in tree:
            style = dict(color=BLUE, lw=3, ls="-", z=2)
        elif k in rejected:
            style = dict(color=RED, lw=1.4, ls="--", z=1)
        elif show_unused:
            style = dict(color=GREY, lw=1.2, ls="--", z=1)
        else:
            continue
        (x1, y1), (x2, y2) = pos[e.u], pos[e.v]
        ax.plot([x1, x2], [y1, y2], color=style["color"], lw=style["lw"],
                ls=style["ls"], zorder=style["z"])
        if len(g) <= 60:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2, fmt_weight(e.w), fontsize=8, ha="center",
                    va="center", zorder=4,
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9))
    cuts = set(cut_vertices)
    xs = [pos[v][0] for v in g.vertices]
    ys = [pos[v][1] for v in g.vertices]
    ax.scatter(xs, ys, s=700 if len(g) <= 30 else 120,
               c=[ORANGE if v in cuts else "#dbe7ff" for v in g.vertices],
               edgecolors="#334", linewidths=1.2, zorder=5)
    if len(g) <= 60:
        for v in g.vertices:
            ax.text(*pos[v], v, fontsize=8, ha="center", va="center", zorder=6, weight="bold")
    ax.margins(0.12)
    fig.tight_layout()
    return fig
