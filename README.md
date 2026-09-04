# Feature-Set Sufficiency in Android Malware Detection

**Research question.** Permissions-only baselines land within a point or two of
full feature sets on standard benchmarks. That result is real and widely
replicated. This project asks the question that follows: *does the gap stay
closed where it matters?*

Three axes, deliberately separated:

| Axis | Question | Expected |
|---|---|---|
| Aggregate accuracy, random split | Does the known result reproduce? | Gap < 2pp |
| TPR at 0.1% / 0.01% FPR | Does the gap survive the operating point a real scanner uses? | Gap opens |
| Evasion cost | How much attacker effort does each feature set demand? | Gap opens sharply |

The headline claim is the third: **two models with statistically
indistinguishable clean accuracy can require wildly different attacker effort
to evade.** Adding a manifest permission is free. Restructuring API call
sequences is not. Nobody selects feature sets on that basis.

## Status

- [x] Pipeline, checkpointing, metrics, evasion analysis — working on synthetic data
- [ ] Drebin loader (see `docs/decisions/0002`)
- [ ] CICMalDroid loader (`docs/decisions/0003`)
- [ ] AndroZoo access + loader (`docs/decisions/0004`) — **request the API key first, it takes days to weeks**

## Quickstart

```bash
pip install -e ".[dev]"
pytest -q
afs-run --experiment 00_smoke --data-root ~/afs-data
```

In Colab, see `environment/colab_bootstrap.md`.

## Layout

```
src/afs/          all logic lives here -- never in notebook cells
configs/          composable yaml; the resolved dict is what gets hashed
notebooks/        thin drivers that import src/ and call it
docs/decisions/   one file per methodological choice (not optional)
paper/            figures and tables
```

The one structural rule: **notebooks contain no logic.** If analysis code lives
in cells, you cannot reproduce your own results in three months — and this
paper's entire selling point is methodological rigor.

## Checkpointing

Three levels, all of which matter in Colab:

**Stage-level.** Artifacts are keyed on `hash(stage, resolved config, input
hashes)`. Change a config value and you get a *different file*, not a silent
reuse of the old one. Every artifact carries a `.manifest.json` sidecar
recording run id, git SHA, full config, library versions, seed, timestamp.

**Within-run.** `ResumableLoop` appends sharded parquet as items complete and
skips completed ids on restart. A disconnect costs one item, not six hours.

**Model-level.** Fitted estimators via joblib, so you never refit just to
regenerate predictions.

Run ids are `YYYYMMDD-<git sha>-<config hash>` and are never reused. New config
means new run, always. Superseded runs move to `_archive/`, never deleted —
two months from now you will want the old numbers.

## Data and records

Two things with opposite requirements, kept separate:

- **Artifacts** (matrices, models, shards) — large, regenerable. Drive only, never git.
- **Records** (manifests, metrics, decision docs) — small, textual, *not* regenerable. Git is the source of truth; Drive holds a mirror.

At the end of each run, `metrics.json` and `manifest.json` are copied into the
repo and committed. A few KB each. The repo then holds the complete
experimental record — what ran, when, on which commit, with which config, and
what came out — while the multi-GB matrices stay in Drive.

`raw/` is write-once. Every stage reads from it and writes elsewhere.
Corrupting raw data mid-project is the one unrecoverable failure.

## Provenance warning

Drebin ships malware only. Whatever benign corpus you choose silently
determines the result, and it is the single most attackable part of this
design. If your benign apps are Play Store and your malware is
VirusShare-flagged, manifest features may encode packaging conventions and
ad-SDK boilerplate as much as malicious intent. State the choice explicitly;
`Dataset.provenance` carries it through to the reported summary.

## License

MIT. See `LICENSE`.
