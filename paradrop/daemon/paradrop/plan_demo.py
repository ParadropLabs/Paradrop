"""
This module is here purely to help with understanding the rather complex
execution plan in Paradrop.  Simply run it (python -m paradrop.plan_demo),
and it will walk through all of the functions that make up a chute creation
operation.
"""
from __future__ import print_function

from paradrop.core.update.update_object import UpdateChute
from paradrop.core.plan import executionplan, plangraph


def loadPriorityMap():
    """
    Make a map of priority values back to their names for reference.

    These are defined as constant integer values in
    paradrop.backend.exc.plangraph.  For example, for priority 9
    (STRUCT_GET_SYSTEM_DEVICES), the dictionary produced by this function
    would contain the entry 9: "STRUCT_GET_SYSTEM_DEVICES".
    """
    priomap = dict()
    for item in dir(plangraph):
        value = getattr(plangraph, item)
        if isinstance(value, int):
            priomap[value] = item
    return priomap


if __name__ == "__main__":
    priomap = loadPriorityMap()

    update = UpdateChute({
        "updateClass": "CHUTE",
        "updateType": "create",
        "name": "test",
        "tok": 0
    })
    executionplan.generatePlans(update)
    executionplan.aggregatePlans(update)

    for prio, func, abort in update.plans.plans:
        print("Module: {}".format(func.func.__module__))
        print("Function: {}".format(func.func.__name__))
        print("Priority: {} ({})".format(priomap[prio], prio))
        if func.func.__doc__ is None:
            print("\n    Function has no docstring.\n")
        else:
            print(func.func.__doc__)

