###################################################################
# Copyright 2013-2014 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from pdtools.lib.output import out

from paradrop.backend.exc import plangraph

def generatePlans(update):
    """
        This function looks at a diff of the current Chute (in @chuteStor) and the @newChute,
        then adds Plan() calls to make the Chute match the @newChute.

        Returns:
            True: abort the plan generation process
    """
    out.verbose("%r\n" % (update))

    #print any warnings from previous update if they exist
    if hasattr(update, 'pkg') and update.old != None and update.old.warning != None:
        update.pkg.request.write(update.old.warning + '\n')

    # TODO: Create a directory for the chute for us to hold onto things (dockerfile, OS config stuff)

    return None
