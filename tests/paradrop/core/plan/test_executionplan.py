
from paradrop.core.plan import executionplan
from paradrop.core.update import update_object


def test_docstrings():
    update = update_object.UpdateChute({
        "updateClass": "CHUTE",
        "updateType": "create",
        "name": "test",
        "tok": 0
    })
    executionplan.generatePlans(update)
    executionplan.aggregatePlans(update)

    for prio, func, abort in update.plans.plans:
        if func.func.__doc__ is None:
            raise Exception("{}.{} has no docstring.".format(
                func.func.__module__, func.func.__name__))
