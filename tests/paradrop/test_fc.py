from mock import Mock, patch
from nose.tools import assert_raises


@patch("paradrop.backend.exc.executionplan.abortPlans", return_value=True)
@patch("paradrop.backend.exc.executionplan.executePlans", return_value=True)
def test_update_object(executePlans, abortPlans):
    """
    Test the UpdateObject class
    """
    from paradrop.backend.fc.updateObject import UpdateObject

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

    update.saveState()

    update.func = Mock()
    update.complete(success=True)

    assert update.func.called
    assert update.result['success']

    update.execute()

    # Add a module that will fail at the generatePlans step.
    badModule = Mock()
    badModule.generatePlans = Mock(return_value=True)
    update.updateModuleList.append(badModule)
    update.execute()


@patch("paradrop.backend.fc.chutestorage.ChuteStorage.getChute")
def test_update_chute(getChute):
    """
    Test the UpdateChute class
    """
    from paradrop.backend.fc.updateObject import UpdateChute
    from paradrop.lib import chute

    obj = {
        'name': 'Test',
        'updateClass': 'CHUTE',
        'updateType': 'restart',
        'new': Mock(),
        'old': Mock(),
        'tok': 'tok',
        'special': 'stuff'
    }

    # This means when it looks up the chute in the ChuteStorage,
    # it will find one that is the same as the new chute.
    getChute.return_value = chute.Chute(obj)

    # We will remove this field on the new object to test the code
    # that imports fields from the old object from storage.
    del obj['special']

    update = UpdateChute(obj)
    assert update.new.special == update.old.special

    update.chuteStor = Mock()
    update.chuteStor.deleteChute = Mock()
    update.chuteStor.saveChute = Mock()

    update.saveState()
    assert update.chuteStor.saveChute.called

    update.updateType = "delete"
    update.saveState()
    assert update.chuteStor.deleteChute.called


def test_update_object_parse():
    """
    Test the updateobject parse function.
    """
    from paradrop.backend.fc.updateObject import UpdateChute, parse

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
