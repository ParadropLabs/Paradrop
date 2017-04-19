from mock import MagicMock, patch
from nose.tools import assert_raises

from paradrop.core.plan import hostconfig


def test_generatePlans():
    update = MagicMock()
    assert hostconfig.generatePlans(update) is None
    assert update.plans.addPlans.called
