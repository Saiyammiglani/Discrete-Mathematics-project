# PROJECT_CONTEXT — NetGraph Analyzer

> Living document. Update it with every meaningful change (what was built, what is pending, decisions).
> Last updated: 2026-10-20 · Local MPSTME facility illustrations added; not yet committed or deployed

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
| FR-01 | Built-in MPSTME and 8-device office samples | Must | Adjusted by user | `data/`, `services/input.py`; original 12-device sample removed |
| FR-02 | CSV upload, bad rows rejected with row number | Must | Upload UI removed at user request | Parser retained for sample loading and tests |
| FR-03 | Add/remove/re-weight edges in a table | Should | Done | sidebar editor in `app.py` |
| FR-04 | Adjacency list and matrix | Must | Done | `core/graph.py`, tab 1 |
| FR-05 | Degrees, highlight hub | Must | Adjusted by user | Degrees and highest-degree caption retained; Hub column removed |
| FR-06 | BFS connectivity and components | Must | Done | `core/properties.py` |
| FR-07 | Path between two devices, cycle check | Must | Done | `core/properties.py`, tab 1 |
| FR-08 | Kruskal with union-find and reasoned step log | Must | Done | `core/kruskal.py` |
| FR-09 | Prim from chosen start with min-heap and log | Must | Done | `core/prim.py` |
| FR-10 | Step through one edge at a time | Should | Done | tab 2 (Previous/Next + slider) |
| FR-11 | Compare both, check against networkx | Must | Adjusted by user | Algorithm comparison retained; reference checks run in tests, removed from UI |
| FR-12 | Full graph and MST side by side | Must | Done | `viz/draw.py`, tab 3 |
| FR-13 | Cut vertices and bridges, full graph and MST | Should | Done | `core/vulnerability.py`, tab 4 |
| FR-14 | Remove device/link and re-check connectivity | Should | Done | tab 4 |
| FR-15 | Export MST CSV and PNG | Could | Done | `services/export.py`, tab 3 |
| FR-16 | Theory note beside each result | Could | Removed at user request | Theory UI and service deleted |

Non-functional: 50-node analysis + drawing is far under 2 s (tested); >200 nodes shows a warning and skips drawing;
connection edits stay in the session; core modules have docstrings and type hints; only permissive licences.

## 3. Architecture (short)

Layers, calls go down only: `app.py` → `services/` → `core/` (pure Python) and `viz/`. networkx is used in tests and
for reference tests and automatic layouts only, never inside the algorithms. Streamlit caches the analysis on the
sorted edge list (`st.cache_data`) so tab changes and stepping never recompute the MST.

## 4. Built so far

- [x] Core: Graph, properties, union-find, Kruskal, Prim, iterative Tarjan, failure test
- [x] Services: input validation, analysis, networkx check, export
- [x] Streamlit app with four tabs, sample picker, link editor, step-through, downloads
- [x] Drawings (fixed coordinates for samples, seeded spring layout for custom networks)
- [x] 354 tests (known answers, 300 random graphs vs networkx, CSV rules, app smoke tests,
  MPSTME cost/trace/failure results, room rendering and layout)
- [x] CI workflow, README, this file

## 5. Decisions and deviations

- The architecture's "ui" layer is `app.py` + `viz/`, with theme CSS in `ui/`.
- `MSTResult` and `Step` follow the architecture, plus `runtime_ms`, `start`, `forest_components` for the Compare tab.
- Kruskal REJECT reasons name the actual cycle (e.g. `cycle CR–SA–SB–CR`), matching the proposal's trace.
- Prim logs only accepted edges (stale heap entries are skipped, not logged), as in the proposal's trace.
- Row numbers in CSV errors count file lines (header = row 1).
- Weights are stored as floats and displayed without `.0` when whole.
- The original 12-device campus sample and optional theory-notes feature were removed at the user's request.
- Failure test runs live on selection (no separate button), on both the full network and the MST.
- Runtime dependencies are pinned in `requirements.txt`; pytest is pinned separately in `requirements-dev.txt`. Python 3.12 is the deployment target.
- Dates in the source documents (presentation 15 Oct 2026) are already past on the day this was built; the plan and
  ownership are kept as written.

## 6. Pending

Current user instruction (20 Oct): tag the previous remote version, debug current files, push the
necessary changes and tag the next release, then deploy to Streamlit. This supersedes the earlier no-push instruction.

Full task list with owners: see [REMAINING_WORK.md](REMAINING_WORK.md).

- Deploy to Streamlit Community Cloud and verify the public URL. Pins and deployment guide are prepared; publication and cloud account access remain pending. See DEPLOYMENT.md.
- Manual interface checklist: sample → MST in ≤ 3 clicks, editor validation, step-through (see section 7).
- Report (PDF) and slides: proofs of cut/cycle properties, complexity write-up, worked example (all three; Saiyam compiles).
- 2-minute backup screen recording of the demo.
- Optional: second reader review of each module (see ownership in README).

## 7. How to run and check

```bash
pip install -r requirements-dev.txt
streamlit run app.py     # app on http://localhost:8501
pytest -q                # all tests
```
Office regression checklist: choose *Office network (8 devices)* → tab *Algorithms* → press Next until step 9 (total 24) →
tab *Costs* (59 → 24) → tab *Failures* (remove cable SB–DB: full connected, MST splits).

