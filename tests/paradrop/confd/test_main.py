
from mock import Mock, patch

import sys


@patch("twisted.internet.reactor.listenTCP")
@patch("paradrop.confd.main.run_pdconfd")
@patch("paradrop.confd.main.run_thread")
@patch("paradrop.backend.server.setup")
def test_paradrop_main(setup, run_thread, run_pdconfd, listenTCP):
    """
    Test paradrop main function
    """
    from paradrop.main import main

    sys.argv = ["pd"]
    main()
    assert run_thread.called
    assert setup.called
    assert listenTCP.called


@patch("twisted.internet.reactor.listenTCP")
@patch("paradrop.confd.main.run_pdconfd")
@patch("paradrop.confd.main.run_thread")
@patch("paradrop.backend.server.setup")
def test_paradrop_main_local(setup, run_thread, run_pdconfd, listenTCP):
    """
    Test paradrop main function (--local)
    """
    from paradrop.main import main

    sys.argv = ["pd", "--local"]
    main()
    assert listenTCP.called


@patch("paradrop.confd.main.run_pdconfd")
@patch("paradrop.confd.main.run_thread")
@patch("paradrop.backend.server.setup")
def test_paradrop_main_config(setup, run_thread, run_pdconfd):
    """
    Test paradrop main function (--config)
    """
    from paradrop.main import main

    sys.argv = ["pd", "--config"]
    main()
    assert run_pdconfd.called
