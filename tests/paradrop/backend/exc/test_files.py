from paradrop.backend.exc import files
from mock import patch, MagicMock


@patch('paradrop.backend.exc.files.out')
def test_generatePlans(mockOutput):
    """
    Test that the generatePlans function does it's job.
    """
    #Test that we get a out.header call
    update = MagicMock()
    files.generatePlans(update)
    mockOutput.header.assert_called_once_with("%r\n" % (update))
