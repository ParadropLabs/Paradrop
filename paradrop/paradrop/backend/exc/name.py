###################################################################
# Copyright 2013-2014 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from paradrop.lib.utils.output import out, logPrefix

from paradrop.backend.exc import plangraph

def generatePlans(update):
    """
        This function looks at a diff of the current Chute (in @chuteStor) and the @newChute,
        then adds Plan() calls to make the Chute match the @newChute.

        Returns:
            True: abort the plan generation process
    """
    out.header("== %s %r\n" % (logPrefix(), update))
    
    # Make sure we need to create this chute (does it already exist)
    # TODO

    return None


