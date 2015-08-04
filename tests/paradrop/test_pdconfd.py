from paradrop.backend.pdconfd.config.command import Command

def test_command():
    """
    Test command execution

    The true and false commands should reliably succeed and fail in most Linux
    environments.
    """
    cmd = ["true"]
    command = Command(0, cmd)
    command.execute()
    assert command.success()

    cmd = ["false"]
    command = Command(0, cmd)
    command.execute()
    assert not command.success()
