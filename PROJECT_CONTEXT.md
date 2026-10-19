# PROJECT_CONTEXT — NetGraph Analyzer

> Living document. Update it with every meaningful change (what was built, what is pending, decisions).
> Last updated: 2026-10-19 · Branch `feature/netgraph-analyzer`

## 1. What this project is

- **Course:** Discrete Mathematics, Graphs and Trees unit. **Title:** *Graph Theory for Network Vulnerability and
  Secure Routing Analysis*. **Product:** NetGraph Analyzer, a free (₹0) Streamlit web app.
- **Team (3):** Tanish Parikh (graph model, properties, vulnerability), Saiyam Miglani (Kruskal, testing, compare,
  report), Arjun Shetty (Prim, UI, drawings, CI, deployment).
- **Dates in the source docs:** project 28 Sep – 16 Oct 2026, presentation 15 Oct, final submission 16 Oct.
- **Source documents** (PDFs given by the team): PRD (free edition), Project Proposal, Technical Architecture v1.0.
  This repo follows them; where this file differs, the decision is listed in section 5.

### Idea in one paragraph
A network is a weighted undirected graph (devices = vertices, links = edges, weight = cost in ₹ thousand). The
cheapest way to connect everything is a Minimum Spanning Tree, built here with Kruskal (union-find) and Prim
(min-heap), both written from scratch and verified against networkx. A tree has no redundancy, so every MST edge is
a bridge: the app shows the cost saving next to the loss of fault tolerance (cut vertices, bridges, failure test).

### Reference numbers (office sample, must stay true)
8 devices, 12 links, total 59. Degrees CR3 FW2 SA5 SB4 WS3 DB3 LS3 AP1 (sum 24 = 2×12). 5 independent cycles.
MST: 7 edges, cost 24 (59% saving). Full network: 1 bridge (AP–LS), 1 cut vertex (LS). MST: 7 bridges, 5 cut vertices
(CR, DB, LS, SA, SB). Losing SB–DB: full network stays connected, MST splits in 2. The Kruskal trace has 9 steps
(rejects CR–SB and FW–WS); Prim from CR adds CR–SA, SA–SB, CR–FW, SB–DB, DB–WS, SB–LS, LS–AP.

## 2. Requirements coverage (PRD)

| ID | Requirement | Priority | Status | Where |
|---|---|---|---|---|
| FR-01 | Built-in samples (8-device office, 12-device campus) | Must | Done | `data/`, `services/input.py` |
| FR-02 | CSV upload, bad rows rejected with row number | Must | Done | `services/input.py` |
| FR-03 | Add/remove/re-weight edges in a table | Should | Done | sidebar editor in `app.py` |
| FR-04 | Adjacency list and matrix | Must | Done | `core/graph.py`, tab 1 |
| FR-05 | Degrees, highlight hub | Must | Done | `core/properties.py`, tab 1 |
| FR-06 | BFS connectivity and components | Must | Done | `core/properties.py` |
| FR-07 | Path between two devices, cycle check | Must | Done | `core/properties.py`, tab 1 |
| FR-08 | Kruskal with union-find and reasoned step log | Must | Done | `core/kruskal.py` |
| FR-09 | Prim from chosen start with min-heap and log | Must | Done | `core/prim.py` |
| FR-10 | Step through one edge at a time | Should | Done | tab 2 (Previous/Next + slider) |
| FR-11 | Compare both, check against networkx | Must | Done | `services/analysis.py`, tab 3 |
| FR-12 | Full graph and MST side by side | Must | Done | `viz/draw.py`, tab 3 |
| FR-13 | Cut vertices and bridges, full graph and MST | Should | Done | `core/vulnerability.py`, tab 4 |
| FR-14 | Remove device/link and re-check connectivity | Should | Done | tab 4 |
| FR-15 | Export MST CSV and PNG | Could | Done | `services/export.py`, tab 3 |
| FR-16 | Theory note beside each result | Could | Done | `services/theory.py`, sidebar toggle |

Non-functional: 50-node analysis + drawing is far under 2 s (tested); >200 nodes shows a warning and skips drawing;
upload cap 1 MB; nothing stored; core modules have docstrings and type hints; only permissive licences.

## 3. Architecture (short)

Layers, calls go down only: `app.py` → `services/` → `core/` (pure Python) and `viz/`. networkx is used in tests and
for the on-screen cross-check/spring layout only, never inside the algorithms. Streamlit caches the analysis on the
sorted edge list (`st.cache_data`) so tab changes and stepping never recompute the MST.

## 4. Built so far

- [x] Core: Graph, properties, union-find, Kruskal, Prim, iterative Tarjan, failure test
- [x] Services: input validation, analysis, networkx check, export, theory notes
- [x] Streamlit app with four tabs, sample picker, upload, link editor, step-through, downloads
- [x] Drawings (fixed coordinates for samples, seeded spring layout for uploads)
- [x] 333 tests passing (known answers from the proposal, 300 random graphs vs networkx, CSV rules, app smoke tests)
- [x] CI workflow, README, this file

## 5. Decisions and deviations

- Folder `services/theory.py` holds theory notes; the architecture's "ui" layer is simply `app.py` + `viz/`.
- `MSTResult` and `Step` follow the architecture, plus `runtime_ms`, `start`, `forest_components` for the Compare tab.
- Kruskal REJECT reasons name the actual cycle (e.g. `cycle CR–SA–SB–CR`), matching the proposal's trace.
- Prim logs only accepted edges (stale heap entries are skipped, not logged), as in the proposal's trace.
- Row numbers in CSV errors count file lines (header = row 1).
- Weights are stored as floats and displayed without `.0` when whole.
- `campus_12.csv` was designed here (the PDFs only name it): 12 devices, 18 links, connected, with a few weight ties.
- Failure test runs live on selection (no separate button), on both the full network and the MST.
- Requirements are unpinned in `requirements.txt` (the architecture says to pin on the first deploy day).
- Dates in the source documents (presentation 15 Oct 2026) are already past on the day this was built; the plan and
  ownership are kept as written.

## 6. Pending

- Deploy to Streamlit Community Cloud and put the public link in README (Arjun); pin versions at that point.
- Manual interface checklist: sample → MST in ≤ 3 clicks, CSV errors visible, step-through (see section 7).
- Report (PDF) and slides: proofs of cut/cycle properties, complexity write-up, worked example (all three; Saiyam compiles).
- 2-minute backup screen recording of the demo.
- Optional: second reader review of each module (see ownership in README).

## 7. How to run and check

```bash
pip install -r requirements.txt
streamlit run app.py     # app on http://localhost:8501
pytest -q                # all tests
```
Manual checklist: open app (sample is preloaded) → tab *Kruskal and Prim* → press Next until step 9 (total 24) →
tab *Compare* (59 → 24, networkx all ✅) → tab *Vulnerability* (remove link SB–DB: full connected, MST splits).

## 8. Team split of the work

| Person | Modules | Tests/docs |
|---|---|---|
| Tanish | `core/graph.py`, `core/properties.py`, `core/vulnerability.py`, `services/input.py`, `services/export.py`, `data/` | `tests/test_input.py` |
| Saiyam | `core/kruskal.py`, `services/analysis.py`, `services/theory.py` | `tests/test_core.py`, report compile |
| Arjun | `core/prim.py`, `app.py`, `viz/draw.py`, CI, deployment | `tests/test_services.py` (app/drawing smoke), demo backup |

Workflow: feature branches, PR to `main`, one second reviewer per module, CI must be green.

## 9. Change log

- 2026-10-19 — First end-to-end version: core, services, app, tests, docs (branch `feature/netgraph-analyzer`).
