"""Small vector room scenes: decorative equipment inside a graph vertex.

Everything is drawn with matplotlib shapes, including furniture and switches,
so app views and PNG exports share the same assets and need no image downloads.
"""
from __future__ import annotations

from matplotlib.patches import Arc, Circle, FancyBboxPatch, Polygon, Rectangle
from viz.styles import GROUP_COLORS, cable_style, diagram_legend
from services.scenarios import rupees

INK = "#2d3a32"
MUTED = "#727d72"
ROOM_W, ROOM_H = 2.9, 2.6


def room_scene(ax, x, y, vertex, facility, *, border="#9daa9e", status="SWITCH ONLINE",
               failed=False):
    """Draw one room containing equipment and a network switch."""
    def rect(px, py, w, h, color, edge=INK, radius=0, z=7):
        if radius:
            p = FancyBboxPatch((x + px, y + py), w, h,
                              boxstyle=f"round,pad=0,rounding_size={radius}",
                              facecolor=color, edgecolor=edge, linewidth=1, zorder=z)
        else:
            p = Rectangle((x + px, y + py), w, h, facecolor=color,
                          edgecolor=edge, linewidth=1, zorder=z)
        ax.add_patch(p)

    def line(points, color=INK, width=1.5, z=8):
        ax.plot([x + p[0] for p in points], [y + p[1] for p in points],
                color=color, lw=width, solid_capstyle="round", zorder=z)

    def circle(px, py, r, color, edge=INK, z=9):
        ax.add_patch(Circle((x + px, y + py), r, facecolor=color,
                            edgecolor=edge, lw=1, zorder=z))

    def monitor(px, py, w=.55):
        rect(px, py, w, .34, "#d6edf8", radius=.04)
        line([(px + w / 2, py), (px + w / 2, py - .12)])
        line([(px + .1, py - .12), (px + w - .1, py - .12)])

    # Outer room, header and an illustration area.
    rect(-1.45, -1.3, ROOM_W, ROOM_H, "#ffffff", border, radius=.05, z=5)
    rect(-1.39, .76, 2.78, .48, "#f1f3ed", "none", radius=.025, z=6)
    ax.text(x, y + 1.01, facility.get("name", vertex), ha="center", va="center",
            fontsize=9, weight="bold", color=INK, zorder=10)
    ax.text(x, y + .59, facility.get("subtitle", "Network location"),
            ha="center", va="center", fontsize=7, color=MUTED, zorder=10)

    kind = facility.get("kind", "research")
    if kind == "library":
        for sx in (-1.06, .55):
            rect(sx, -.27, .52, .66, "#dfc7a6")
            for row in (-.19, .09):
                for j, color in enumerate(("#8ca79b", "#b8a48b", "#83929d", "#c2b9a5")):
                    rect(sx + .05 + j * .11, row, .08, .21, color, "none")
            line([(sx, .02), (sx + .52, .02)], "#987954", 1)
        rect(-.37, -.2, .74, .22, "#e4d7bf", radius=.03)
        rect(-.21, .03, .42, .13, "white", "#8295a4")
        line([(0, .03), (0, .16)], "#8295a4", .8)
    elif kind == "arvr":
        for dx in (-.99, .34):
            rect(dx - .08, -.27, .8, .1, "#ccd9e4")
            monitor(dx, -.04, .64)
            ax.add_patch(Arc((x + dx + .32, y + .27), .5, .36,
                             theta1=0, theta2=180, color=INK, lw=2, zorder=9))
            rect(dx + .08, .1, .48, .22, "#718b83", radius=.05)
            circle(dx + .2, .2, .045, "#c3edee")
            circle(dx + .43, .2, .045, "#c3edee")
    elif kind == "robotics":
        rect(-.65, -.32, 1.3, .12, "#ccd9e4")
        rect(-.27, -.2, .54, .16, "#8ca2b6", radius=.04)
        arm = [(0, -.04), (-.35, .22), (.07, .39), (.5, .14)]
        line(arm, "#ac9271", 7)
        for px, py in arm[:-1]:
            circle(px, py, .075, "#fff3d6")
        line([(.5, .14), (.61, .19), (.72, .12)])
        line([(.5, .14), (.53, .02), (.66, -.03)])
        rect(.79, -.18, .22, .22, "#a9cbd3")
    elif kind == "telecom":
        rect(-1.04, -.28, .57, .67, "#d8e4ed", radius=.04)
        for dy in (-.13, .04, .21):
            rect(-.96, dy, .4, .1, "#617f99", "none")
        line([(.45, -.27), (.45, .19)], "#617f99", 2)
        line([(.19, -.27), (.45, .12), (.71, -.27)], "#617f99", 2)
        circle(.45, .19, .055, "#54adbf")
        for radius in (.14, .26):
            ax.add_patch(Arc((x + .45, y + .19), radius * 2, radius * 2,
                             theta1=30, theta2=150, color="#3999ac", lw=1.3, zorder=9))
    elif kind == "printing":
        rect(-.76, -.32, 1.52, .73, "#dbe8ee", radius=.04)
        rect(-.61, -.19, 1.22, .5, "#f5fafc")
        line([(-.55, .24), (.55, .24)], "#6a879d", 2)
        line([(.03, .24), (.03, .05)], "#6a879d", 3)
        ax.add_patch(Polygon([(x - .2, y - .14), (x + .2, y - .14),
                              (x + .13, y + .03), (x - .08, y + .09)],
                             facecolor="#7eb8aa", edgecolor=INK, lw=1, zorder=9))
        rect(-.58, -.28, 1.16, .07, "#8ba3b5", "none")
    else:
        rect(-1.04, -.28, 2.08, .1, "#d4dfe8")
        monitor(-.92, -.03, .65)
        monitor(.25, -.03, .65)
        for px in (-.59, .58):
            line([(px, .08), (px + .13, .15), (px + .25, .1)], "#53a18b", 1.5)

    # Room equipment converges on the one switch represented by this vertex.
    line([(-.8, -.37), (-.8, -.48), (0, -.48), (0, -.58)], "#8ea8b8", 1)
    line([(.8, -.37), (.8, -.48), (0, -.48)], "#8ea8b8", 1)
    rect(-.54, -.86, 1.08, .28, "#cbd7e0" if failed else "#294c63", radius=.06)
    for i in range(6):
        rect(-.39 + i * .13, -.78, .08, .09, "#879ca8" if failed else "#b4d3df", "none")
    circle(.41, -.65, .025, "#cd4d52" if failed else "#6ae0b0", "none")
    ax.text(x, y - 1.08, f"{vertex}  /  {status}", ha="center", va="center",
            fontsize=6.6, weight="bold", color=border, zorder=10)
    if failed:
        line([(-.23, -.97), (.23, -.5)], "#c33e4a", 2.5, 12)
        line([(-.23, -.5), (.23, -.97)], "#c33e4a", 2.5, 12)


