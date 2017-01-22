from paradrop.core.plan import resource
from mock import patch, MagicMock


@patch('paradrop.core.plan.resource.out')
def test_generatePlans(mockOutput):
    """
    Test that the generatePlans function does it's job.
    """
    #Test that we get a out.header call
    update = MagicMock()
    resource.generatePlans(update)
