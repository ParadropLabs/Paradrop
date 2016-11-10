from mock import patch, MagicMock

from paradrop.lib import portal


@patch('paradrop.lib.portal.reactor')
@patch('paradrop.lib.portal.resource_filename')
def test_startPortal(resource_filename, reactor):
    resource_filename.return_value = "/tmp/paradrop"
    portal.startPortal()
    assert reactor.listenTCP.called
