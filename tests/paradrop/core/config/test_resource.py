from nose.tools import assert_raises
from mock import MagicMock, Mock, patch

from paradrop.core.config import resource
from paradrop.core.chute import chute


def test_computeResourceAllocation():
    chutes = []
    assert resource.computeResourceAllocation(chutes) == {}

    chutes = [MagicMock(), MagicMock()]

    chutes[0].name = "chute1"
    chutes[0].isRunning.return_value = True
    chutes[0].resources = {}

    chutes[1].name = "chute2"
    chutes[1].isRunning.return_value = False
    chutes[1].resources = {}

    allocation = resource.computeResourceAllocation(chutes)
    assert len(allocation) == 1

    chutes[1].name = "chute2"
    chutes[1].isRunning.return_value = True
    chutes[1].resources = {}

    allocation = resource.computeResourceAllocation(chutes)
    assert len(allocation) == 2
