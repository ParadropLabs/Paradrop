from paradrop.lib.utils import parsing


def test_str_to_numeric():
    result = parsing.str_to_numeric("42")
    assert isinstance(result, int)
    assert result == 42

    result = parsing.str_to_numeric("3.14")
    assert isinstance(result, float)
    assert int(result) == 3
