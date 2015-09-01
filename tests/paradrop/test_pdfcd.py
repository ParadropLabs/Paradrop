from mock import MagicMock, Mock, patch

from .pdmock import call, do_nothing, make_dummy


def test_server_complete():
    """
    Test ParadropAPIServer complete method
    """
    from paradrop.backend.pdfcd.server import ParadropAPIServer

    reactor = MagicMock()
    reactor.callFromThread = call

    server = ParadropAPIServer(reactor)
    update = MagicMock()

    server.complete(update)

    # Test the private _complete method.
    update = MagicMock()
    update.result = {}
    server._complete(update)
    assert update.pkg.request.write.called
    assert update.pkg.request.finish.called

    update.pkg.request.write.side_effect = Exception("Boom!")
    server._complete(update)


def test_server_preprocess():
    """
    Test ParadropAPIServer preprocess method
    """
    from paradrop.backend.pdfcd.server import ParadropAPIServer

    reactor = MagicMock()

    server = ParadropAPIServer(reactor)
    server.WHITELIST_IP = ["192.168.1.0/24"]
    server.failprocess = do_nothing

    request = MagicMock()

    assert server.preprocess(request, False, None) is None

    failures = dict()
    checks = ("192.168.1.1", "token", "paradrop", failures)
    assert server.preprocess(request, checks, None) is None

    failures = {"paradrop": Mock(attempts=0)}
    checks = ("192.168.2.1", "token", "paradrop", failures)
    assert server.preprocess(request, checks, None) is None

    failures = {"paradrop": Mock(attempts=float("inf"))}
    checks = ("192.168.2.1", "token", "paradrop", failures)
    assert server.preprocess(request, checks, None) is not None


def test_server_postprocess():
    """
    Test ParadropAPIServer postprocess method
    """
    from paradrop.backend.pdfcd.server import ParadropAPIServer

    reactor = MagicMock()

    server = ParadropAPIServer(reactor)
    server.WHITELIST_IP = ["192.168.1.0/24"]
    server.failprocess = do_nothing

    request = MagicMock()

    server.postprocess(request, None, None, False)

    failures = dict()
    logs = (None, "192.168.1.1", None)
    server.postprocess(request, "key", failures, logs)

    failures = {"key": Mock()}
    logs = (None, "192.168.1.1", None)
    server.postprocess(request, "key", failures, logs)


def test_server_failprocess():
    """
    Test ParadropAPIServer failprocess method
    """
    from paradrop.backend.pdfcd.server import ParadropAPIServer
    from paradrop.lib.api import pdapi    

    reactor = MagicMock()

    server = ParadropAPIServer(reactor)
    server.WHITELIST_IP = ["192.168.1.0/24"]

    request = MagicMock()

    server.failprocess("192.168.1.1", request, None, None, None, pdapi.ERR_BADPARAM)
    server.failprocess("192.168.1.1", request, None, None, None, pdapi.OK)

    errorStmt = "Malformed Body: %s"
    logUsage = (None, None)
    server.failprocess("192.168.1.1", request, None, errorStmt, logUsage, pdapi.OK)

    logFailure = ("key", {})
    server.failprocess("192.168.1.1", request, logFailure, errorStmt, None, pdapi.OK)

    # This call will update an item in logFailure that was created in the
    # previous call.
    errorStmt = "Malformed Body: %s"
    server.failprocess("192.168.1.1", request, logFailure, errorStmt, None, pdapi.OK)


def test_server_get():
    """
    Test ParadropAPIServer GET_test method
    """
    from paradrop.backend.pdfcd.server import ParadropAPIServer

    reactor = MagicMock()
    server = ParadropAPIServer(reactor)
    request = MagicMock()
    server.GET_test(request)


def test_server_default():
    """
    Test ParadropAPIServer default method
    """
    from paradrop.backend.pdfcd.server import ParadropAPIServer

    reactor = MagicMock()
    server = ParadropAPIServer(reactor)

    request = MagicMock()
    request.received_headers = {'X-Real-IP': '192.168.1.1'}

    # Exercise path where preprocess returns something
    server.preprocess = make_dummy("stuff")
    server.default(request)

    # Exercise path where preprocess returns None
    server.preprocess = make_dummy(None)
    server.default(request)


def test_server_initialization():
    """
    Test pdfcd server initialization function
    """
    from paradrop.backend.pdfcd import server
    server.initializeSystem()


@patch("twisted.internet.reactor.listenTCP")
@patch("twisted.internet.reactor.run")
def test_server_setup(mockRun, mockListenTCP):
    """
    Test pdfcd server setup function
    """
    from paradrop.backend.pdfcd import server
    from paradrop.backend.pdconfd.main import ConfigService

    manager = MagicMock()
    manager.waitSystemUp = make_dummy("[]")
    ConfigService.configManager = manager

    server.setup()

    args = Mock(development=True, unittest=False)
    server.setup(args)

    args = Mock(development=False, unittest=True)
    server.setup(args)
