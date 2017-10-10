from paradrop.core.chute.chute import Chute
from paradrop.core.update import update_object
from mock import patch, MagicMock

@patch('paradrop.core.update.update_object.ChuteStorage')
@patch('paradrop.core.update.update_object.out')
@patch('paradrop.core.update.update_object.plan')
def test_update_object(mExc, mOut, mStore):
    store = MagicMock()
    mStore.return_value = store
    update = dict(updateClass='CHUTE', updateType='create', name='test',
            tok=111111)
    update = update_object.parse(update)
    mExc.executionplan.generatePlans.return_value = False
    mExc.executionplan.executePlans.return_value = False
    update.execute()
    mExc.executionplan.generatePlans.assert_called_once_with(update)
    mExc.executionplan.aggregatePlans.assert_called_once_with(update)
    mExc.executionplan.executePlans.assert_called_once_with(update)
    assert mOut.usage.call_count == 1


@patch('paradrop.core.update.update_object.ChuteStorage')
def test_UpdateChute(ChuteStorage):
    storage = MagicMock()
    ChuteStorage.return_value = storage

    #
    # Test creating a new chute.
    #
    storage.getChute.return_value = None

    update_data = {
        'name': 'test',
        'version': 4,
        'updateType': 'create'
    }
    update = update_object.UpdateChute(update_data)

    # Expected new chute state is RUNNING
    assert update.state == Chute.STATE_RUNNING

    # Update should have picked up version number from update_data.
    assert update.new.version == update_data['version']

    #
    # Test stopping an existing chute.
    #
    old_chute_data = {
        'name': 'test',
        'version': 5
    }
    storage.getChute.return_value = Chute(old_chute_data)

    update_data = {
        'name': 'test',
        'updateType': 'stop'
    }
    update = update_object.UpdateChute(update_data)

    # Expected new chute state is RUNNING
    assert update.state == Chute.STATE_STOPPED

    # Update should have picked up version number from the old chute.
    assert update.new.version == old_chute_data['version']
