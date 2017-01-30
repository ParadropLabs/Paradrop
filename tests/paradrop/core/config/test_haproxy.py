import StringIO

from mock import MagicMock, patch
from nose.tools import assert_raises

from paradrop.core.config import haproxy


@patch("paradrop.core.config.haproxy.ChuteStorage.getChuteList")
def test_generateConfigSections(getChuteList):
    chute1 = MagicMock()
    chute1.name = "chute1"

    getChuteList.return_value = [chute1]

    sections = haproxy.generateConfigSections()
    assert len(sections) > 0


def test_writeConfigFile():
    output = StringIO.StringIO()
    haproxy.writeConfigFile(output)

    conf = output.getvalue()
    output.close()

    assert len(conf) > 0
