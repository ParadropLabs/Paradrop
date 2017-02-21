from paradrop.core.container.dockerfile import Dockerfile


def test_getString():
    config = {
        "use": "python2",
        "command": "python"
    }
    dockerfile = Dockerfile(config)
    result = dockerfile.getString()
    assert "FROM" in result
    assert "CMD" in result


def test_isValid():
    # Missing required fields.
    config = {}
    dockerfile = Dockerfile(config)
    valid, reason = dockerfile.isValid()
    assert valid is False
    assert reason is not None

    # Command is not a string or list.
    config['use'] = 'python2'
    config['command'] = 42
    dockerfile = Dockerfile(config)
    valid, reason = dockerfile.isValid()
    assert valid is False
    assert reason is not None

    # Valid
    config['command'] = "python"
    dockerfile = Dockerfile(config)
    valid, reason = dockerfile.isValid()
    assert valid is True
    assert reason is None

    # Packages is not a list.
    config['packages'] = 42
    dockerfile = Dockerfile(config)
    valid, reason = dockerfile.isValid()
    assert valid is False
    assert reason is not None

    # Packages contains a weird value.
    config['packages'] = ["a\nb"]
    dockerfile = Dockerfile(config)
    valid, reason = dockerfile.isValid()
    assert valid is False
    assert reason is not None

    # Valid
    config['packages'] = ["a", "ab", "abc"]
    dockerfile = Dockerfile(config)
    valid, reason = dockerfile.isValid()
    assert valid is True
    assert reason is None
