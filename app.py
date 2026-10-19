"""NetGraph Analyzer: Streamlit entry point (sidebar, four tabs, downloads).

Owner: Arjun. All algorithms live in core/; this file only wires the UI.
Run with:  streamlit run app.py
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from core.graph import Graph, fmt_weight
from core.properties import handshaking_holds, hubs
from core.vulnerability import failure_test
from services.analysis import (Analysis, analyze, comparison_rows, mst_graph,
                               networkx_check, same_edge_set)
from services.export import figure_png, mst_csv
from services.input import SAMPLES, TEMPLATE_CSV, build_graph, load_sample, parse_csv
from services.theory import THEORY
from viz.draw import MAX_DRAW_NODES, draw_graph, layout

st.set_page_config(page_title="NetGraph Analyzer", page_icon="🕸️", layout="wide")
ss = st.session_state


@st.cache_data(show_spinner=False)
def cached_analysis(edges: tuple, start: str | None) -> Analysis:
    """Analysis is keyed on the sorted edge list, so tab changes never recompute it."""
    return analyze(Graph(edges), start)


def show_errors(errors, infos=()):
    st.error("The network could not be loaded. Fix these rows and upload again.")
    st.dataframe(pd.DataFrame(errors, columns=["Row", "Problem"]), hide_index=True)
    st.markdown("Expected header: `source,target,weight`")
    st.download_button("Download CSV template", TEMPLATE_CSV, "template.csv", "text/csv")


def edges_df(g: Graph) -> pd.DataFrame:
    return pd.DataFrame([(e.u, e.v, e.w) for e in g.edges()], columns=["source", "target", "weight"])


# ---------------------------------------------------------------- sidebar
st.sidebar.title("🕸️ NetGraph Analyzer")
sample = st.sidebar.selectbox("Sample network", list(SAMPLES))
upload = st.sidebar.file_uploader("…or upload a CSV edge list", type=["csv"],
                                  help="Columns: source,target,weight (cost > 0)")
theory_on = st.sidebar.toggle("Theory notes", value=True)

if upload is not None:
    data = upload.getvalue()
    sid = ("upload", upload.name, len(data))
    res, base_pos = parse_csv(data), None
else:
    sid = ("sample", sample)
    res, base_pos = load_sample(sample), SAMPLES[sample]["pos"]

ov = ss.get("override")
if ov and ov["sid"] == sid and res.ok:
    res = build_graph(ov["rows"])

if not res.ok:
    show_errors(res.errors)
    st.stop()
g = res.graph
for msg in res.infos:
    st.sidebar.info(msg)

with st.sidebar.expander("Edit links (add / remove / re-weight)"):
    ver = ss.get("ver", 0)
    edited = st.data_editor(edges_df(g), num_rows="dynamic", hide_index=True,
                            key=f"editor_{sid}_{ver}")
    if st.button("Apply edits"):
        rows = [(i + 2, r.source if pd.notna(r.source) else "", r.target if pd.notna(r.target) else "",
                 r.weight if pd.notna(r.weight) else "") for i, r in enumerate(edited.itertuples())]
        new = build_graph(rows)
        if new.ok:
            ss["override"] = {"sid": sid, "rows": rows}
            ss["ver"] = ver + 1
            st.rerun()
        else:
            for n, m in new.errors:
                st.error(f"Row {n}: {m}")
    if ov and ov["sid"] == sid and st.button("Reset to original"):
        ss.pop("override", None)
        ss["ver"] = ss.get("ver", 0) + 1
        st.rerun()

verts = g.vertices
start = st.sidebar.selectbox("Prim start vertex", verts, index=verts.index("CR") if "CR" in verts else 0)

# ---------------------------------------------------------------- analysis
a = cached_analysis(tuple((e.u, e.v, e.w) for e in g.edges()), start)
too_big = len(g) > MAX_DRAW_NODES
pos = None if too_big else layout(g, base_pos)
mst_keys = [e.key for e in a.kruskal.edges]
mst = mst_graph(g, a.kruskal)

st.title("NetGraph Analyzer")
st.caption("Cheapest way to connect every device, and where the network is fragile.")
if too_big:
    st.warning(f"{len(g)} devices is more than {MAX_DRAW_NODES}: drawings and the adjacency matrix "
               "are skipped. The analysis is still shown.")
if not a.connected:
    st.warning("The network is **disconnected**, so a minimum spanning forest is built. Components: "
               + "; ".join(f"{i + 1}: {', '.join(c)}" for i, c in enumerate(a.components)))
if len({e.w for e in g.edges()}) < len(g.edges()):
    st.info("Some links have equal weights. Ties are broken by edge name, so results are repeatable. "
            "The MST may not be unique, but its total weight is.")


def note(key: str):
    if theory_on:
        st.info(THEORY[key])


def show_fig(fig):
    st.pyplot(fig, width="stretch")


tab1, tab2, tab3, tab4 = st.tabs(["Graph properties", "Kruskal and Prim", "Compare", "Vulnerability"])

# ---------------------------------------------------------------- tab 1
with tab1:
    note("properties")
    hub = hubs(g)
    c = st.columns(5)
    c[0].metric("Devices", len(g))
    c[1].metric("Links", len(g.edges()))
    c[2].metric("Connected?", "Yes" if a.connected else f"No ({len(a.components)} parts)")
    c[3].metric("Independent cycles", a.cycles)
    c[4].metric("Hub (max degree)", ", ".join(hub))
    st.caption("Has cycles: " + ("yes" if a.cycles else "no") +
               f"  ·  Σ deg(v) = {sum(a.degrees.values())} = 2 × {len(g.edges())}"
               + ("  ✓ Handshaking Lemma" if handshaking_holds(g) else "  ✗"))
    if pos:
        show_fig(draw_graph(g, pos, title="Network"))
    left, right = st.columns(2)
    with left:
        st.subheader("Degree table")
        st.dataframe(pd.DataFrame([{"Device": v, "Degree": d, "Hub": "★" if v in hub else ""}
                                   for v, d in a.degrees.items()]), hide_index=True)
    with right:
        st.subheader("Adjacency list")
        st.dataframe(pd.DataFrame([{"Device": v, "Neighbours (cost)": ", ".join(
            f"{n} ({fmt_weight(w)})" for n, w in sorted(g.adj[v].items()))} for v in verts]),
            hide_index=True)
    if not too_big:
        st.subheader("Adjacency matrix")
        vs, m = g.adjacency_matrix()
        st.dataframe(pd.DataFrame(m, index=vs, columns=vs).map(lambda x: fmt_weight(x) if x else "·"))
    st.subheader("Path finder")
    p1, p2 = st.columns(2)
    s = p1.selectbox("From", verts, key="path_s")
    t = p2.selectbox("To", verts, index=min(1, len(verts) - 1), key="path_t")
    pth = g.path(s, t)
    if pth is None:
        st.warning(f"No path between {s} and {t}: they are in different components.")
    else:
        cost = sum(g.weight(x, y) for x, y in zip(pth, pth[1:]))
        st.success(f"Fewest-hop path ({len(pth) - 1} hops, cost {fmt_weight(cost)}): " + " → ".join(pth))

# ---------------------------------------------------------------- tab 2
with tab2:
    alg = st.radio("Algorithm", ["Kruskal", "Prim"], horizontal=True)
    note("kruskal" if alg == "Kruskal" else "prim")
    r = a.kruskal if alg == "Kruskal" else a.prim
    n = len(r.steps)
    ctx = (sid, ss.get("ver", 0), alg, start)
    if ss.get("step_ctx") != ctx:
        ss["step_ctx"], ss["step"] = ctx, 1

    def go(delta):
        ss["step"] = max(1, min(n, ss["step"] + delta))

    b1, b2, b3 = st.columns([1, 1, 6])
    b1.button("◀ Previous", on_click=go, args=(-1,), disabled=ss["step"] <= 1)
    b2.button("Next ▶", on_click=go, args=(1,), disabled=ss["step"] >= n)
    step = b3.slider("Step", 1, n, key="step") if n > 1 else 1
    cur = r.steps[step - 1]
    done = r.steps[:step]
    accepted = [x.edge.key for x in done if x.action == "ACCEPT"]
    rejected = [x.edge.key for x in done if x.action == "REJECT"]
    verb = "accepted" if cur.action == "ACCEPT" else "rejected"
    st.markdown(f"**Step {step} of {n}:** {cur.edge.name} (cost {fmt_weight(cur.edge.w)}) "
                f"**{verb}**, {cur.reason}.")
    if alg == "Prim":
        in_tree = {r.edges[0].u} if r.edges else set()
        for x in done:
            in_tree |= {x.edge.u, x.edge.v}
        st.caption(f"Start: {r.start or verts[0]}  ·  tree so far: {', '.join(sorted(in_tree))}")
    cA, cB = st.columns([3, 2])
    with cA:
        if pos:
            show_fig(draw_graph(g, pos, tree=accepted, rejected=rejected, current=cur.edge.key,
                                title=f"{alg}: step {step}"))
    with cB:
        log = pd.DataFrame([{"Step": x.step, "Edge": x.edge.name, "Weight": fmt_weight(x.edge.w),
                             "Action": x.action.title(), "Reason": x.reason} for x in done])
        st.dataframe(log.style.apply(
            lambda row: ["background-color: #d8f3dc" if row.name == step - 1 else "" for _ in row], axis=1),
            hide_index=True)
    if step == n:
        st.success(f"{alg} finished: {len(r.edges)} edges, total cost {fmt_weight(r.total)}.")

# ---------------------------------------------------------------- tab 3
with tab3:
    note("compare")
    c = st.columns(4)
    c[0].metric("Full network cost", fmt_weight(a.full_total))
    c[1].metric("MST cost", fmt_weight(a.mst_total))
    c[2].metric("Saved", fmt_weight(a.saving), f"{a.saving_pct:.0f}% lower")
    c[3].metric("Links", f"{len(g.edges())} → {len(a.kruskal.edges)}")
    if a.same_total:
        st.success(f"Kruskal and Prim both reach total weight {fmt_weight(a.kruskal.total)}."
                   + ("" if same_edge_set(a) else " The edge sets differ (equal-weight ties), but the cost is the same."))
    else:
        st.error("Kruskal and Prim totals differ. This should never happen.")
    if pos:
        l, rr = st.columns(2)
        with l:
            show_fig(draw_graph(g, pos, tree=mst_keys, title="Full network (MST in blue)"))
        with rr:
            fig_mst = draw_graph(g, pos, tree=mst_keys, show_unused=False, title="Minimum spanning tree")
            show_fig(fig_mst)
    st.dataframe(pd.DataFrame(comparison_rows(a)), hide_index=True)
    with st.expander("Check against networkx", expanded=True):
        chk = networkx_check(g, a)
        ok = lambda b: "✅ match" if b else "❌ mismatch"
        st.dataframe(pd.DataFrame([
            {"Check": f"MST weight (networkx = {fmt_weight(chk['nx_total'])}), Kruskal", "Result": ok(chk["kruskal_ok"])},
            {"Check": "MST weight, Prim", "Result": ok(chk["prim_ok"])},
            {"Check": "Connected components", "Result": ok(chk["components_ok"])},
            {"Check": "Cut vertices", "Result": ok(chk["cut_vertices_ok"])},
            {"Check": "Bridges", "Result": ok(chk["bridges_ok"])},
        ]), hide_index=True)
    d1, d2, _ = st.columns([1, 1, 4])
    d1.download_button("⬇ MST edge list (CSV)", mst_csv(a.kruskal.edges), "mst.csv", "text/csv")
    if pos:
        d2.download_button("⬇ Drawing (PNG)", figure_png(draw_graph(
            g, pos, tree=mst_keys, show_unused=False, title="Minimum spanning tree", dpi=220)),
            "mst.png", "image/png")

# ---------------------------------------------------------------- tab 4
with tab4:
    note("vulnerability")
    cols = st.columns(2)
    for col, (label, gr, cv, br) in zip(cols, [("Full network", g, a.cut_vertices, a.bridges),
                                              ("Minimum spanning tree", mst, a.mst_cut_vertices, a.mst_bridges)]):
        with col:
            st.subheader(label)
            m1, m2 = st.columns(2)
            m1.metric("Bridges (single-link failures)", len(br))
            m2.metric("Cut vertices (single-device failures)", len(cv))
            if pos:
                show_fig(draw_graph(gr, pos, tree=[e.key for e in gr.edges()] if label != "Full network" else (),
                                    bridges=br, cut_vertices=cv, title=f"{label}: bridges red, cut vertices orange"))
            st.write("**Cut vertices:** " + (", ".join(cv) or "none"))
            st.write("**Bridges:** " + (", ".join(f"{x}–{y}" for x, y in br) or "none"))
    st.subheader("Failure test")
    kind = st.radio("Remove a", ["device", "link"], horizontal=True)
    if kind == "device":
        pick = st.selectbox("Device", verts)
        args = dict(vertex=pick)
    else:
        names = {e.name: e for e in g.edges()}
        pick = st.selectbox("Link", list(names))
        args = dict(edge=names[pick].key)
    f1, f2 = st.columns(2)
    for col, label, gr in [(f1, "Full network", g), (f2, "Minimum spanning tree", mst)]:
        with col:
            if kind == "link" and not gr.has_edge(*args["edge"]):
                st.info(f"{label}: this link is not in the tree, so removing it changes nothing.")
                continue
            fr = failure_test(gr, **args)
            if fr.split:
                st.error(f"{label}: losing {fr.removed} splits the network into {len(fr.components)} parts: "
                         + " | ".join(",".join(c) for c in fr.components))
            else:
                st.success(f"{label}: still {'connected' if fr.connected else 'in the same ' + str(len(fr.components)) + ' parts'} "
                           f"after losing {fr.removed}.")
