"""Core algorithm tests: unit, known-answer, reference (networkx) and invariants."""
import random

import networkx as nx
import pytest

from core.graph import Edge, Graph
from core.kruskal import UnionFind, kruskal
from core.prim import prim
from core.properties import (components, degrees, handshaking_holds, hubs,
                             independent_cycles, is_connected, path)
from core.vulnerability import cut_vertices_and_bridges, failure_test
from services.input import load_sample

OFFICE = lambda: load_sample("Office network (8 devices)").graph


# ---- graph -------------------------------------------------------------
def test_edge_canonical_and_name():
    e = Edge.of("SB", "SA", 2)
    assert (e.u, e.v) == ("SA", "SB") and e.name == "SA–SB"


def test_graph_rejects_bad_edges():
    with pytest.raises(ValueError):
        Graph([("A", "A", 1)])
    for w in (0, -1, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            Graph([("A", "B", w)])


def test_duplicate_keeps_cheaper():
    g = Graph([("A", "B", 5), ("B", "A", 2)])
    assert g.weight("A", "B") == 2 and len(g.edges()) == 1


def test_adjacency_matrix_symmetric():
    vs, m = OFFICE().adjacency_matrix()
    assert vs == sorted(vs) and all(m[i][j] == m[j][i] for i in range(8) for j in range(8))
    assert sum(1 for r in m for x in r if x) == 24


# ---- union-find --------------------------------------------------------
def test_union_find():
    uf = UnionFind("abcd")
    assert uf.union("a", "b") and uf.union("c", "d")
    assert uf.find("a") == uf.find("b") != uf.find("c")
    assert not uf.union("a", "b")
    assert uf.union("b", "c") and uf.find("a") == uf.find("d")


# ---- known answers: the sample network from the proposal ---------------
def test_sample_properties():
    g = OFFICE()
    assert len(g) == 8 and len(g.edges()) == 12 and g.total_weight() == 59
    assert degrees(g) == {"AP": 1, "CR": 3, "DB": 3, "FW": 2, "LS": 3, "SA": 5, "SB": 4, "WS": 3}
    assert hubs(g) == ["SA"] and handshaking_holds(g)
    assert is_connected(g) and independent_cycles(g) == 5
    assert g.cut_vertices_and_bridges() == (["LS"], [("AP", "LS")])


def test_kruskal_trace_matches_proposal():
    k = kruskal(OFFICE())
    got = [(s.edge.name, s.edge.w, s.action) for s in k.steps]
    assert got == [("AP–LS", 2, "ACCEPT"), ("SA–SB", 2, "ACCEPT"), ("CR–SA", 3, "ACCEPT"),
                   ("DB–WS", 3, "ACCEPT"), ("CR–FW", 4, "ACCEPT"), ("DB–SB", 4, "ACCEPT"),
                   ("CR–SB", 5, "REJECT"), ("FW–WS", 6, "REJECT"), ("LS–SB", 6, "ACCEPT")]
    assert k.total == 24 and len(k.edges) == 7
    assert k.steps[6].reason == "cycle CR–SA–SB–CR"
    assert k.steps[7].reason == "cycle FW–CR–SA–SB–DB–WS–FW"


def test_prim_trace_matches_proposal():
    p = prim(OFFICE(), "CR")
    assert [(s.edge.name, s.edge.w) for s in p.steps] == [
        ("CR–SA", 3), ("SA–SB", 2), ("CR–FW", 4), ("DB–SB", 4),
        ("DB–WS", 3), ("LS–SB", 6), ("AP–LS", 2)]
    assert p.total == 24


def test_mst_is_fully_fragile():
    g = OFFICE()
    t = Graph(kruskal(g).edges, vertices=g.vertices)
    cuts, bridges = t.cut_vertices_and_bridges()
    assert cuts == ["CR", "DB", "LS", "SA", "SB"] and len(bridges) == 7
    assert independent_cycles(t) == 0


def test_failure_test_sb_db():
    g = OFFICE()
    t = Graph(kruskal(g).edges, vertices=g.vertices)
    assert failure_test(g, edge=("DB", "SB")).connected
    r = failure_test(t, edge=("DB", "SB"))
    assert r.split and len(r.components) == 2
    assert failure_test(g, vertex="LS").split
    with pytest.raises(ValueError):
        failure_test(g)


# ---- edge cases --------------------------------------------------------
def test_disconnected_forest():
    g = Graph([("A", "B", 1), ("B", "C", 2), ("A", "C", 3), ("X", "Y", 4)])
    assert len(components(g)) == 2
    for r in (kruskal(g), prim(g, "A"), prim(g)):
        assert r.total == 7 and len(r.edges) == 3 and r.forest_components == 2


def test_ties_are_deterministic_and_same_total():
    g = Graph([("A", "B", 1), ("B", "C", 1), ("A", "C", 1), ("C", "D", 1)])
    assert [e.name for e in kruskal(g).edges] == [e.name for e in kruskal(g).edges]
    assert kruskal(g).total == prim(g, "A").total == 3


def test_path_and_none():
    g = Graph([("A", "B", 1), ("B", "C", 1), ("X", "Y", 1)])
    assert path(g, "A", "C") == ["A", "B", "C"] and path(g, "A", "A") == ["A"]
    assert path(g, "A", "X") is None
    with pytest.raises(KeyError):
        path(g, "A", "nope")


def test_unknown_prim_start():
    with pytest.raises(KeyError):
        prim(OFFICE(), "nope")


def test_long_chain_no_recursion_error():
    n = 5000
    g = Graph([(f"n{i}", f"n{i + 1}", 1) for i in range(n)])
    cuts, bridges = cut_vertices_and_bridges(g)
    assert len(bridges) == n and len(cuts) == n - 1


def test_single_edge_and_isolated_vertex():
    g = Graph([("A", "B", 2)], vertices=["Z"])
    assert kruskal(g).total == 2 and prim(g).total == 2
    assert cut_vertices_and_bridges(g) == ([], [("A", "B")])


# ---- reference tests: 300 random graphs vs networkx --------------------
def random_graph(rng: random.Random):
    n = rng.randint(2, 40)
    names = [f"v{i}" for i in range(n)]
    edges = {}
    for _ in range(rng.randint(0, n * 3)):
        a, b = rng.sample(names, 2)
        edges[tuple(sorted((a, b)))] = rng.choice([1, 2, 3, 4, 5, 7.5, 10])   # many ties
    return names, [(a, b, w) for (a, b), w in edges.items()]


@pytest.mark.parametrize("seed", range(300))
def test_matches_networkx(seed):
    names, edges = random_graph(random.Random(seed))
    g = Graph(edges, vertices=names)
    G = nx.Graph()
    G.add_nodes_from(names)
    G.add_weighted_edges_from(edges)
    ref = sum(d["weight"] for _, _, d in nx.minimum_spanning_tree(G).edges(data=True))
    k, p = kruskal(g), prim(g, rng_start(seed, names))
    c = nx.number_connected_components(G)
    assert k.total == pytest.approx(ref) and p.total == pytest.approx(ref)
    assert len(k.edges) == len(p.edges) == len(names) - c
    assert len(components(g)) == c
    assert sorted(g.cut_vertices_and_bridges()[0]) == sorted(nx.articulation_points(G))
    assert g.cut_vertices_and_bridges()[1] == sorted(tuple(sorted(b)) for b in nx.bridges(G))
    assert independent_cycles(g) == len(nx.cycle_basis(G))
    assert handshaking_holds(g)


def rng_start(seed, names):
    return random.Random(seed + 1).choice(names)
