from paradrop.lib.utils import uci


def test_stringifyOptionValue():
    assert uci.stringifyOptionValue(True) == "1"
    assert uci.stringifyOptionValue(False) == "0"
    assert uci.stringifyOptionValue(42) == "42"
    assert uci.stringifyOptionValue("test") == "test"


def test_getLineParts():
    # Test simple case.
    line = "option key 'value'"
    parts = uci.getLineParts(line)
    assert parts[0] == "option"
    assert parts[1] == "key"
    assert parts[2] == "value"

    # Test spaces inside quotation marks.
    line = "config ssid 'Free WiFi' # <- Space inside quotation marks."
    parts = uci.getLineParts(line)
    assert parts[0] == "config"
    assert parts[1] == "ssid"
    assert parts[2] == "Free WiFi"

    # Test embedded quotation marks.
    line = "option key '\"value\"'"
    parts = uci.getLineParts(line)
    assert parts[0] == "option"
    assert parts[1] == "key"
    assert parts[2] == "\"value\""

    # Make sure the line processor handles inner single quotation marks.
    line = "    option classes 'Priority Express Normal Bulk'"
    parts = uci.getLineParts(line)
    assert parts[2] == "Priority Express Normal Bulk"

    # Make sure the line processor handles inner double quotation marks.
    line = '    option classes "Priority Express Normal Bulk"'
    parts = uci.getLineParts(line)
    assert parts[2] == "Priority Express Normal Bulk"

    # Test a very challenging line with odd spacing.
    line = "    option  key 'correct horse   battery staple' #comment "
    parts = uci.getLineParts(line)
    assert parts[0] == "option"
    assert parts[1] == "key"
    assert parts[2] == "correct horse   battery staple"
    assert parts[3] == "#comment"
