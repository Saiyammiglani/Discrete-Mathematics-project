# Remaining work

What is left after the first version of NetGraph Analyzer (merged to `main`, CI green, 333 tests).
Owners follow the module split in `README.md`. Keep this file and `PROJECT_CONTEXT.md` in sync.

## Needs a team member (cannot be done from code)

| # | Task | Owner | Notes |
|---|---|---|---|
| 1 | Deploy to Streamlit Community Cloud | Arjun | Sign in at share.streamlit.io with GitHub, pick this repo, branch `main`, file `app.py`. Free apps sleep after 12 h: open the link 5 min before presenting. |
| 2 | Put the public app link in `README.md` and pin versions in `requirements.txt` | Arjun | Pin on the day of the first deploy (`pip freeze` for streamlit, networkx, matplotlib, pandas, pytest). |
| 3 | Manual check in a real browser | All | The app was tested headlessly only. Follow the checklist in `PROJECT_CONTEXT.md` §7 on laptop and phone; check that drawings look right and the step slider behaves. |
| 4 | Report (PDF) | Saiyam compiles, all write | Sections: modelling, properties, theory (cut and cycle property proofs), Kruskal, Prim, vulnerability, results, system design, complexity. Worked example and figures can come from the app's PNG export. |
| 5 | Slides | All | Same sections as the report, plus a demo script. |
| 6 | 2-minute backup screen recording of the demo | Arjun | Backup in case hosting is down. |
| 7 | Rehearsal (10 minutes, live demo plus backup) | All | |
| 8 | Final submission: report PDF, GitHub link, app link | Saiyam | |
| 9 | Second-reader review of each module | Tanish ↔ Saiyam ↔ Arjun | Rotation is in `README.md`. |

## Optional improvements (not required by the PRD)

- Show the "add back the cheapest links that close cycles" idea from the proposal (e.g. CR–SB) as a suggestion in the Vulnerability tab.
- Add a simple screenshot or GIF of the app to the README.
- Add a `.streamlit/config.toml` for a fixed theme.

## Known limitations

- Dates in the source documents (presentation 15 Oct 2026, submission 16 Oct) were already past when the code was written; re-check the real deadlines.
- Adjacency matrix and drawings are skipped above 200 devices, as the PRD specifies.
- The Streamlit interface itself has no browser-level automated tests, only headless `AppTest` smoke tests.

## Done

Everything in the PRD's functional requirements FR-01 to FR-16, the CI workflow, the test suite, README and `PROJECT_CONTEXT.md`. See `PROJECT_CONTEXT.md` §2 and §4.
