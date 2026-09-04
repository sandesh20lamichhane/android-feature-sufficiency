# Colab bootstrap

Paste into the first cell of any notebook. Everything else imports from `afs`.

```python
# 1. Mount Drive (artifacts + records live here, never in the repo)
from google.colab import drive
drive.mount('/content/drive')

# 2. Clone or pull. Token from Colab Secrets -- never paste it in a cell.
from google.colab import userdata
import os, subprocess
TOKEN = userdata.get('GITHUB_TOKEN')      # fine-grained PAT, scoped to this repo
USER, REPO = '<your-github-user>', 'android-feature-sufficiency'
if not os.path.exists(f'/content/{REPO}'):
    subprocess.run(['git','clone',f'https://{TOKEN}@github.com/{USER}/{REPO}.git'],
                   cwd='/content', check=True)
else:
    subprocess.run(['git','pull'], cwd=f'/content/{REPO}', check=True)
%cd /content/{REPO}

# 3. Install pinned deps + package in editable mode
!pip install -q -r environment/requirements.txt
!pip install -q -e .

# 4. Point at Drive for durable storage, /content for hot scratch
os.environ['AFS_DATA_ROOT'] = '/content/drive/MyDrive/afs-data'
os.environ['AFS_SCRATCH']   = '/content/afs-scratch'

from afs.paths import Paths
paths = Paths.create()
print('data root:', paths.data_root)
```

## Why scratch matters

Drive I/O collapses under many small files and enforces a file-count quota that
per-sample outputs will hit fast. `ResumableLoop` writes sharded parquet (a few
hundred rows per file) to local `/content` and syncs to Drive every few shards.
Local disk is far faster and you only lose the last interval on a crash.

## Things that will bite you

**Drive has no atomic write.** A disconnect mid-write leaves a truncated parquet
that reads as valid until it doesn't. Everything in `afs.checkpoint.atomic`
writes to a temp name then renames. Never write to Drive directly.

**One session per run_id.** Two Colab sessions writing the same run directory
will produce `file (1).parquet` collisions and corruption. If you need
parallelism, use different run ids.

**Background execution still caps at 24h** on Pro+. Resumability has to be a
property of the design, not a recovery plan — which is why every long loop goes
through `ResumableLoop`.

**Drive sync lag is real.** A file written from Colab may not be visible in the
Drive web UI for a while. Debug from the notebook, not the UI.

**Check quota before long runs.** Feature matrices across three datasets and
four feature sets, plus per-sample evasion outputs, run to tens of GB, and Drive
quota is shared with everything else on the account.

**Commit before any run you intend to cite.** The pipeline warns on a dirty
working tree, because the recorded git SHA then doesn't describe the code that
produced the result.

## After a run

```python
!cp {paths.run_dir(run_id)}/metrics.json paper/tables/
!git add -A && git commit -m "run {run_id}" && git push
```

Records go to git. Artifacts stay in Drive.
