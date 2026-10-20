# Streamlit Community Cloud deployment

Status: local preparation complete; no cloud app or public URL verified yet.
Local release checks: 354 tests passed, `pip check` reports no broken requirements,
and `git diff --check` passes. Cloud deployment and public verification are pending.

## Stack and files

- Python 3.12, Streamlit, NetworkX, Matplotlib and pandas.
- `app.py` is the entrypoint. No Node.js build, database or API keys are required.
- `requirements.txt` pins the four direct runtime dependencies to versions tested locally.
- `requirements-dev.txt` adds pytest for local checks and GitHub Actions.
- `.streamlit/config.toml` supplies the theme and disables usage telemetry.
- Include `core/`, `services/`, `viz/`, `ui/` and `data/` with the entrypoint.
- Generated `output/`, `.venv/` and Streamlit secrets are excluded from Git.

## Release gate

The user authorized release publication on 20 October 2026: preserve the old remote version,
review and test the current files, publish the necessary changes, tag the new version,
then deploy to Streamlit Cloud. The baseline `v1.0.0` preserves commit
`327db1920515bc9a7affa81e045783c916fe495e`. The new release is `v1.1.0` after CI passes.

Before publishing, run:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
git diff --check
```

The local checks use Windows/Python 3.12. A successful cloud build is still required
to verify the Linux deployment environment; local tests do not establish that.

## Cloud settings

Open https://share.streamlit.io/ and sign in with an account that can access the repository.
Use Create app, then the option to deploy an existing app from GitHub:

| Field | Value |
|---|---|
| Repository | `Saiyammiglani/Discrete-Mathematics-project` |
| Branch | The approved release branch containing the latest changes; use `main` after merge |
| Main file path | `app.py` |
| Python version, Advanced settings | `3.12` |
| Secrets | None required |
| App URL | Choose an available name in the deployment form |

Wait for the build to finish and inspect its logs. Do not record a guessed URL as deployed.
Account sign-in, permissions or consent may require the account owner.

## Verify the public app

1. Open the assigned URL in a fresh browser session.
2. Check MPSTME loads with six rooms, nine proposed cables and costs of ₹38,000 / ₹16,000.
3. Check there is no CSV upload, Hub column, theory notes or Reference checks section.
4. At Kruskal step 5, check four selected cables and one rejection; LIB–ROB is absent
   unless Show rejected cables is enabled. Step 6 completes five selected cables.
5. Check Prim from LIB completes in five additions with the same ₹16,000 total.
6. Cut ROB–RES: the full design remains connected; the tree splits into two groups.
7. Check single points of failure: full design 0 bridges / 0 cut vertices; tree 5 / 3.
8. Check both illustration settings, the office sample, connection editing and CSV/PNG downloads.
9. Record the actual URL and deployed commit in README and the remaining-work checklist.

Keep the local app as the presentation backup:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Rollback

If the public checks fail, keep using the local copy. Revert the release through a reviewed
Git commit or point the deployment to a known-good branch, then verify the public app again.

Official instructions: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
