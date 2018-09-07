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

    assert isinstance(mychute.get_environment(), dict)


def test_Chute_create_specification():
    mychute = chute.Chute(name="Test")

    spec = mychute.create_specification()
    assert spec['name'] == mychute.name
    assert 'environment' in spec
    assert 'services' in spec
    assert 'web' in spec
