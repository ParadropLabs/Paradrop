
from mock import Mock, patch

import sys


@patch("paradrop.confd.main.run_pdconfd")
@patch("paradrop.confd.main.run_thread")
@patch("paradrop.backend.server.setup")
def test_paradrop_main(setup, run_thread, run_pdconfd):
    """
    Test paradrop main function
    """
    from paradrop.main import main

    sys.argv = ["pd", "-m", "unittest"]
    main()
    assert run_thread.called
    assert setup.called


@patch("paradrop.confd.main.run_pdconfd")
@patch("paradrop.confd.main.run_thread")
@patch("paradrop.backend.server.setup")
def test_paradrop_main_config(setup, run_thread, run_pdconfd):
    """
    Test paradrop main function (--config)
    """
    from paradrop.main import main

    sys.argv = ["pd", "--config", "-munittest"]
    main()
    assert run_pdconfd.called