Default MPSTME demo: 6 rooms/9 proposed cables, costs ₹38,000 → ₹16,000. Kruskal rejects LIB-ROB at step 5
and completes at step 6. Remove ROB-RES: full network survives; MST separates PRINT/RES from the other four
rooms. Facility metadata and fixed schematic coordinates live outside the graph core. Furniture/equipment
are illustrations inside a vertex, not additional nodes. The office sample and connection editor remain available; campus sample and CSV upload UI were removed. See README for the complete, tie-checked demo trace.

## 8. Team split of the work

| Person | Modules | Tests/docs |
|---|---|---|
| Tanish | `core/graph.py`, `core/properties.py`, `core/vulnerability.py`, `services/input.py`, `services/export.py`, `data/` | `tests/test_input.py` |
| Saiyam | `core/kruskal.py`, `services/analysis.py` | `tests/test_core.py`, report compile |
| Arjun | `core/prim.py`, `app.py`, `viz/draw.py`, CI, deployment | `tests/test_services.py` (app/drawing smoke), demo backup |

Workflow: feature branches, PR to `main`, one second reviewer per module, CI must be green.

## 9. Change log

- 2026-10-20 — User authorized tags, GitHub publication and Streamlit deployment. Published baseline
  tag v1.0.0 at 327db19. Release review fixed CSV escaping/float precision and disconnected export
  titles; added regression coverage. Release target v1.1.0.

- 2026-10-20 — Began Streamlit Cloud deployment preparation: pinned tested runtime dependencies,
  separated test dependencies, updated CI installation, added DEPLOYMENT.md and excluded generated
  output from Git. Refreshed user-adjusted requirements and remaining-work status. Release checks:
  353 passed, pip check clean, diff check clean. Cloud account setup is open; GitHub publication
  awaits resolution of the earlier no-push instruction. No public URL yet.

- 2026-10-20 — Removed Hub table column and Reference checks UI. Algorithm diagrams now show only
  selected cables by default, with an optional rejected-cable overlay and explicit rejection message.
  Clarified that single points of failure are computed on each design before the simulated outage.

- 2026-10-20 — Removed CSV upload controls and upload-specific app routing at the user's request.
  Sample selection, connection editing and CSV/PNG downloads remain. Local changes only.

- 2026-10-20 — Audited both sample networks, every recorded MST step and single cable/switch outage
  in both diagram modes. Shared cable styles/accurate legends now govern all views; current rejections
  are explicitly labelled, plain diagrams show failure markers and component colours, and MPSTME
  currency remains consistent when illustrations are off. Upload identity includes content to prevent
  edits carrying over to a different same-length file. Full suite: 353 passed. Reviewed ten rendered
  views in output/verification/graph_audit/contact_sheet.png. Local changes only; no commit or push.

- 2026-10-20 — Fixed current-step highlighting overriding rejected cable styling in both diagram modes.
  Split facility legend labels and added selected/rejected counts plus trace-count explanations.
  Kruskal still correctly records five accepts and one rejection; Prim records five additions.

- 2026-10-20 — Removed the Case study assumptions expander from the Network page at the user's request.
  Local UI change only; no commit or push.

- 2026-10-20 — Removed the theory-notes toggle, rendering and service, plus the 12-device campus
  dataset/sample and its obsolete smoke test, as requested. MPSTME, office and CSV upload remain.
  This intentionally changes original PRD FR-01/FR-16. Local changes only; no push.

- 2026-10-20 — Simplified the local UI: restrained light/green theme, Network/Algorithms/Costs/Failures
  navigation, compact results, full-width connection editor, collapsible theory/graph data/reference checks,
  a single comparison drawing selector, and failure controls before the diagrams. Removed emoji labels,
  decorative taglines and routine success banners. Refined facility illustration colours and borders.
  The upload widget now advertises/enforces 1 MB. CSV escaping/precision fixes remain pending.
  Regression suite: 337 passed. No push or deployment; user explicitly requested local-only work.
- 2026-10-20 — Redesigned Network/Costs/Failures views checked in the desktop browser. Browser authority
  restrictions interrupted the final phone-size recheck and screenshot capture; do not record that mobile
  recheck as passed. Responsive CSS is present. Earlier mobile emulation checks refer to the older UI.

- 2026-10-20 — Added local MPSTME Mumbai sample, vector room scenes, rupee cost display, illustration toggle,
  large/side-by-side compare views and after-failure group drawings. Preserved core algorithms. Revised two
  illustrative costs to guarantee a Kruskal rejection before completion; locked the exact trace and fault
  outcome in tests. These changes have not been committed, pushed or deployed.
- 2026-10-20 — Verified the MPSTME sample in the local browser: step 5 rejects LIB-ROB; cutting RES-ROB
  keeps the full graph connected and splits the MST into the expected two illustrated groups. Full suite:
  337 passed; focused Prim completion check confirms currency display. Existing CSV export/size-label
  audit issues remain separate pending fixes.

- 2026-10-19 — First end-to-end version: core, services, app, tests, docs (PR #1, merged to `main`, CI green).
- 2026-10-19 — Working agreement: Claude does not wait for approval on routine work; it opens a PR, waits for green CI, and merges it, then records the change here. Deploying to Streamlit Cloud needs a team member's own account, so that stays with Arjun.
- 2026-10-19 — Added `REMAINING_WORK.md` listing what is left, with owners.
