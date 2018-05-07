from mock import Mock, patch
from nose.tools import assert_raises


@patch("paradrop.core.plan.executionplan.abortPlans", return_value=True)
@patch("paradrop.core.plan.executionplan.executePlans", return_value=True)
def test_update_object(executePlans, abortPlans):
    """
    Test the UpdateObject class
    """
    from paradrop.core.update.update_object import UpdateObject

    obj = {
        'name': 'Test',
        'updateClass': 'CHUTE',
        'updateType': 'CREATE',
        'tok': 'tok'
    }
    update = UpdateObject(obj)

    # Test some basic functions
    assert "Update" in repr(update)
    assert "Update" in str(update)

    update.func = Mock()
    update.complete(success=True)

    assert update.result['success']

    update.execute()

    # Add a module that will fail at the generatePlans step.
    badModule = Mock()
    badModule.generatePlans = Mock(return_value=True)
    update.updateModuleList.append(badModule)
    update.execute()


@patch("paradrop.core.chute.chute_storage.ChuteStorage.getChute")
def test_update_chute(getChute):
    """
    Test the UpdateChute class
    """
    from paradrop.core.update.update_object import UpdateChute
    from paradrop.core.chute import chute

    obj = {
        'name': 'Test',
        'updateClass': 'CHUTE',
        'updateType': 'restart',
        'new': Mock(),
        'old': Mock(),
        'tok': 'tok'
    }

    # This means when it looks up the chute in the ChuteStorage,
    # it will find one that is the same as the new chute.
    getChute.return_value = chute.Chute(name="Test", description="testing",
            version="1")

    update = UpdateChute(obj)
    assert update.new.description == "testing"
    assert update.new.version == "1"


def test_update_object_parse():
    """
    Test the updateobject parse function.
    """
    from paradrop.core.update.update_object import UpdateChute, parse

    obj = {
        'name': 'Test',
        'updateClass': 'CHUTE',
        'updateType': 'CREATE',
        'tok': 'tok'
    }

    # Test creating an UpdateChute object
    update = parse(obj)
    assert isinstance(update, UpdateChute)

    # Test an unrecognized type
    obj['updateClass'] = "FAIL"
    assert_raises(Exception, parse, obj)
