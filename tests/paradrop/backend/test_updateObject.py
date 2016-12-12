from paradrop.backend import updateObject 
from mock import patch, MagicMock

@patch('paradrop.backend.updateObject.chutestorage')
@patch('paradrop.backend.updateObject.out')
@patch('paradrop.backend.updateObject.plan')
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
    assert mOut.usage.call_count == 1
    func.assert_called_once_with(update)
