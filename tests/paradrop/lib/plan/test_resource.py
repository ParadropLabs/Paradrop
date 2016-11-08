from paradrop.lib.plan import resource
from mock import patch, MagicMock


@patch('paradrop.lib.plan.resource.out')
def test_generatePlans(mockOutput):
    """
    Test that the generatePlans function does it's job.
    """
    #Test that we get a out.header call
    update = MagicMock()
    resource.generatePlans(update)
    mockOutput.header.assert_called_once_with("%r\n" % (update))
