from paradrop.backend.fc import updateObject 
from mock import patch, MagicMock

@patch('paradrop.backend.fc.updateObject.chutestorage')
@patch('paradrop.backend.fc.updateObject.out')
@patch('paradrop.backend.fc.updateObject.exc')
def test_updateObject(mExc, mOut, mStore):

    func = MagicMock()
    store = MagicMock()
    mStore.ChuteStorage.return_value = store
    update = dict(updateClass='CHUTE', updateType='create', name='test', 
            tok=111111, pkg=None, func=func)
    update = updateObject.parse(update)
    mExc.executionplan.generatePlans.return_value = False
    mExc.executionplan.executePlans.return_value = False
    update.execute()
    mExc.executionplan.generatePlans.assert_called_once_with(update)
    mExc.executionplan.aggregatePlans.assert_called_once_with(update)
    mExc.executionplan.executePlans.assert_called_once_with(update)
    store.saveChute.assert_called_once_with(update.new)
    assert mOut.usage.call_count == 1
    func.assert_called_once_with(update)
