from mock import patch, MagicMock

from paradrop.lib.misc import portal


@patch('paradrop.lib.misc.portal.reactor')
@patch('paradrop.lib.misc.portal.resource_filename')
def test_startPortal(resource_filename, reactor):
    resource_filename.return_value = "/tmp/paradrop"
    portal.startPortal()
    assert reactor.listenTCP.called
