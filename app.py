"""NetGraph Analyzer: network input, algorithms, costs and failure analysis.

Owner: Arjun. Algorithms live in core/; this module presents their results.
Run with: streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from core.graph import Graph, fmt_weight
from core.properties import handshaking_holds, hubs
from core.vulnerability import failure_test
from services.analysis import (Analysis, analyze, comparison_rows, mst_graph,
                               same_edge_set)
from services.export import figure_png, mst_csv
from services.input import SAMPLES, build_graph, load_sample
from services.scenarios import location_name, rupees
from viz.draw import MAX_DRAW_NODES, draw_graph, layout

st.set_page_config(page_title="NetGraph | Network analysis", page_icon=":material/hub:", layout="wide")
st.html(Path(__file__).parent / "ui" / "styles.css")
ss = st.session_state


@st.cache_data(show_spinner=False)
def cached_analysis(edges: tuple, start: str | None) -> Analysis:
    """Cache algorithm results independently of the selected view."""
    return analyze(Graph(edges), start)


def show_errors(errors):
    st.error("The network contains invalid connections.")
    st.dataframe(pd.DataFrame(errors, columns=["Row", "Problem"]), hide_index=True)
    st.caption("Connections need a source, target and cost greater than zero.")


def edges_df(gr: Graph) -> pd.DataFrame:
    return pd.DataFrame([(e.u, e.v, e.w) for e in gr.edges()], columns=["source", "target", "weight"])


# Input controls stay separate from the working area.
st.sidebar.title("NetGraph")
st.sidebar.caption("Discrete Mathematics project")
st.sidebar.divider()
sample = st.sidebar.selectbox("Sample network", list(SAMPLES))
sid = ("sample", sample)
res, base_pos = load_sample(sample), SAMPLES[sample]["pos"]

ov = ss.get("override")
if ov and ov["sid"] == sid and res.ok:
    res = build_graph(ov["rows"])
if not res.ok:
    show_errors(res.errors)
    st.stop()

g = res.graph
scenario = SAMPLES[sample]
facilities = scenario.get("facilities", {})
label = lambda v: location_name(v, facilities)
device_option = lambda v: f"{label(v)} ({v})" if v in facilities else v
money = rupees if facilities else fmt_weight
illustrated = False
if facilities:
    with st.sidebar.expander("Display options"):
        illustrated = st.toggle("Illustrated facilities", value=True)
verts = g.vertices
preferred = "LIB" if facilities and "LIB" in verts else "CR"
with st.sidebar.expander("Prim settings"):
    start = st.selectbox("Prim start vertex", verts,
                         index=verts.index(preferred) if preferred in verts else 0,
                         format_func=device_option)
for msg in res.infos:
    st.sidebar.caption(msg)

# Calculate once; every view reads the same graph.
a = cached_analysis(tuple((e.u, e.v, e.w) for e in g.edges()), start)
too_big = len(g) > MAX_DRAW_NODES
pos = None if too_big else layout(g, base_pos, facility_mode=bool(facilities))
mst_keys = [e.key for e in a.kruskal.edges]
mst = mst_graph(g, a.kruskal)
has_ties = len({e.w for e in g.edges()}) < len(g.edges())

if facilities:
    st.title("MPSTME Mumbai")
    st.caption(f"{len(g)} facilities · {len(g.edges())} proposed connections · Illustrative installation costs")
else:
    st.title(sample.split(" (")[0])
    st.caption("Weighted, undirected network · Positive connection costs")
if too_big:
    st.warning(f"{len(g)} devices exceeds the drawing limit of {MAX_DRAW_NODES}. Analysis is available; drawings and the matrix are omitted.")
if not a.connected:
    st.warning("Disconnected network. A minimum spanning forest is shown. Components: "
               + "; ".join(f"{i + 1}: {', '.join(c)}" for i, c in enumerate(a.components)))


def show_fig(fig):
    st.pyplot(fig, width="stretch")


def draw(gr, **kwargs):
    return draw_graph(gr, pos, facilities=facilities if illustrated else None,
                      weight_label=money, **kwargs)


def edit_connections():
    """Full-width editor avoids hiding cost columns in the sidebar."""
    with st.expander("Edit connections"):
        st.caption("Weights use the same units as the input CSV. Changes apply to this session.")
        ver = ss.get("ver", 0)
        edited = st.data_editor(edges_df(g), num_rows="dynamic", hide_index=True,
                                key=f"editor_{sid}_{ver}", width="stretch")
        apply, reset, _ = st.columns([1, 1, 4])
        if apply.button("Apply edits", type="primary"):
            rows = [(i + 2, r.source if pd.notna(r.source) else "",
                     r.target if pd.notna(r.target) else "",
                     r.weight if pd.notna(r.weight) else "")
                    for i, r in enumerate(edited.itertuples())]
            new = build_graph(rows)
            if new.ok:
                ss["override"] = {"sid": sid, "rows": rows}
                ss["ver"] = ver + 1
                st.rerun()
            for n, message in new.errors:
                st.error(f"Row {n}: {message}")
        if ov and ov["sid"] == sid and reset.button("Reset to original"):
            ss.pop("override", None)
            ss["ver"] = ver + 1
            st.rerun()


tab1, tab2, tab3, tab4 = st.tabs(["Network", "Algorithms", "Costs", "Failures"])

with tab1:
    c = st.columns(4)
    c[0].metric("Facilities" if facilities else "Devices", len(g))
    c[1].metric("Connections", len(g.edges()))
    c[2].metric("Connected", "Yes" if a.connected else f"No · {len(a.components)} groups")
    c[3].metric("Independent cycles", a.cycles)
    if pos:
        show_fig(draw(g))
    edit_connections()
    with st.expander("Graph data"):
        hub = hubs(g)
        st.caption("Highest degree: " + ", ".join(label(v) for v in hub))
        st.caption(f"Sum of degrees: {sum(a.degrees.values())} = 2 × {len(g.edges())}"
                   + (" · Handshaking Lemma verified" if handshaking_holds(g) else " · Check failed"))
        left, right = st.columns(2)
        with left:
            st.subheader("Degrees")
            st.dataframe(pd.DataFrame([{"Device": device_option(v), "Degree": d}
                                       for v, d in a.degrees.items()]), hide_index=True)
        with right:
            st.subheader("Adjacency list")
            st.dataframe(pd.DataFrame([{"Device": v, "Neighbours (cost)": ", ".join(
                f"{n} ({fmt_weight(w)})" for n, w in sorted(g.adj[v].items()))} for v in verts]), hide_index=True)
        if not too_big:
            st.subheader("Adjacency matrix")
            vs, matrix = g.adjacency_matrix()
            st.dataframe(pd.DataFrame(matrix, index=vs, columns=vs).map(lambda x: fmt_weight(x) if x else "·"))
    st.subheader("Find a path")
    p1, p2 = st.columns(2)
    s = p1.selectbox("From", verts, key="path_s", format_func=device_option)
    t = p2.selectbox("To", verts, index=min(1, len(verts) - 1), key="path_t", format_func=device_option)
    path = g.path(s, t)
    if path is None:
        st.warning(f"No path between {label(s)} and {label(t)}: they are in different components.")
    else:
        cost = sum(g.weight(x, y) for x, y in zip(path, path[1:]))
        st.write(" → ".join(label(v) for v in path))
        hops = len(path) - 1
        st.caption(f"{hops} {'hop' if hops == 1 else 'hops'} · Path cost {money(cost)} · BFS, minimum hops")

with tab2:
    alg = st.radio("Algorithm", ["Kruskal", "Prim"], horizontal=True)
    r = a.kruskal if alg == "Kruskal" else a.prim
    n = len(r.steps)
    ctx = (sid, ss.get("ver", 0), alg, start)
    if ss.get("step_ctx") != ctx:
        ss["step_ctx"], ss["step"] = ctx, 1

    def go(delta):
        ss["step"] = max(1, min(n, ss["step"] + delta))

    b1, b2, b3 = st.columns([1, 1, 6])
    b1.button("Previous", on_click=go, args=(-1,), disabled=ss["step"] <= 1)
    b2.button("Next", on_click=go, args=(1,), disabled=ss["step"] >= n)
    step = b3.slider("Step", 1, n, key="step") if n > 1 else 1
    cur = r.steps[step - 1]
    done = r.steps[:step]
    accepted = [x.edge.key for x in done if x.action == "ACCEPT"]
    rejected = [x.edge.key for x in done if x.action == "REJECT"]
    edge_label = f"{label(cur.edge.u)} – {label(cur.edge.v)}" if facilities else cur.edge.name
    st.markdown(f"**{step} / {n} · {edge_label}** · {money(cur.edge.w)} · {cur.action.title()}")
    st.caption(cur.reason)
    st.caption(f"Selected cables: {len(accepted)} / {len(r.edges)} · Rejected cables: {len(rejected)}")
    if alg == "Kruskal":
        st.caption("Steps count examined cables, including rejections. Rejected cables are excluded from the selected network.")
    else:
        st.caption("Steps count cables added to the tree. Already-connected heap entries are skipped without a displayed step.")
    show_rejected = st.toggle("Show rejected cables", value=False) if alg == "Kruskal" else False
    if cur.action == "REJECT":
        st.info(f"{edge_label} was rejected because it creates a cycle. The selected network has not changed.")
    if pos:
        show_fig(draw(g, tree=accepted, rejected=rejected if show_rejected else (),
                      current=cur.edge.key if cur.action == "ACCEPT" or show_rejected else None,
                      show_unused=False))
        st.caption("Only selected cables are drawn" + ("; rejected cables are dotted red." if show_rejected else "."))
    if step == n:
        st.caption(f"{alg} finished: {len(r.edges)} edges, total cost {money(r.total)}.")
    if alg == "Prim":
        st.caption(f"Start: {device_option(r.start or verts[0])}")
    if has_ties:
        st.caption("Equal weights use vertex IDs for repeatable ordering. Other MSTs can have the same total cost.")
    with st.expander("Step log"):
        log = pd.DataFrame([{"Step": x.step, "Connection": x.edge.name, "Weight": fmt_weight(x.edge.w),
                             "Action": x.action.title(), "Reason": x.reason} for x in done])
        st.dataframe(log, hide_index=True)
        if facilities:
            st.caption("Log weights use CSV units: ₹1,000 each.")

with tab3:
    c = st.columns(4)
    c[0].metric("Full network cost", money(a.full_total))
    c[1].metric("MST cost", money(a.mst_total))
    c[2].metric("Saved", money(a.saving), f"{a.saving_pct:.0f}% lower")
    c[3].metric("Connections", f"{len(g.edges())} → {len(a.kruskal.edges)}")
    if facilities:
        st.caption("Estimates for a new installation. Full cost assumes building every proposed connection.")
    if not a.same_total:
        st.error("Kruskal and Prim totals differ. Check the analysis.")
    view = st.radio("Drawing", ["Minimum-cost design", "All connections", "Side by side"], horizontal=True)
    if pos:
        if view == "Side by side":
            left, right = st.columns(2)
            with left:
                st.caption("All proposed connections")
                show_fig(draw(g, tree=mst_keys))
            with right:
                st.caption("Minimum-cost design")
                show_fig(draw(g, tree=mst_keys, show_unused=False))
        else:
            show_fig(draw(g, tree=mst_keys, show_unused=view == "All connections"))
    dl1, dl2, _ = st.columns([1, 1, 4])
    dl1.download_button("Download CSV", mst_csv(a.kruskal.edges), "mst.csv", "text/csv")
    if pos:
        dl2.download_button("Download PNG", figure_png(draw(
            g, tree=mst_keys, show_unused=False,
            title="Minimum-cost connected design" if a.connected else "Minimum-cost forest (disconnected)", dpi=220)), "mst.png", "image/png")
    with st.expander("Algorithm comparison"):
        st.dataframe(pd.DataFrame(comparison_rows(a)), hide_index=True)
        if a.same_total:
            st.caption("Both algorithms agree on total cost." + ("" if same_edge_set(a) else " Equal-weight ties produce different edge sets."))

with tab4:
    st.subheader("Simulate an outage")
    controls1, controls2 = st.columns([1, 3])
    with controls1:
        kind = st.radio("Remove a", ["device", "link"], index=1 if facilities else 0,
                        horizontal=True, format_func=lambda x: {"device": "Switch", "link": "Cable"}[x])
    with controls2:
        if kind == "device":
            pick = st.selectbox("Device", verts, format_func=device_option)
            args = dict(vertex=pick)
            incident = label(pick)
        else:
            names = {e.name: e for e in g.edges()}
            demo_edge = next((name for name, e in names.items() if e.key == ("RES", "ROB")), None)
            pick = st.selectbox("Link", list(names), index=list(names).index(demo_edge) if facilities and demo_edge else 0,
                format_func=lambda name: f"{label(names[name].u)} — {label(names[name].v)}")
            args = dict(edge=names[pick].key)
            incident = f"{label(names[pick].u)} — {label(names[pick].v)}"
    failure_results = {}
    for col, design_name, gr in zip(st.columns(2), ("Full network", "Minimum spanning tree"), (g, mst)):
        with col:
            fr = failure_test(gr, **args) if kind == "device" or gr.has_edge(*args["edge"]) else None
            failure_results[design_name] = (gr, fr)
            st.caption(design_name)
            if fr is None:
                st.write("Unchanged")
                st.caption("This connection is not in the selected design.")
            elif fr.split:
                st.error(f"{len(fr.components)} disconnected groups")
            else:
                st.write("Connected" if fr.connected else f"{len(fr.components)} groups · unchanged")
    result_design = st.radio("View the network after failure", ["Minimum spanning tree", "Full network"], horizontal=True,
                             format_func=lambda x: "Minimum-cost design" if x == "Minimum spanning tree" else "All connections")
    before, result = failure_results[result_design]
    after = before.copy()
    failed_edges, failed_vertices = [], []
    if result:
        if kind == "device":
            after.remove_vertex(args["vertex"])
            failed_vertices = [args["vertex"]]
        else:
            after.remove_edge(*args["edge"])
            failed_edges = [args["edge"]]
    groups = result.components if result else before.components()
    if pos:
        show_fig(draw(after, components=groups, failed_edges=failed_edges, failed_vertices=failed_vertices))
    if result:
        st.caption(f"Removed: {incident}. " + ("Separate groups cannot communicate with each other." if result.split else "No additional split in the remaining network."))
    with st.expander("Connected groups"):
        for i, group in enumerate(groups, start=1):
            st.write(f"**Group {i}:** " + ", ".join(label(v) for v in group))
        st.caption("This checks connectivity, not internet access or packet routing.")
    with st.expander("Single points of failure"):
        st.caption("These results describe each design before the simulated outage above. A bridge is a cable whose removal splits the network; a cut vertex is a switch whose removal splits the remaining switches.")
        for col, design_name, gr, cv, br in zip(st.columns(2), ("Full network", "Minimum spanning tree"),
                (g, mst), (a.cut_vertices, a.mst_cut_vertices), (a.bridges, a.mst_bridges)):
            with col:
                st.subheader(design_name)
                st.write(f"{len(br)} bridges · {len(cv)} cut vertices")
                st.caption("Cut vertices: " + (", ".join(label(v) for v in cv) or "None"))
                st.caption("Bridges: " + (", ".join(f"{label(x)} — {label(y)}" for x, y in br) or "None"))
        critical_view = st.radio("Highlight weak points in", ["Minimum-cost design", "All proposed connections"], horizontal=True)
        cg, cuts, brs = ((mst, a.mst_cut_vertices, a.mst_bridges) if critical_view == "Minimum-cost design"
                         else (g, a.cut_vertices, a.bridges))
        if pos:
            show_fig(draw(cg, tree=[e.key for e in cg.edges()], bridges=brs, cut_vertices=cuts))
