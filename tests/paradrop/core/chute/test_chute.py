from paradrop.core.chute import chute

def test_chute():
    """
    Test the Chute class
    """
    desc = {
        'name': 'Test',
        'state': 'running'
    }
    mychute = chute.Chute(name="Test")

    # Basic tests for the new object
    assert mychute.name == "Test"
    assert "Chute" in repr(mychute)
    assert "Chute" in str(mychute)

    assert mychute.isValid()

    mychute.setCache("key", "value")
    assert mychute.getCache("key") == "value"
