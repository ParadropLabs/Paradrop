from paradrop.core.plan import name
from mock import patch, MagicMock


@patch('paradrop.core.plan.name.out')
def test_generatePlans(mockOutput):
    """
    Test that the generatePlans function does it's job.
    """
    update = MagicMock()
    assert name.generatePlans(update) is None
