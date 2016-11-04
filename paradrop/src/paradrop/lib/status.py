"""
    This file contains the status variables of the ParaDrop router.
    They are defaulted to some particular value and can be called by any module in the paradrop
    system with the following code:

        from paradrop.lib import status
        print(status.STUFF)
"""

wampConnected = False
apiTokenVerified = False