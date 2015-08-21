
from mock import Mock, patch

import sys

@patch("paradrop.backend.pdconfd.main.run_pdconfd")
@patch("paradrop.backend.pdconfd.main.run_thread")
@patch("paradrop.backend.pdfcd.server.setup")
def test_paradrop_main(setup, run_thread, run_pdconfd):
    """
    Test paradrop main function
    """
    from paradrop.main import main

    args = {
        'mode': 'production'
    }

    sys.argv = ["pd"]
    main()
    assert run_thread.called
    assert setup.called

    sys.argv.append("--local")
    main()

    sys.argv.append("--config")
    main()
    assert run_pdconfd.called
