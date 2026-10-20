"""Matplotlib drawings of the network and its MST. Owner: Arjun.

Uses matplotlib's object API (Figure), never pyplot, so no global state leaks
between Streamlit reruns.
"""
from __future__ import annotations

from matplotlib.figure import Figure

from core.graph import Graph, fmt_weight
from viz.styles import (SELECTED as BLUE, UNUSED as GREY, REJECTED as RED,
                        CURRENT as GREEN, GROUP_COLORS, cable_style, diagram_legend)

ORANGE = "#c28124"
MAX_DRAW_NODES = 200


def layout(g: Graph, pos: dict | None = None, *, facility_mode: bool = False) -> dict[str, tuple[float, float]]:
    """Fixed hand-placed positions for samples, seeded spring layout otherwise."""
    if pos and set(pos) == set(g.vertices):
        return pos
    if pos and facility_mode:
        result = {v: pos[v] for v in g.vertices if v in pos}
        extra = [v for v in g.vertices if v not in pos]
        for i, v in enumerate(extra):
            result[v] = (-4.2 + (i % 4) * 4.2, -4.2 * (1 + i // 4))
        return result
    import networkx as nx

    G = nx.Graph()
    G.add_nodes_from(g.vertices)
    G.add_edges_from((e.u, e.v) for e in g.edges())
    return {k: tuple(v) for k, v in nx.spring_layout(G, seed=42, weight=None).items()}


def draw_graph(g: Graph, pos: dict, *, tree=(), current=None, rejected=(),
               bridges=(), cut_vertices=(), show_unused: bool = True,
               title: str = "", dpi: int = 150, facilities=None, components=(),
               failed_edges=(), failed_vertices=(), weight_label=None) -> Figure:
    """Draw the graph. Edge/vertex roles are given as collections of keys.

    tree: MST (or accepted) edges, thick blue. current: one edge key shown green.
    rejected: edges shown dashed red. bridges: red. cut_vertices: orange nodes.
    show_unused=False hides links that are not in the tree.
    """
    if facilities:
        from viz.facilities import draw_facility_network
        return draw_facility_network(
            g, pos, facilities=facilities, tree=tree, current=current, rejected=rejected,
            bridges=bridges, cut_vertices=cut_vertices, show_unused=show_unused,
            title=title, dpi=dpi, components=components, failed_edges=failed_edges,
            failed_vertices=failed_vertices, weight_label=weight_label)
    weight_label = weight_label or fmt_weight
    tree = {tuple(sorted(k)) for k in tree}
    rejected = {tuple(sorted(k)) for k in rejected}
    bridges = {tuple(sorted(k)) for k in bridges}
    cur = tuple(sorted(current)) if current else None
    failed_vertices = set(failed_vertices)
    group = {v: i for i, c in enumerate(components) for v in c}
    styles = []
    fig = Figure(figsize=(6.4, 4.8), dpi=dpi, facecolor="#fafaf7")
    ax = fig.add_subplot(111)
    ax.set_axis_off()
    if title:
        ax.set_title(title, fontsize=11, color="#2d3a32")
    for e in g.edges():
        k = e.key
        style = cable_style(k, tree=tree, rejected=rejected, bridges=bridges,
                            current=cur, show_unused=show_unused, group=group)
        if style is None:
            continue
        styles.append(style)
        color, width, linestyle, _ = style
        (x1, y1), (x2, y2) = pos[e.u], pos[e.v]
        ax.plot([x1, x2], [y1, y2], color=color, lw=width, ls=linestyle, zorder=2)
        if len(g) <= 60:
            text = ("REJECTED · " if k == cur and k in rejected else "") + weight_label(e.w)
            ax.text((x1 + x2) / 2, (y1 + y2) / 2, text, fontsize=8, ha="center",
                    va="center", zorder=4,
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9))
    cuts = set(cut_vertices)
    vertices = sorted(set(g.vertices) | failed_vertices)
    xs = [pos[v][0] for v in vertices]
    ys = [pos[v][1] for v in vertices]
    ax.scatter(xs, ys, s=700 if len(g) <= 30 else 120,
               c=["#f5d9dc" if v in failed_vertices else ORANGE if v in cuts else
                  GROUP_COLORS[group[v] % len(GROUP_COLORS)] if v in group else "#edf1e9"
                  for v in vertices],
               edgecolors="#536254", linewidths=1.2, zorder=5)
    if len(g) <= 60:
        for v in vertices:
            ax.text(*pos[v], v + ("\nFAILED" if v in failed_vertices else ""), fontsize=8,
                    ha="center", va="center", zorder=6, weight="bold")
    for u, v in failed_edges:
        if u in pos and v in pos:
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            ax.plot([x1, x2], [y1, y2], color=RED, lw=2.3, ls=":", zorder=3)
            ax.text((x1 + x2) / 2, (y1 + y2) / 2, "X CABLE CUT", color=RED,
                    fontsize=8, ha="center", zorder=7, bbox=dict(fc="white", ec=RED, pad=2))
    for v in failed_vertices:
        ax.scatter(*pos[v], marker="x", s=850, color=RED, zorder=7)
    # Keep framing fixed when switches are removed, including a failed outermost switch.
    if pos:
        ax.update_datalim(list(pos.values()))
        ax.autoscale_view()
    diagram_legend(ax, styles, components=components, cuts=bool(cuts),
                   failed_switch=bool(failed_vertices), failed_cable=bool(failed_edges))
    ax.margins(0.12)
    ax.set_aspect("equal", adjustable="datalim")
    fig.tight_layout()
    fig.subplots_adjust(bottom=.22)
    return fig
