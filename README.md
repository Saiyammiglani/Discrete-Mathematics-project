# NetGraph Analyzer

**Graph Theory for Network Vulnerability and Secure Routing Analysis** — a Discrete Mathematics project
(Graphs and Trees unit) by Tanish Parikh, Saiyam Miglani and Arjun Shetty.

NetGraph Analyzer turns a computer network into a weighted graph, finds the cheapest way to connect every
device with **Kruskal's** and **Prim's** algorithms (step by step), and shows where the network is fragile
(**cut vertices** and **bridges**). Free edition: Python, Streamlit, no database, ₹0 to build and host.

On the built-in 8-device office network the MST cuts cost from **59 to 24 (59% lower)**, but every link of
the tree becomes a single point of failure (1 bridge in the full network, 7 in the MST).

## Run it

```bash
python -m venv .venv && source .venv/bin/activate     # optional
pip install -r requirements.txt
streamlit run app.py                                   # opens http://localhost:8501
pytest -q                                              # 333 tests
```

Python 3.12 or newer. Nothing is stored; uploaded files stay in your session.

## Using the app

1. The sidebar loads a sample network at once (office with 8 devices, campus with 12), or upload a CSV
   `source,target,weight` (a template is offered when a file is rejected). Use *Edit links* to add, remove or
   re-weight links.
2. Four tabs analyse the same graph:
   | Tab | What it shows |
   |---|---|
   | Graph properties | Drawing, adjacency list and matrix, degrees and hub, connectivity, path finder, cycles |
   | Kruskal and Prim | Pick an algorithm, step with Previous/Next, see why each edge is accepted or rejected |
   | Compare | Full graph vs MST, cost saving, both algorithms side by side, networkx check, CSV and PNG downloads |
   | Vulnerability | Bridges and cut vertices (full network and MST), remove a device or link and re-check |

CSV rules: names 1–30 characters; weight > 0; self-loops, bad weights and empty names are rejected with the
row number (the header is row 1); a duplicate pair keeps the cheaper cost; a disconnected network gives a
minimum spanning forest with a warning; ties break by edge name; more than 200 devices skips drawings.

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
services/theory.py      Saiyam   theory notes
viz/draw.py             Arjun    matplotlib drawings
data/                            office_8.csv, campus_12.csv
tests/                  Saiyam   unit, known-answer, 300 random graphs vs networkx, app smoke tests
.github/workflows/ci.yml Arjun   runs pytest on every push
```

Each module has a second reviewer: Tanish's modules are read by Saiyam, Saiyam's by Arjun, Arjun's by Tanish.
See [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) for status, decisions and the full project context.

## Deploy (free)

Push to GitHub, then create the app on [Streamlit Community Cloud](https://share.streamlit.io) pointing at
`app.py` on `main`. Free apps sleep after 12 hours: open the link 5 minutes before presenting and keep the
local copy (`streamlit run app.py`) as the backup.

## Licence

MIT (see `LICENSE`). Dependencies are open source: Streamlit (Apache 2.0), networkx, pandas (BSD),
matplotlib, pytest (MIT).
