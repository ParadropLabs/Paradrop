from mock import MagicMock
from nose.tools import assert_raises

from paradrop.backend.pdfcd import apibridge


def test_BridgeRequest():
    """
    Test backend.pdfcd.apibridge.BridgeRequest
    """
    request = apibridge.BridgeRequest()
    assert request.write("TEST") is None
    assert request.finish() is None


def test_BridgePackage():
    """
    Test backend.pdfcd.apibridge.BridgePackage
    """
    package = apibridge.BridgePackage()
    assert package.request is not None


def test_UpdateCallback():
    """
    Test backend.pdfcd.apibridge.UpdateCallback
    """
    d = MagicMock()
    callback = apibridge.UpdateCallback(d)

    update = MagicMock()
    update.result = "RESULT"

    callback(update)
    d.callback.assert_called_once_with("RESULT")


def test_APIBridge():
    """
    Test backend.pdfcd.apibridge.APIBridge
    """
    configurer = MagicMock()

    bridge = apibridge.APIBridge()
    assert_raises(Exception, bridge.startChute, name="NoConfigurerSet")

    bridge.setConfigurer(configurer)

    assert bridge.createChute({}) is not None
    assert bridge.deleteChute(name="foo") is not None
    assert bridge.startChute(name="foo") is not None
    assert bridge.stopChute(name="foo") is not None

    assert configurer.updateList.called
