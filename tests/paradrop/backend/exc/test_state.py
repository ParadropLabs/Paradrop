from mock import MagicMock, patch
from nose.tools import assert_raises


def test_state_generatePlans():
    from paradrop.backend.exc.state import generatePlans

    update = MagicMock()

    # Check assumption about how MagicMock works.
    assert update.old is not None

    # Update to newer version should be ok.
    update.updateType = "update"
    update.old.version = 1
    update.old.version = 2
    result = generatePlans(update)
    print(result)
    assert result is None

    # Update to same version should return True for failure.
    update.old.version = 1
    update.new.version = 1
    assert generatePlans(update) is True

    # Update to older version should return True for failure.
    update.old.version = 2
    update.new.version = 1
    assert generatePlans(update) is True
