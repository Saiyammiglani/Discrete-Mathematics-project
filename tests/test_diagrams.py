"""Verify drawn edges against algorithm decisions and independent connectivity checks."""
import networkx as nx
import pytest
from matplotlib.colors import to_rgba

from core.graph import Graph
from core.vulnerability import failure_test
from services.analysis import analyze, mst_graph
from services.input import SAMPLES, load_sample
from services.scenarios import MPSTME_SAMPLE, rupees
from viz.draw import draw_graph, layout
from viz.styles import SELECTED, CURRENT, REJECTED, UNUSED, GROUP_COLORS


def legend(fig):
    lg = fig.axes[0].get_legend()
    return [t.get_text() for t in lg.get_texts()] if lg else []


@pytest.mark.parametrize("sample", list(SAMPLES))
@pytest.mark.parametrize("illustrated", [False, True])
def test_every_algorithm_frame_matches_selected_forest(sample, illustrated):
    meta = SAMPLES[sample]
    g = load_sample(sample).graph
    pos = layout(g, meta["pos"])
    facilities = meta.get("facilities") if illustrated else None
    a = analyze(g, "LIB" if sample == MPSTME_SAMPLE else "CR")
    for result in (a.kruskal, a.prim):
        selected, rejected = [], []
        reference = nx.Graph()
        reference.add_nodes_from(g.vertices)
        for step in result.steps:
            u, v = step.edge.key
            if step.action == "ACCEPT":
                assert not nx.has_path(reference, u, v)
                reference.add_edge(u, v)
                selected.append(step.edge.key)
            else:
                assert nx.has_path(reference, u, v)
                rejected.append(step.edge.key)
            fig = draw_graph(g, pos, facilities=facilities, tree=selected,
                             rejected=rejected, current=step.edge.key)
            for edge, line in zip(g.edges(), fig.axes[0].lines):
                expected = (REJECTED if edge.key in rejected else CURRENT if edge.key == step.edge.key
                            else SELECTED if edge.key in selected else UNUSED)
                assert to_rgba(line.get_color()) == to_rgba(expected)
                assert (line.get_linestyle() == "-") == (edge.key in selected)
            assert nx.is_forest(reference)
            assert len(selected) == reference.number_of_edges()
            fig.clear()
        assert set(selected) == {e.key for e in result.edges}


@pytest.mark.parametrize("sample", list(SAMPLES))
@pytest.mark.parametrize("illustrated", [False, True])
@pytest.mark.parametrize("minimum", [False, True])
def test_every_outage_diagram_matches_remaining_components(sample, illustrated, minimum):
    meta = SAMPLES[sample]
    original = load_sample(sample).graph
    g = mst_graph(original, analyze(original).kruskal) if minimum else original
    pos = layout(original, meta["pos"])
    failures = [dict(vertex=v) for v in g.vertices] + [dict(edge=e.key) for e in g.edges()]
    for args in failures:
        result = failure_test(g, **args)
        after = g.copy()
        removed_vertices, removed_edges = [], []
        if "vertex" in args:
            after.remove_vertex(args["vertex"])
            removed_vertices = [args["vertex"]]
        else:
            after.remove_edge(*args["edge"])
            removed_edges = [args["edge"]]
        ref = nx.Graph()
        ref.add_nodes_from(after.vertices)
        ref.add_edges_from(e.key for e in after.edges())
        assert {frozenset(c) for c in result.components} == {frozenset(c) for c in nx.connected_components(ref)}
        fig = draw_graph(after, pos, facilities=meta.get("facilities") if illustrated else None,
                         components=result.components, failed_vertices=removed_vertices, failed_edges=removed_edges)
        group = {v: i for i, c in enumerate(result.components) for v in c}
        for edge, line in zip(after.edges(), fig.axes[0].lines):
            assert group[edge.u] == group[edge.v]
            assert to_rgba(line.get_color()) == to_rgba(GROUP_COLORS[group[edge.u] % len(GROUP_COLORS)])
        texts = [t.get_text() for t in fig.axes[0].texts]
        if removed_vertices:
            assert any("FAILED" in t for t in texts)
            assert "Failed switch" in legend(fig)
        else:
            assert any("CABLE CUT" in t for t in texts)
            assert "Failed cable (removed)" in legend(fig)
        fig.clear()


@pytest.mark.parametrize("illustrated", [False, True])
def test_overview_mst_critical_legends_and_currency(illustrated):
    meta = SAMPLES[MPSTME_SAMPLE]
    g = load_sample(MPSTME_SAMPLE).graph
    a = analyze(g, "LIB")
    pos = layout(g, meta["pos"])
    kwargs = dict(facilities=meta["facilities"] if illustrated else None, weight_label=rupees)
    overview = draw_graph(g, pos, **kwargs)
    assert legend(overview) == ["Proposed cable"]
    assert "₹4,000" in [t.get_text() for t in overview.axes[0].texts]
    tree = [e.key for e in a.kruskal.edges]
    minimum = draw_graph(g, pos, tree=tree, show_unused=False, **kwargs)
    # The first lines are cables; room interiors are drawn afterwards.
    assert all(to_rgba(l.get_color()) == to_rgba(SELECTED) for l in minimum.axes[0].lines[:len(tree)])
    assert legend(minimum) == ["Selected cable"]
    critical = draw_graph(mst_graph(g, a.kruskal), pos, tree=tree,
                          bridges=a.mst_bridges, cut_vertices=a.mst_cut_vertices, **kwargs)
    assert all(to_rgba(l.get_color()) == to_rgba(REJECTED) for l in critical.axes[0].lines[:len(tree)])
    assert set(legend(critical)) == {"Bridge (critical cable)", "Cut vertex (critical switch)"}
    for fig in (overview, minimum, critical):
        fig.clear()


def test_disconnected_and_single_remaining_vertex_drawings():
    g = Graph([("A", "B", 1), ("X", "Y", 2)])
    pos = layout(g)
    for args in (dict(vertex="A"), dict(edge=("A", "B"))):
        result = failure_test(g, **args)
        assert len(result.components) == 2 + ("edge" in args)
    single = Graph(vertices=["B"])
    fig = draw_graph(single, {"A": (0, 0), "B": (1, 0)},
                     components=[["B"]], failed_vertices=["A"])
    assert "Failed switch" in legend(fig)
    assert len(fig.axes[0].collections[0].get_offsets()) == 2
