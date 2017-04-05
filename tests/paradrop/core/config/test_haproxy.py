import StringIO

from mock import MagicMock, patch
from nose.tools import assert_raises

from paradrop.core.config import haproxy


@patch("paradrop.core.config.haproxy.ChuteContainer")
@patch("paradrop.core.config.haproxy.ChuteStorage.getChuteList")
def test_generateConfigSections(getChuteList, ChuteContainer):
    chute1 = MagicMock()
    chute1.name = "chute1"

    getChuteList.return_value = [chute1]

    container = MagicMock()
    container.isRunning.return_value = True
    ChuteContainer.return_value = container

    sections = haproxy.generateConfigSections()
    assert len(sections) > 0

    # Make sure one of the sections is for chute1.
    assert any(chute1.name in v['header'] for v in sections)


def test_writeConfigFile():
    output = StringIO.StringIO()
    haproxy.writeConfigFile(output)

    conf = output.getvalue()
    output.close()

    assert len(conf) > 0
