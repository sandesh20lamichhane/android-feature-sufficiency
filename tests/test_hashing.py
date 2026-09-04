from afs.utils.hashing import hash_obj


def test_key_order_irrelevant():
    assert hash_obj({"a": 1, "b": 2}) == hash_obj({"b": 2, "a": 1})


def test_nested_stable():
    a = {"m": {"p": [1, 2, {"z": 0.1}]}}
    b = {"m": {"p": [1, 2, {"z": 0.1}]}}
    assert hash_obj(a) == hash_obj(b)


def test_value_change_detected():
    assert hash_obj({"C": 1.0}) != hash_obj({"C": 1.1})
