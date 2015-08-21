def test_chute():
    """
    Test the Chute class
    """
    from paradrop.lib import chute

    desc = {
        'name': 'Test',
        'state': 'running'
    }
    mychute = chute.Chute(desc)

    # Basic tests for the new object
    assert mychute.name == "Test"
    assert "Chute" in repr(mychute)
    assert "Chute" in str(mychute)

    assert mychute.isValid()

    mychute.setCache("key", "value")
    assert mychute.getCache("key") == "value"
    mychute.delCache("key")
    assert mychute.getCache("key") is None

    mychute.setCache("key", "value")
    dump = mychute.dumpCache()
    assert dump == "key:value"

    # Appending to a string-valued entry should fail
    assert mychute.appendCache("key", "value2") is None

    # Appending to a new list should work.
    assert mychute.appendCache("list", "value1") is True
    assert mychute.appendCache("list", "value2") is True
    assert len(mychute.getCache("list")) == 2
