from mock import MagicMock


def test_getIP():
    """
    Test backend.pdfcd.apiutils.getIP
    """
    from paradrop.backend.pdfcd.apiutils import getIP

    request = MagicMock()

    request.getClientIP.return_value = "192.168.1.1"
    request.received_headers.get.return_value = None

    assert getIP(request) == "192.168.1.1"

    request.received_headers.get.return_value = "192.168.2.1"

    assert getIP(request) == "192.168.2.1"
