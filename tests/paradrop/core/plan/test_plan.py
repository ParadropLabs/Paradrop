from nose.tools import assert_raises

from mock import Mock

from pdmock import MockChute, MockUpdate, do_nothing, make_dummy


def test_executionplan():
    from paradrop.core.plan import executionplan as excplan
    from paradrop.core.plan import struct

    update = Mock()

    # Simulate a module that fails during the generatePlans step.
    badModule = Mock()
    badModule.generatePlans = Mock(return_value=True)
    update.updateModuleList = [badModule]
    assert excplan.generatePlans(update)

    # This one should succeed.
    update.updateModuleList = [struct]
    assert excplan.generatePlans(update) is None

    excplan.aggregatePlans(update)

    # Make a list of dummy functions to run
    plans = list()
    plans.append((do_nothing, ("data",)))
    plans.append((make_dummy(do_nothing), ("data",)))
    plans.append((do_nothing, ("skipped",)))
    plans.append(None)  # Popping None will end the loop.
    plans.reverse()
    abortPlans = list(plans)

    # Should return False for success
    update.plans = Mock()
    update.plans.getNextTodo = plans.pop
    update.plans.getNextAbort = abortPlans.pop
    assert excplan.executePlans(update) is False
    assert excplan.abortPlans(update) is False

    # Make a plan with non-callable ("fail" string) to cause an error
    plans = list()
    def fail(data):
        pass

    plans.append((fail, ("data",)))
    plans.append((fail, ("data",))) # Need two failures to break abortPlans
    plans.append(None)  # Popping None will end the loop.
    plans.reverse()
    abortPlans = list(plans)

    # Should return True for failure
    update.plans = Mock()
    update.plans.getNextTodo = plans.pop
    update.plans.getNextAbort = abortPlans.pop
    assert excplan.executePlans(update)
    assert excplan.abortPlans(update)


def test_plangraph():
    from paradrop.core.plan.plangraph import PlanMap

    class Output(object):
        pass
    def f(x):
        print(x)
    out = Output()
    out.info = f
    out.warn = f
    out.err = f

    class TestChute(object):
        pass
    def exceptionFunc(x):
        raise Exception('test5')

    def security0(x):
        out.info(x)
    def security1(x):
        out.info(x)

    def get0(x):
        out.info(x)
    def get1(x):
        out.info(x)
 
    def set0(x):
        out.info(x)
        return reload0
    def set1(x):
        out.info(x)
    def revertSet0(x):
        out.warn(x)
    def revertSet1(x):
        out.warn(x)

    def reload0(x):
        out.info(x)
    def reload1(x):
        out.info(x)
    def revertReload0(x):
        out.warn(x)
    def revertReload1(x):
        out.warn(x)

    #
    # Setup new map
    #
    pm = PlanMap('test')
    ch = TestChute()
    ch.guid = 'TESTCHUTE'

    #
    # Generate plans portion
    #
    reload1 = exceptionFunc

    # Category zere stuff
    pm.addPlans(0, (lambda x: out.info(x), 'category 0'), (lambda x: out.warn(x), 'reverting category 0'))

    # Category one stuff
    abtPlans = []
    pm.addPlans(1, (security0, 'sec0'))

    # Abort plan should be a tuple or list, not a string.
    assert_raises(Exception, pm.addPlans, 11, (get0, 'get0'), "fail")

    pm.addPlans(11, (get0, 'get0'))

    abtPlans.append((revertSet0, 'reverting set 0'))
    pm.addPlans(21, (set0, 'set0'), abtPlans)

    abtPlans.append((revertReload0, 'reverting reload 0'))

    # Intentionally add same function with different parameter to exercise
    # different section of equality check.
    abtPlans.append((revertReload0, 'reverting reload 0 (again)'))

    pm.addPlans(31, (reload0, 'reload0'), abtPlans)

    # Category two stuff
    abtPlans = []
    pm.addPlans(2, (security1, 'sec1'))

    pm.addPlans(12, (get1, 'get1'))

    abtPlans.append((revertSet1, 'reverting set 1'))
    pm.addPlans(22, (set1, 'set1'), abtPlans)

    abtPlans.append((revertReload1, 'reverting reload 1'))
    pm.addPlans(32, (reload1, 'reload1'), abtPlans)

    # Category three stuff
    pm.addPlans(43, (lambda x: out.info(x), 'category 3'), (lambda x: out.warn(x), 'reverting category 3'))

    out.info(pm)

    #
    # Aggregate plans portion
    #
    pm.sort()

    #
    # Execute Plans portion
    #
    doAbort = False
    while(True):
        p = pm.getNextTodo()
        if(not p):
            break
        f, a = p
        try:
            s = f(a)
            if(s):
                out.info('Got skip function: %s' % s.__module__)
                pm.registerSkip(s)
        except Exception as e:
            doAbort = True
            break

    #
    # Abort plans portion
    #
    if(doAbort):
        while(True):
            p = pm.getNextAbort()
            if(not p):
                break
            f, a = p
            try:
                f(a)
            except Exception as e:
                out.err(e)
                break

    # After the last item, we should get None back.
    assert pm.getNextTodo() != None
    assert pm.getNextTodo() == None

    assert repr(pm) == "<PlanMap 'test': 10 Plans>"

    # This should end up doubling the plans in pm.
    pm.addMap(pm)
    assert repr(pm) == "<PlanMap 'test': 20 Plans>"

def test_state():
    """
    Test plan generation for state module
    """
    from paradrop.core.plan import state
    from paradrop.core.chute.chute import Chute
    from paradrop.base import settings

    # Set this to exercise debug mode code
    settings.DEBUG_MODE = True

    update = MockUpdate()

    # generatePlans returns:
    # True on failure
    # None on success

    # Stop with no old chute should fail
    update.old = None
    update.new = MockChute()
    update.updateType = "stop"
    assert state.generatePlans(update) is True

    # Install with no old chute should succeed
    update.updateType = "install"
    update.new.state = Chute.STATE_RUNNING
    assert state.generatePlans(update) is None

    # Entering invalid state should fail
    update.new.state = Chute.STATE_INVALID
    assert state.generatePlans(update) is True

    # Start with old chute already running should fail
    update.old = MockChute()
    update.updateType = "start"
    update.old.state = Chute.STATE_RUNNING
    assert state.generatePlans(update) is True

    # But if the old chute was stopped, then start should succeed
    update.old.state = Chute.STATE_STOPPED
    assert state.generatePlans(update) is None

    # Should be fine
    update.updateType = "restart"
    assert state.generatePlans(update) is None

    # Create should fail when old chute exists
    update.updateType = "create"
    assert state.generatePlans(update) is True

    # Delete and set to stopped is fine
    update.new.state = Chute.STATE_STOPPED
    update.updateType = "delete"
    assert state.generatePlans(update) is None

    # Stopping an already stopped chute should fail
    update.updateType = "stop"
    update.old.state = Chute.STATE_STOPPED
    assert state.generatePlans(update) is True

    # Stopping a running chute is fine
    update.old.state = Chute.STATE_RUNNING
    assert state.generatePlans(update) is None
