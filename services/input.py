"""Input service: samples, CSV parsing and row validation. Owner: Tanish.

Row numbers count file lines, so the header is row 1 and the first link is row 2.
"""
from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass, field
from pathlib import Path

from core.graph import Graph, fmt_weight

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAX_BYTES = 1_000_000          # 1 MB upload cap
MAX_NAME = 30
EXPECTED_HEADER = ["source", "target", "weight"]
TEMPLATE_CSV = "source,target,weight\nA,B,4\nB,C,2\nA,C,5\n"

# Hand-placed coordinates so drawings match the report.
SAMPLES: dict[str, dict] = {
    "Office network (8 devices)": {
        "file": "office_8.csv",
        "pos": {"CR": (0.0, 0.0), "FW": (-1.2, 1.4), "SA": (1.2, 0.2), "SB": (1.4, -1.6),
                "WS": (-0.4, 2.6), "DB": (2.6, 0.9), "LS": (0.2, -2.8), "AP": (-1.4, -3.2)},
    },
    "Campus network (12 devices)": {
        "file": "campus_12.csv",
        "pos": {"GW": (-3.0, 1.0), "FW": (-1.8, 1.0), "CORE1": (-0.4, 1.8), "CORE2": (-0.4, 0.0),
                "LIB": (1.2, 2.6), "ADM": (2.4, 1.6), "HST1": (3.6, 2.4), "HST2": (3.2, 3.6),
                "LAB1": (1.0, -0.8), "LAB2": (2.2, 0.2), "DC": (1.2, -2.2), "WIFI": (3.2, -1.2)},
    },
}


@dataclass
class ParseResult:
    """Outcome of reading an edge list."""

    graph: Graph | None = None
    errors: list[tuple[int, str]] = field(default_factory=list)   # (row, reason)
    infos: list[str] = field(default_factory=list)
    n_rows: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors and self.graph is not None


def load_sample_text(name: str) -> str:
    return (DATA_DIR / SAMPLES[name]["file"]).read_text(encoding="utf-8")


def build_graph(rows) -> ParseResult:
    """Validate `(row_number, source, target, weight)` tuples and build a Graph.

    Bad rows are all collected; a graph is returned only if none are bad.
    A duplicate pair keeps the cheaper weight and adds an info note.
    """
    res = ParseResult()
    kept: dict[tuple[str, str], tuple[float, int]] = {}
    for n, s, t, w in rows:
        res.n_rows += 1
        s, t, w = str(s).strip(), str(t).strip(), str(w).strip()
        bad = None
        if not s:
            bad = "source is empty"
        elif not t:
            bad = "target is empty"
        elif len(s) > MAX_NAME or len(t) > MAX_NAME:
            bad = f"device names must be 1 to {MAX_NAME} characters"
        elif s == t:
            bad = f"self-loop {s}–{t}"
        else:
            try:
                wf = float(w)
            except ValueError:
                bad = f"weight '{w}' is not a number"
            else:
                if not math.isfinite(wf) or wf <= 0:
                    bad = "weight must be > 0"
        if bad:
            res.errors.append((n, bad))
            continue
        key = (s, t) if s <= t else (t, s)
        if key in kept:
            old, _ = kept[key]
            keep = min(old, wf)
            res.infos.append(f"{key[0]}–{key[1]} listed twice, kept {fmt_weight(keep)}")
            kept[key] = (keep, n)
        else:
            kept[key] = (wf, n)
    if res.errors:
        return res
    if not kept:
        res.errors.append((0, "the file has no links"))
        return res
    res.graph = Graph((u, v, w) for (u, v), (w, _) in kept.items())
    return res


def parse_csv(data: str | bytes) -> ParseResult:
    """Parse an uploaded CSV edge list (source,target,weight)."""
    if isinstance(data, bytes):
        if len(data) > MAX_BYTES:
            return ParseResult(errors=[(0, "file is larger than the 1 MB limit")])
        try:
            data = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            return ParseResult(errors=[(0, "file is not valid UTF-8 text")])
    elif len(data.encode("utf-8")) > MAX_BYTES:
        return ParseResult(errors=[(0, "file is larger than the 1 MB limit")])
    lines = [r for r in csv.reader(io.StringIO(data))]
    if not lines:
        return ParseResult(errors=[(0, "the file is empty")])
    header = [h.strip().lower() for h in lines[0]]
    if header != EXPECTED_HEADER:
        return ParseResult(errors=[(1, "header must be exactly: source,target,weight")])
    rows = []
    for i, r in enumerate(lines[1:], start=2):
        if not any(c.strip() for c in r):
            continue                                  # skip blank lines
        if len(r) != 3:
            rows.append((i, "", "", ""))              # surfaces as a clear error below
            continue
        rows.append((i, *r))
    res = build_graph(rows)
    # replace the generic message for rows with the wrong number of columns
    wrong = {i for i, r in enumerate(lines[1:], start=2) if any(c.strip() for c in r) and len(r) != 3}
    res.errors = [(n, "expected 3 columns: source,target,weight" if n in wrong else m)
                  for n, m in res.errors]
    return res


def load_sample(name: str) -> ParseResult:
    return parse_csv(load_sample_text(name))
