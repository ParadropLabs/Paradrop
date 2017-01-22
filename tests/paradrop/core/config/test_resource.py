from nose.tools import assert_raises
from mock import MagicMock, Mock, patch

from paradrop.core.config import resource
from paradrop.core.chute import chute


def test_computeResourceAllocation():
    chutes = []
    assert resource.computeResourceAllocation(chutes) == {}

    chutes = [MagicMock(), MagicMock()]
    chutes[0].isRunning.return_value = True
    chutes[0].isRunning.return_value = False

    allocation = resource.computeResourceAllocation(chutes)
    assert len(allocation) == 1
