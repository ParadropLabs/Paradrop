from paradrop.backend import update_object 
from mock import patch, MagicMock

@patch('paradrop.backend.update_object.chutestorage')
@patch('paradrop.backend.update_object.out')
@patch('paradrop.backend.update_object.plan')
def test_update_object(mExc, mOut, mStore):

    store = MagicMock()
    mStore.ChuteStorage.return_value = store
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
