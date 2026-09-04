import pandas as pd
from afs.checkpoint import CheckpointStore


def test_reuses_valid_checkpoint(tmp_path):
    s = CheckpointStore(tmp_path)
    cfg = {"a": 1}
    art = s.artifact("stage", cfg)
    assert not art.valid
    art.commit(lambda p: pd.DataFrame({"x": [1]}).to_parquet(p))
    assert s.artifact("stage", cfg).valid


def test_config_change_invalidates(tmp_path):
    s = CheckpointStore(tmp_path)
    s.artifact("stage", {"a": 1}).commit(
        lambda p: pd.DataFrame({"x": [1]}).to_parquet(p))
    # Different config must produce a *different file*, not a silent reuse.
    art2 = s.artifact("stage", {"a": 2})
    assert not art2.valid


def test_missing_manifest_is_stale(tmp_path):
    s = CheckpointStore(tmp_path)
    art = s.artifact("stage", {"a": 1})
    art.commit(lambda p: pd.DataFrame({"x": [1]}).to_parquet(p))
    from afs.checkpoint.manifest import Manifest
    Manifest.path_for(art.path).unlink()
    assert not s.artifact("stage", {"a": 1}).valid


def test_failed_write_leaves_no_artifact(tmp_path):
    s = CheckpointStore(tmp_path)
    art = s.artifact("stage", {"a": 1})

    def boom(p):
        raise RuntimeError("disconnect")

    try:
        art.commit(boom)
    except RuntimeError:
        pass
    assert not art.path.exists()
