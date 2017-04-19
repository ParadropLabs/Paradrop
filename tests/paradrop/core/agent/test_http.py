from mock import patch, MagicMock

from paradrop.core.agent import http


def fake_deferred(*args, **kwargs):
    """
    Returns a fake deferred object whose addCallback method immediately fires
    with the given arguments.
    """
    def call_callback(cb):
        cb(*args, **kwargs)
    deferred = MagicMock()
    deferred.addCallback.side_effect = call_callback
    return deferred


@patch("paradrop.lib.utils.http.nexus")
def test_PDServerRequest_patch(nexus):
    driver = MagicMock()
    driver_factory = MagicMock()
    driver_factory.return_value = driver

    http.PDServerRequest.token = "token"
    request = http.PDServerRequest("test", driver=driver_factory)
    assert request.url.endswith('/test')

    op = {'op': 'replace', 'path': '/completed', 'value': True}
    request.patch(op)
    driver.setHeader.assert_called_with('Authorization', 'Bearer token')
    driver.request.assert_called()


@patch("paradrop.lib.utils.http.nexus")
def test_PDServerRequest_put(nexus):
    driver = MagicMock()
    driver_factory = MagicMock()
    driver_factory.return_value = driver

    http.PDServerRequest.token = "token"
    request = http.PDServerRequest("test", driver=driver_factory)
    assert request.url.endswith('/test')

    request.put(var=42)
    driver.setHeader.assert_called_with('Authorization', 'Bearer token')
    driver.request.assert_called()


@patch("paradrop.lib.utils.http.nexus")
def test_PDServerRequest_receiveResponse(nexus):
    nexus.core.info.pdid = "pdid"
    nexus.core.getKey.return_value = "apitoken"

    driver = MagicMock()
    driver_factory = MagicMock()
    driver_factory.return_value = driver

    authResponse = MagicMock()
    driver.request.return_value = fake_deferred(authResponse)

    http.PDServerRequest.token = "token"
    request = http.PDServerRequest("test", driver=driver_factory)
    assert request.url.endswith('/test')
    request.method = 'GET'

    # Fake a 401 (Not authorized) response.
    response = MagicMock()
    response.code = 401

    # Fake a failed response from the auth endpoint.
    authResponse.success = False
    request.receiveResponse(response)

    # Fake a successful response from the auth endpoint.
    authResponse.success = True
    authResponse.data.get.return_value = "token2"

    # It should try to reissue the original request with the new token.
    request.receiveResponse(response)
    driver.setHeader.assert_called_with('Authorization', 'Bearer token2')
    driver.request.assert_called()
