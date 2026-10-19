"""Export service: MST edge list as CSV and figures as PNG. Owner: Tanish."""
from __future__ import annotations

import io

from core.graph import Edge, fmt_weight

PNG_DPI = 220


def mst_csv(edges: list[Edge]) -> str:
    """MST edge list in the same format as the input (source,target,weight)."""
    lines = ["source,target,weight"]
    lines += [f"{e.key[0]},{e.key[1]},{fmt_weight(e.w)}" for e in sorted(edges, key=lambda e: (e.w, e.key))]
    return "\n".join(lines) + "\n"


def figure_png(fig, dpi: int = PNG_DPI) -> bytes:
    """Render a matplotlib Figure to PNG bytes."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    return buf.getvalue()
