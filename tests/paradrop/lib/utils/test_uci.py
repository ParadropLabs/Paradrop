from paradrop.lib.utils import uci


def test_stringifyOptionValue():
    assert uci.stringifyOptionValue(True) == "1"
    assert uci.stringifyOptionValue(False) == "0"
    assert uci.stringifyOptionValue(42) == "42"
    assert uci.stringifyOptionValue("test") == "test"
