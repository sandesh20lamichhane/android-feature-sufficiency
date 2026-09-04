# Start here

Three steps. Nothing else to apply, patch, or copy.

## 1. Push this repo

This is the complete, corrected repo. Replace whatever is currently on GitHub:

```bash
cd android-feature-sufficiency          # your existing clone
rm -rf configs docs environment notebooks paper scripts src tests \
       pyproject.toml README.md LICENSE CITATION.cff .gitignore .gitattributes
# copy everything from this zip into the folder, then:
git add -A
git commit -m "Complete scaffold: pipeline, checkpointing, evasion analysis"
git push
```

Check the Actions tab goes green. CI runs `ruff`, `pytest`, and a full smoke
experiment on synthetic data — no real dataset needed.

## 2. Create the Drive folders

Open `notebooks/00_setup_drive.ipynb` in Colab and run all cells. It creates
`MyDrive/afs-data` with the exact directory names the code expects, plus a
README in every folder.

Safe to re-run. Never overwrites data.

## 3. Verify the pipeline

Open `notebooks/00_setup_verify.ipynb` in Colab and run all cells. It clones,
installs, runs the tests, simulates a Colab disconnect to prove resume works,
and executes a full experiment on synthetic data.

---

## Then: the actual blocking task

**Request the AndroZoo API key today.** Academic email required, approval takes
days to weeks. It gates both the temporal axis and the Drebin benign corpus, so
nothing on the critical path can start without it.

While waiting, fill in `docs/decisions/0002-drebin-benign-corpus.md`. Drebin
ships malware only; the benign corpus you pick silently determines your result
and is the first thing a reviewer will attack.

## Notebook order

| Notebook | When |
|---|---|
| `00_setup_drive` | Once, before anything else |
| `00_setup_verify` | Every new Colab session |
| `01_data_audit` | After datasets are downloaded |
| `02_reproduce_baseline` | Week 1 gate — does the known result reproduce? |
| `03_low_fpr` | Week 2 gate — does the gap survive a real operating point? |
| `04_evasion_cost` | Weeks 3–5 — the contribution |
| `99_figures` | Paper figures from committed metrics |
