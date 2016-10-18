from mock import MagicMock, patch
from nose.tools import assert_raises

from paradrop.backend import exc


UPDATE_TYPES = ["create", "start", "stop", "restart", "update", "delete"]


def test_all_generatePlans():
    """
    Test generatePlans method on all modules under paradrop.backend.exc with a
    variety of update types.
    """
    for module in dir(exc):
        if not hasattr(module, 'generatePlans'):
            continue

        for updateType in UPDATE_TYPES:
            update = MagicMock()
            update.updateType = updateType

            print("Testing {}.generatePlans with updateType={}".format(
                module, updateType))
            module.generatePlans(update)
            update.plans.addPlans.assert_called()
