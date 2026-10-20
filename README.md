# NetGraph Analyzer

**Graph Theory for Network Vulnerability and Secure Routing Analysis** — a Discrete Mathematics project
(Graphs and Trees unit) by Tanish Parikh, Saiyam Miglani and Arjun Shetty.

NetGraph Analyzer turns a computer network into a weighted graph, finds the cheapest way to connect every
device with **Kruskal's** and **Prim's** algorithms (step by step), and shows where the network is fragile
(**cut vertices** and **bridges**). Free edition: Python, Streamlit, no database, ₹0 to build and host.

On the built-in 8-device office network the MST cuts cost from **59 to 24 (59% lower)**, but every link of
the tree becomes a single point of failure (1 bridge in the full network, 7 in the MST).

The default demo is now **MPSTME Mumbai (6 facilities)**: illustrated rooms contain bookshelves, VR
headsets, a robot arm, telecom equipment, a 3-D printer and research workstations. Every room contains
one switch, which is the graph vertex; furniture is decorative. Facility names follow MPSTME's
[published infrastructure](https://engineering.nmims.edu/academics/infrastructure/). The rooms, routes,
equipment illustrations and installation estimates are a case study, not the real campus floor plan or network.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate     # optional
pip install -r requirements-dev.txt
streamlit run app.py                                   # opens http://localhost:8501
pytest -q
```

Python 3.12 is the tested deployment target. Connection edits stay in your session.

## Using the app

1. The sidebar loads MPSTME Mumbai at once (6 facilities); the office sample (8 devices)
   is also available. Add, remove or re-weight links
   in the full-width *Edit connections* table on the Network tab.
2. Four tabs analyse the same graph:
   | Tab | What it shows |
   |---|---|
   | Network | Drawing, summary, connection editor, graph data and path finder |
   | Algorithms | Kruskal/Prim step-through, acceptance/rejection reason and step log |
   | Costs | Costs, selectable drawings, CSV/PNG downloads and algorithm comparison |
   | Failures | Switch/cable outage, connected groups and expandable single points of failure |

Connection editor rules: names 1–30 characters; weight > 0; self-loops, bad weights and empty names are rejected with the
row number; a duplicate pair keeps the cheaper cost; a disconnected network gives a
minimum spanning forest with a warning; ties break by edge name; more than 200 devices skips drawings.

## MPSTME presentation walkthrough

1. Start with the built-in MPSTME sample to use its fixed schematic positions and
   illustrated facilities. Toggle *Illustrated facilities* off to show the underlying graph.
2. In *Costs*, show nine proposed connections costing **₹38,000**, versus five MST connections
   costing **₹16,000** (saving ₹22,000, approximately 58%). Weights in the CSV are in ₹ thousand.
   Choose the minimum-cost design, all connections, or a side-by-side drawing.
3. Choose Kruskal. The deterministic trace is ARVR-ROB (2), ARVR-TELE (3), PRINT-RES (3), ARVR-LIB (4),
   **reject LIB-ROB (4), cycle LIB-ARVR-ROB-LIB**, accept RES-ROB (4). The final tree has five edges.
   Name-based tie breaking determines this demonstration, rather than a promise that every MST uses
   the same links. Prim from LIB gives the same edge set and total for this sample.
4. In *Failures*, choose *Cable*. ROB-RES is preselected. The full network stays connected
   (RES has alternative routes); the MST splits into ARVR/LIB/ROB/TELE and PRINT/RES. The after-failure
   drawing marks the cut cable and colors the separate groups. Switch failures retain the failed room
   with an offline switch, rather than suggesting the room disappeared.
5. Change connections in the editor to recompute the results. The walkthrough is a known example,
   not a hard-coded result. Algorithm diagrams show selected cables by default; rejected cables are optional.

The Library-Robotics estimate is ₹4,000 and Telecom-3-D Printing is ₹7,000. These revised illustrative
estimates deliberately put a rejected edge before the final accepted edge, while preserving totals 38/16.

## Code layout and who owns what

The core never imports Streamlit or matplotlib; calls only go downward (app → services → core).

```
app.py                  Arjun    Streamlit entry: sidebar, four tabs, step-through
core/graph.py           Tanish   Edge, Graph, adjacency list + matrix
core/properties.py      Tanish   degree, BFS components, path, cycles
core/vulnerability.py   Tanish   Tarjan cut vertices/bridges (iterative), failure_test
core/kruskal.py         Saiyam   UnionFind, kruskal(), Step/MSTResult
core/prim.py            Arjun    prim() with min-heap and step log
services/input.py       Tanish   samples, CSV validation, error messages
services/export.py      Tanish   MST CSV, PNG
services/analysis.py    Saiyam   analyze(), comparison table, networkx cross-check
viz/draw.py             Arjun    matplotlib drawings
data/                            mpstme_mumbai.csv, office_8.csv
tests/                  Saiyam   unit, known-answer, 300 random graphs vs networkx, app smoke tests
.github/workflows/ci.yml Arjun   runs pytest on every push
```

Each module has a second reviewer: Tanish's modules are read by Saiyam, Saiyam's by Arjun, Arjun's by Tanish.
See [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) for status, decisions and the full project context.

## Deploy (free)

Deployment preparation uses **Streamlit Community Cloud**, Python **3.12**, and pinned runtime
dependencies. No public deployment has been verified yet. See [DEPLOYMENT.md](DEPLOYMENT.md) for
the exact repository settings and public-app checks. Keep the local app as a presentation backup.

## Licence

MIT (see `LICENSE`). Dependencies are open source: Streamlit (Apache 2.0), networkx, pandas (BSD),
matplotlib, pytest (MIT).
