from mock import call, patch, MagicMock
from nose.tools import assert_raises

from paradrop.core.container import log_provider


@patch("paradrop.core.container.log_provider.docker.DockerClient")
def test_monitor_logs(DockerClient):
    client = MagicMock()
    DockerClient.return_value = client

    container = MagicMock()
    client.containers.get.return_value = container

    logs = [
        "0 MessageA",
        "MessageB",
        {"message": "MessageC"}
    ]
    container.logs.return_value = logs

    output = []
    queue = MagicMock()
    queue.put = output.append

    log_provider.monitor_logs("chute", queue)

    assert len(output) == 3
    assert output[0]['message'] == "MessageA"
    assert output[1]['message'] == "MessageB"
    assert output[2]['message'] == "MessageC"
