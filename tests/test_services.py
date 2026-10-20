"""Service, export, drawing and app smoke tests."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from core.graph import Graph
from services.analysis import analyze, comparison_rows, networkx_check, same_edge_set, mst_graph
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


def test_mst_csv_preserves_quoted_names_and_precise_weights():
    g = Graph([('Lab, North', 'Room "A"', 1.2345678901234567),
               ('Room "A"', 'Room\nB', 0.000000123456789)])
    exported = mst_csv(analyze(g).kruskal.edges)
    result = parse_csv(exported)
    assert result.ok
    assert [(e.key, e.w) for e in result.graph.edges()] == [(e.key, e.w) for e in g.edges()]


@pytest.mark.parametrize("illustrated", [False, True])
def test_current_rejected_cable_stays_red_and_outside_tree(illustrated):
    from matplotlib.colors import to_rgba
    from services.scenarios import MPSTME_SAMPLE
    from viz.draw import RED
    meta = SAMPLES[MPSTME_SAMPLE]
    g = load_sample(MPSTME_SAMPLE).graph
    trace = analyze(g, "LIB").kruskal.steps[:5]
    accepted = [s.edge.key for s in trace if s.action == "ACCEPT"]
    rejected = [s.edge.key for s in trace if s.action == "REJECT"]
    current = trace[-1].edge.key
    assert current == ("LIB", "ROB") and current not in accepted
    fig = draw_graph(g, layout(g, meta["pos"]), tree=accepted,
                     rejected=rejected, current=current,
                     facilities=meta["facilities"] if illustrated else None)
    cable_index = [e.key for e in g.edges()].index(current)
    cable = fig.axes[0].lines[cable_index]
    assert to_rgba(cable.get_color()) == to_rgba("#c33e4a" if illustrated else RED)
    assert cable.get_linestyle() in (":", "--")
    if illustrated:
        legend = [t.get_text() for t in fig.axes[0].get_legend().get_texts()]
        assert "Rejected cable (not selected)" in legend
        assert "Current step" not in legend
    selected_only = draw_graph(g, layout(g, meta["pos"]), tree=accepted,
                               show_unused=False, weight_label=lambda w: f"COST:{w}",
                               facilities=meta["facilities"] if illustrated else None)
    labels = [t.get_text() for t in selected_only.axes[0].texts if t.get_text().startswith("COST:")]
    assert len(labels) == 4
    assert all(l.get_linestyle() == "-" for l in selected_only.axes[0].lines[:4])


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
    assert vals["Full network cost"] == "₹38,000" and vals["MST cost"] == "₹16,000"
    assert [t.label for t in at.tabs] == ["Network", "Algorithms", "Costs", "Failures"]


def test_app_prim_and_step_buttons():
    at = app()
    at.radio[0].set_value("Prim").run()
    assert not at.exception
    nxt = [b for b in at.button if "Next" in b.label][0]
    nxt.click().run()
    assert not at.exception and at.session_state["step"] == 2
    at.slider[0].set_value(5).run()
    assert not at.exception
    assert any("Prim finished: 5 edges, total cost ₹16,000." in s.value for s in at.caption)


def test_mpstme_known_answer_and_cable_failure():
    from services.scenarios import MPSTME_SAMPLE
    g = load_sample(MPSTME_SAMPLE).graph
    a = analyze(g, "LIB")
    assert len(g) == 6 and len(g.edges()) == 9
    assert (a.full_total, a.mst_total, a.saving) == (38, 16, 22)
    assert a.same_total and not a.bridges and not a.cut_vertices
    assert len(a.mst_bridges) == 5
    from core.vulnerability import failure_test
    full = failure_test(g, edge=("ROB", "RES"))
    tree = failure_test(mst_graph(g, a.kruskal), edge=("ROB", "RES"))
    assert full.connected and tree.split
    assert tree.components == [["ARVR", "LIB", "ROB", "TELE"], ["PRINT", "RES"]]
    assert [(s.edge.key, s.action) for s in a.kruskal.steps] == [
        (("ARVR", "ROB"), "ACCEPT"), (("ARVR", "TELE"), "ACCEPT"),
        (("PRINT", "RES"), "ACCEPT"), (("ARVR", "LIB"), "ACCEPT"),
        (("LIB", "ROB"), "REJECT"), (("RES", "ROB"), "ACCEPT"),
    ]
    assert {e.key for e in a.kruskal.edges} == {e.key for e in a.prim.edges}


def test_mpstme_scenes_export_and_failed_switch():
    from services.scenarios import MPSTME_SAMPLE
    meta = SAMPLES[MPSTME_SAMPLE]
    g = load_sample(MPSTME_SAMPLE).graph
    positions = layout(g, meta["pos"], facility_mode=True)
    before = set(g.vertices)
    h = g.copy()
    h.remove_vertex("ROB")
    fig = draw_graph(h, positions, facilities=meta["facilities"],
                     components=h.components(), failed_vertices=["ROB"])
    texts = [t.get_text() for t in fig.axes[0].texts]
    assert "Library" in texts and "Robotics Lab" in texts
    assert any("SWITCH FAILED" in text for text in texts)
    assert len(fig.axes[0].patches) > 60  # equipment, furniture and switch scenes
    assert figure_png(fig, dpi=60).startswith(b"\x89PNG")
    assert set(g.vertices) == before and g.has_edge("ROB", "RES")


def test_facility_layout_keeps_room_spacing_after_custom_edits():
    from services.scenarios import MPSTME_SAMPLE
    meta = SAMPLES[MPSTME_SAMPLE]
    g = load_sample(MPSTME_SAMPLE).graph
    g.add_edge("LIB", "NEW", 2)
    positions = layout(g, meta["pos"], facility_mode=True)
    assert positions["LIB"] == meta["pos"]["LIB"]
    assert set(positions) == set(g.vertices)
    assert all(abs(positions["NEW"][1] - pos[1]) >= 4.2 for pos in meta["pos"].values())


def test_app_mpstme_failure_scene_and_generic_sample():
    at = app()
    remove = next(r for r in at.radio if r.label == "Remove a")
    remove.set_value("link").run()
    assert not at.exception
    assert any("2 disconnected groups" in e.value for e in at.error)
    assert any("**Group 2:** 3-D Printing Lab, Research Lab" in m.value for m in at.markdown)
    at.sidebar.selectbox[0].set_value("Office network (8 devices)").run()
    assert not at.exception
    vals = {m.label: m.value for m in at.metric}
    assert vals["Full network cost"] == "59" and vals["MST cost"] == "24"
