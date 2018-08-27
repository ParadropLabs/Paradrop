###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################
'''
    This module contains the methods required to generate and act upon
    execution plans.

    An execution plan is a set of operations that must be performed
    to update a Chute from some old state into the new state provided
    by the API server.

    All plans that are generated are function pointers, as in no actual
    operations are performed during the generation process.
'''

import traceback

from twisted.internet.defer import Deferred

from paradrop.base.output import out


def generatePlans(update):
    """
    For an update object provided this function references the updateModuleList which lets all exc
    modules determine if they need to add functions to change the state of the system when new 
    chutes are added to the OS.

    Returns: True in error, as in we should stop with this update plan
    """
    out.header('Generating %r\n' % (update))

    # Iterate through the list provided for this update type
    for mod in update.updateModuleList:
        if(mod.generatePlans(update)):
            return True


def aggregatePlans(update):
    """
        Takes the PlanMap provided which can be a combination of changes for multiple
        different chutes and it puts things into a sane order and removes duplicates where
        possible.

        This keeps things like reloading networking from happening twice if 2 chutes make changes.

        Returns:
            A new PlanMap that should be executed
    """
    out.header('Aggregating plans\n')
    # For now we just order the plans and return a new list
    update.plans.sort()


def executePlans(update):
    """
        Primary function that actually executes all the functions that were added to plans by all
        the exc modules. This function can heavily modify the OS/files/etc.. so the return value is
        very important.
        Returns:
            True in error : abortPlans function should be called
            False otherwise : everything is OK
    """
    out.header('Executing plans %r\n' % (update))
    # Finding the functions to call is actually done by a 'iterator' like function in the plangraph module
    while(True):
        # This function either returns None or a tuple just like generate added to it
        p = update.plans.getNextTodo()

        # No more to do?
        if(not p):
            break

        # Explode tuple otherwise
        func, args = p

        # We are in a try-except block so if func isn't callable that will catch it
        try:
            out.verbose('Calling %s\n' % (func))
            update.progress("Calling {}".format(func.__name__))
            #
            # Call the function from the execution plan
            #
            # args may be empty, but we don't want to pass in a tuple if we don't need to.
            # This below explodes the args so if @args is (), then what is passed is @update
            skipme = func(*((update, ) + args))

        except Exception as e:
            out.exception(e, True)
            # plans = str(update.plans)) # Removed because breaks new out.exception call
            out.warn("Failed to execute plan %s%s" % (func.__name__, args))
            update.responses.append({'exception': str(e), 'traceback': traceback.format_exc()})
            update.failure = str(e)
            return True

        # The functions we call here can return other functions, if they do
        # these are functions that should be skipped later on (for instance a
        # set* function discovering it didn't change anything, later on we
        # shouldn't call the corresponding reload function)
        if skipme is not None:
            # If the function returned a Deferred, we will drop out of the
            # execution pipeline and resume later.
            if isinstance(skipme, Deferred):
                out.verbose('Function {} returned a Deferred'.format(func))
                return skipme

            # These functions can return individual functions to skip, or a
            # list of multiple functions
            elif callable(skipme):
                skipme = [skipme]

            for skip in skipme:
                out.warn('Identified a skipped function: %r\n' % (skip))
                update.plans.registerSkip(skip)

    # Now we are done
    return False


def abortPlans(update):
    """
        This function should be called if one of the Plan objects throws an Exception.
        It takes the PlanMap argument and calls the getNextAbort function just like executePlans does with todoPlans.
        This dynamically generates an abort plan list based on what plans were originally executed.
        Returns:
            True in error : This is really bad
            False otherwise : we were able to restore system state back to before the executeplans function was called
    """
    out.header('Aborting plans %r\n' % (update.plans))
    sameError = False
    while(True):
        # This function either returns None or a tuple just like generate added to it
        p = update.plans.getNextAbort()

        # No more to do?
        if(not p):
            break

        # Explode tuple otherwise
        func, args = p

        # We are in a try-except block so if func isn't callable that will catch it
        try:
            out.verbose('Calling {}\n'.format(func))
            update.progress('Calling {}'.format(func.__name__))

            func(*((update, ) + args))

            # If the func is called without exception then clear the @sameError flag for the next function call
            sameError = False

        except Exception as e:
            # Since we are running this in an infinite loop if a major function throws an error
            # we could loop forever, so check for the error, which is only reset at the end of the loop
            if(sameError):
                return True
            update.responses.append({'exception': str(e), 'traceback': traceback.format_exc()})
            out.fatal('An abort function raised an exception!!! %r: %s\n%s\n' % (update.plans, str(e), traceback.format_exc()))
            sameError = True

    # Getting here we assume the system state has been restored using our abort plan
    return False