def connection_path(u, v, pos):
    """Route cable ends to room boundaries; detour around intervening rooms."""
    x1, y1 = pos[u]
    x2, y2 = pos[v]
    if abs(y1 - y2) < .01 and any(
        w not in (u, v) and abs(p[1] - y1) < .01 and min(x1, x2) < p[0] < max(x1, x2)
        for w, p in pos.items()
    ):
        outer_y = y1 + (2.1 if y1 > 1 else -2.1)
        sy = ROOM_H / 2 if outer_y > y1 else -ROOM_H / 2
        return [(x1, y1 + sy), (x1, outer_y), (x2, outer_y), (x2, y2 + sy)], (
            (x1 + x2) / 2, outer_y)
    dx, dy = x2 - x1, y2 - y1
    scale = min((ROOM_W / 2) / abs(dx) if dx else float("inf"),
                (ROOM_H / 2) / abs(dy) if dy else float("inf"))
    return [(x1 + dx * scale, y1 + dy * scale),
            (x2 - dx * scale, y2 - dy * scale)], ((x1 + x2) / 2, (y1 + y2) / 2)


def draw_facility_network(g, pos, *, facilities, tree=(), current=None, rejected=(),
                          bridges=(), cut_vertices=(), show_unused=True, title="",
                          dpi=150, components=(), failed_edges=(), failed_vertices=(), weight_label=None):
    """Render facility vertices consistently in overview, traces and failure views."""
    from matplotlib.figure import Figure
    weight_label = weight_label or rupees
    fig = Figure(figsize=(13.5, 7.2), dpi=dpi, facecolor="#fafaf7")
    ax = fig.add_subplot(111)
    ax.set_axis_off()
    ax.set_aspect("equal")
    if title:
        ax.set_title(title, fontsize=12, color=INK, weight="medium", pad=16)
    keys = lambda values: {tuple(sorted(k)) for k in values}
    tree, rejected, bridges, failed_edges = map(keys, (tree, rejected, bridges, failed_edges))
    current = tuple(sorted(current)) if current else None
    cuts, failed_vertices = set(cut_vertices), set(failed_vertices)
    group = {v: i for i, c in enumerate(components) for v in c}
    styles = []

    for e in g.edges():
        k = e.key
        style = cable_style(k, tree=tree, rejected=rejected, bridges=bridges,
                            current=current, show_unused=show_unused, group=group)
        if style is None:
            continue
        styles.append(style)
        color, width, linestyle, _ = style
        points, label = connection_path(e.u, e.v, pos)
        ax.plot(*zip(*points), color=color, lw=width, ls=linestyle, zorder=2)
        text = ("REJECTED · " if k == current and k in rejected else "") + weight_label(e.w)
        ax.text(*label, text, ha="center", va="center",
                fontsize=8, color=INK, zorder=4,
                bbox=dict(boxstyle="square,pad=.25", fc="white", ec="#dfe3d9"))

    for u, v in failed_edges:
        if u not in pos or v not in pos:
            continue
        points, label = connection_path(u, v, pos)
        ax.plot(*zip(*points), color="#c33e4a", lw=2.3, ls=":", zorder=3)
        ax.text(*label, "X  CABLE CUT", color="#ad2737", fontsize=8, weight="bold",
                ha="center", va="center", zorder=11,
                bbox=dict(boxstyle="round,pad=.35", fc="#fff1f2", ec="#c33e4a"))

    for vertex in sorted(set(g.vertices) | failed_vertices):
        x, y = pos[vertex]
        border, status = "#9daa9e", "SWITCH ONLINE"
        if components:
            i = group.get(vertex, 0)
            border, status = GROUP_COLORS[i % len(GROUP_COLORS)], f"GROUP {i + 1}"
        if vertex in cuts:
            border, status = "#c28124", "CRITICAL SWITCH"
        if vertex in failed_vertices:
            border, status = "#ad5660", "SWITCH FAILED"
        facility = facilities.get(vertex, {"name": vertex, "kind": "research",
                                           "subtitle": "Custom location"})
        room_scene(ax, x, y, vertex, facility, border=border, status=status,
                   failed=vertex in failed_vertices)

    all_pos = [pos[v] for v in set(g.vertices) | failed_vertices]
    if all_pos:
        xs, ys = zip(*all_pos)
        ax.set_xlim(min(xs) - 1.85, max(xs) + 1.85)
        ax.set_ylim(min(ys) - 2.45, max(ys) + 2.45)
    diagram_legend(ax, styles, components=components, cuts=bool(cuts),
                   failed_switch=bool(failed_vertices), failed_cable=bool(failed_edges))
    fig.text(.04, .025, "Illustrative MPSTME network · Costs in INR", fontsize=7, color=MUTED)
    fig.subplots_adjust(left=.025, right=.975, top=.93 if title else .99, bottom=.13)
    return fig
