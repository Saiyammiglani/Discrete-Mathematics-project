"""Shared edge meanings for schematic and illustrated network diagrams."""
from matplotlib.lines import Line2D

SELECTED, UNUSED, REJECTED, CURRENT = "#28594b", "#b4bcb2", "#c33e4a", "#16856b"
GROUP_COLORS = ("#16856b", "#bd5d22", "#7752ad", "#237bc1", "#b33d78", "#657923")


def cable_style(key, *, tree, rejected, bridges, current, show_unused, group):
    if key in rejected:
        return REJECTED, 3.5 if key == current else 1.8, ":", "Rejected cable (not selected)"
    if key == current:
        return CURRENT, 3.5, "-", "Current cable (accepted)"
    if key in bridges:
        return REJECTED, 2.7, "-", "Bridge (critical cable)"
    if key in tree:
        return SELECTED, 2.7, "-", "Selected cable"
    if not show_unused:
        return None
    if group:
        i = group[key[0]]
        return GROUP_COLORS[i % len(GROUP_COLORS)], 2.3, "-", f"Group {i + 1}"
    if tree or rejected or current:
        return UNUSED, 1.4, "--", "Other proposed cable (not selected)"
    return SELECTED, 2, "-", "Proposed cable"


def diagram_legend(ax, styles, *, components=(), cuts=False, failed_switch=False, failed_cable=False):
    if components:
        handles = [Line2D([0], [0], color=GROUP_COLORS[i % len(GROUP_COLORS)], lw=3,
                          label=f"Group {i + 1}: {len(c)} locations") for i, c in enumerate(components)]
    else:
        entries = {s[3]: s for s in styles}
        handles = [Line2D([0], [0], color=s[0], lw=s[1], ls=s[2], label=s[3]) for s in entries.values()]
    if cuts:
        handles.append(Line2D([], [], marker="o", ls="", color="#c28124", label="Cut vertex (critical switch)"))
    if failed_switch:
        handles.append(Line2D([], [], marker="x", ls="", color=REJECTED, label="Failed switch"))
    if failed_cable:
        handles.append(Line2D([], [], color=REJECTED, lw=2, ls=":", label="Failed cable (removed)"))
    if handles:
        ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(.5, -.12),
                  ncol=min(2, len(handles)), frameon=False, fontsize=8)
