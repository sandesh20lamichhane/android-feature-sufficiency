from afs.checkpoint import ResumableLoop


def test_resumes_after_crash(tmp_path):
    calls = []

    def flaky(i):
        calls.append(i)
        if i == 7 and len(calls) < 10:
            raise RuntimeError("colab disconnect")
        return {"value": i * 2}

    loop = ResumableLoop(tmp_path, id_field="item_id", shard_size=3)
    try:
        loop.run(range(10), flaky, key=int, progress=False)
    except RuntimeError:
        pass

    done_first = loop.completed_ids()
    assert len(done_first) > 0  # partial progress persisted

    loop2 = ResumableLoop(tmp_path, id_field="item_id", shard_size=3)
    df = loop2.run(range(10), lambda i: {"value": i * 2}, key=int, progress=False)
    assert len(df) == 10
    assert set(df["item_id"]) == set(range(10))


def test_no_duplicate_work(tmp_path):
    seen = []
    loop = ResumableLoop(tmp_path, shard_size=2)
    loop.run(range(6), lambda i: (seen.append(i), {"v": i})[1], key=int, progress=False)
    loop2 = ResumableLoop(tmp_path, shard_size=2)
    loop2.run(range(6), lambda i: (seen.append(i), {"v": i})[1], key=int, progress=False)
    assert len(seen) == 6  # second pass did nothing
