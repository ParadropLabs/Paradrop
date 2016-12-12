from mock import patch, MagicMock

from paradrop.backend import portal


@patch('paradrop.backend.portal.reactor')
@patch('paradrop.backend.portal.resource_filename')
def test_startPortal(resource_filename, reactor):
    resource_filename.return_value = "/tmp/paradrop"
    portal.startPortal()
    assert reactor.listenTCP.called
