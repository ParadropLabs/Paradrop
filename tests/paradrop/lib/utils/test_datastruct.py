from paradrop.lib.utils import datastruct

def test_getValue():
    data = {"a": [1, 2, 3]}
    assert datastruct.getValue(data, "a.1") == 2
    assert datastruct.getValue(data, "a.3") is None
    assert datastruct.getValue(data, "a.1.b") is None
