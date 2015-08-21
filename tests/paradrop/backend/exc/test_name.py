from paradrop.backend.exc import name
from mock import patch, MagicMock


@patch('paradrop.backend.exc.name.out')
def test_generatePlans(mockOutput):
    """
    Test that the generatePlans function does it's job.
    """
    #Test that we get a warning if there is one
    update = MagicMock()
    update.old.warning = "TEST WARNING"
    name.generatePlans(update)
    update.pkg.request.write.assert_called_once_with(update.old.warning + "\n")
