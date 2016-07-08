from mock import MagicMock
from nose.tools import assert_raises

from paradrop.backend.pdfcd import apiinternal


def test_RouterSession():
    """
    Test backend.pdfcd.apiinternal.RouterSession
    """
    config = MagicMock()
    config.extra = 'pd.test'
    session = apiinternal.RouterSession(config=config)

    configurer = MagicMock()
    session.bridge.setConfigurer(configurer)

    pdid = "pd.test"
    assert session.createChute(pdid, {}) is not None
    assert session.deleteChute(pdid, name="foo") is not None
    assert session.startChute(pdid, name="foo") is not None
    assert session.stopChute(pdid, name="foo") is not None
