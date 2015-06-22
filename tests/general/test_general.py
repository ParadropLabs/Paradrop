'''
General tests for stability
'''

import paradrop
from paradrop.lib.utils.output import out


def testTestsWork():
    ''' Tests Work '''
    assert 1


def testOut():
    out.info('Hey!')
    assert 1
