###################################################################
# Copyright 2013-2014 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from paradrop.base.output import out


def generatePlans(update):
    """
        This function looks at a diff of the current Chute (in @chuteStor) and the @newChute,
        then adds Plan() calls to make the Chute match the @newChute.

        Returns:
            True: abort the plan generation process
    """
    out.verbose("%r\n" % (update))

    # TODO: Create a directory for the chute for us to hold onto things (dockerfile, OS config stuff)

    return None
