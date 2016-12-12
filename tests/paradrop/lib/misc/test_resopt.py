from mock import patch, MagicMock
from nose.tools import assert_raises

from paradrop.lib.misc import resopt


def is_expected(result, expected, epsilon=0.001):
    if len(result) != len(expected):
        return False
    for i in range(len(result)):
        if abs(result[i] - expected[i]) > epsilon:
            return False
    return True


def test_allocate():
    assert resopt.allocate([]) == []

    result = resopt.allocate([0.25, None, None])
    assert is_expected(result, [0.5, 0.25, 0.25])

    result = resopt.allocate([0.4, None, None])
    assert is_expected(result, [0.6, 0.2, 0.2])

    result = resopt.allocate([0.2, 0.2, 0.2])
    assert is_expected(result, [0.3333, 0.3333, 0.3333])

    result = resopt.allocate([None, None, None])
    assert is_expected(result, [0.3333, 0.3333, 0.3333])

    assert_raises(Exception, resopt.allocate, [0.5, 0.5, 0.5])
