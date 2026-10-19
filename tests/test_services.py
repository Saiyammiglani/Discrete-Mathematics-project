"""Service, export, drawing and app smoke tests."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from core.graph import Graph
from services.analysis import analyze, comparison_rows, networkx_check, same_edge_set
from services.export import figure_png, mst_csv
from services.input import SAMPLES, load_sample, parse_csv
from viz.draw import draw_graph, layout


APP = Path(__file__).resolve().parent.parent / "app.py"


def office():
    return load_sample("Office network (8 devices)").graph


def test_analysis_office():
    a = analyze(office(), "CR")
    assert (a.full_total, a.mst_total, a.saving) == (59, 24, 35)
    assert round(a.saving_pct) == 59 and a.same_total and a.connected
    assert a.cut_vertices == ["LS"] and len(a.mst_bridges) == 7
    assert a.mst_cut_vertices == ["CR", "DB", "LS", "SA", "SB"]
    assert a.cycles == 5 and a.degrees["SA"] == 5
    assert comparison_rows(a)[0] == {"Measure": "Total weight", "Kruskal": "24", "Prim": "24"}
    assert same_edge_set(a)   # sample weights give a unique MST


def test_networkx_check_all_ok():
    for name in SAMPLES:
        g = load_sample(name).graph
        chk = networkx_check(g, analyze(g))
        assert all(v for k, v in chk.items() if k.endswith("_ok"))


def test_mst_csv_roundtrip():
    a = analyze(office())
    text = mst_csv(a.kruskal.edges)
    assert text.splitlines()[0] == "source,target,weight" and len(text.splitlines()) == 8
    assert parse_csv(text).graph.total_weight() == 24


def test_fifty_node_network_fast():
    import random, time
    rng = random.Random(1)
    names = [f"n{i}" for i in range(50)]
    es = {(names[i], names[rng.randrange(i)]): rng.randint(1, 20) for i in range(1, 50)}
    for _ in range(150):
        a, b = rng.sample(names, 2)
        es[tuple(sorted((a, b)))] = rng.randint(1, 20)
    g = Graph([(a, b, w) for (a, b), w in es.items()])
    t0 = time.perf_counter()
    a = analyze(g)
    fig = draw_graph(g, layout(g), tree=[e.key for e in a.kruskal.edges])
    assert time.perf_counter() - t0 < 2 and a.same_total
    assert figure_png(fig, dpi=60)[:4] == b"\x89PNG"


def test_draw_all_styles():
    g = office()
    a = analyze(g)
    fig = draw_graph(g, layout(g, SAMPLES["Office network (8 devices)"]["pos"]),
                     tree=[e.key for e in a.kruskal.edges], current=("CR", "SA"),
                     rejected=[("CR", "SB")], bridges=a.bridges, cut_vertices=a.cut_vertices,
                     title="t")
    assert fig.axes


def test_layout_falls_back_to_spring():
    g = Graph([("A", "B", 1), ("B", "C", 1)])
    assert set(layout(g, {"X": (0, 0)})) == {"A", "B", "C"}


# ---- whole app, headless --------------------------------------------------
def app():
    return AppTest.from_file(str(APP), default_timeout=60).run()


def test_app_loads_sample_and_shows_mst():
    at = app()
    assert not at.exception
    vals = {m.label: m.value for m in at.metric}
    assert vals["Full network cost"] == "59" and vals["MST cost"] == "24"
    assert [t.label for t in at.tabs] == ["Graph properties", "Kruskal and Prim", "Compare", "Vulnerability"]


def test_app_prim_and_step_buttons():
    at = app()
    at.radio[0].set_value("Prim").run()
    assert not at.exception
    nxt = [b for b in at.button if "Next" in b.label][0]
    nxt.click().run()
    assert not at.exception and at.session_state["step"] == 2


def test_app_campus_sample():
    at = app()
    at.sidebar.selectbox[0].set_value("Campus network (12 devices)").run()
    assert not at.exception
    assert {m.label: m.value for m in at.metric}["Devices"] == "12"
