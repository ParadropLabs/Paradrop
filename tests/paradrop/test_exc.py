from nose.tools import assert_raises

def test_plangraph():
    from paradrop.backend.exc.plangraph import PlanMap

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
