###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

import heapq

###############################################################################
# PRIORITYFLAGS: Define the priority numbers as constants here
#
# These priority numbers control the order of execution for the stages of an
# update.  Many of them are unused and can be repurposed.  Feel free to insert
# new steps as needed.  However, be very careful changing the order of existing
# steps, as many of them require a particular ordering.
###############################################################################

###############################################################################
# Security Checks
ENFORCE_ACCESS_RIGHTS           = 1

###############################################################################
# Configuration Generation
DOWNLOAD_CHUTE_FILES            = 6
LOAD_CHUTE_CONFIGURATION        = 7
STRUCT_GET_SYSTEM_DEVICES       = 8
STRUCT_GET_RESERVATIONS         = 9
STRUCT_GET_HOST_CONFIG          = 10
STRUCT_GET_INT_NETWORK          = 11
STRUCT_GET_OS_NETWORK           = 12
STRUCT_GET_OS_WIRELESS          = 13
STRUCT_GET_L3BRIDGE_CONFIG      = 14
TRAFFIC_GET_OS_FIREWALL         = 18
TRAFFIC_GET_DEVELOPER_FIREWALL  = 19
RUNTIME_GET_VIRT_PREAMBLE       = 20
RUNTIME_GET_VIRT_DHCP           = 21
DHCP_GET_VIRT_RULES             = 22
STATE_GENERATE_SERVICE_PLANS    = 23

###############################################################################
# Build Docker Image
STATE_BUILD_IMAGE               = 30
STATE_CHECK_IMAGE               = 31
STATE_CALL_STOP                 = 35

###############################################################################
# System Validation
CHECK_SYSTEM_DEVICES            = 40
RESOURCE_GET_ALLOCATION         = 41

###############################################################################
# Write Configuration Data
RUNTIME_RELOAD_CONFIG_BACKOUT   = 45
CREATE_VOLUME_DIRS              = 50
STRUCT_SET_SYSTEM_DEVICES       = 51
STRUCT_SET_HOST_CONFIG          = 52
STRUCT_SET_OS_WIRELESS          = 53
STRUCT_SET_OS_NETWORK           = 54
TRAFFIC_SET_OS_FIREWALL         = 55
STRUCT_SET_L3BRIDGE_CONFIG      = 56
RESOURCE_SET_VIRT_QOS           = 57
NAME_MNT_PART                   = 58
STATE_SET_VIRT_CONFIG           = 59
STATE_SET_VIRT_SCRIPT           = 60
RUNTIME_SET_VIRT_DHCP           = 61
DHCP_SET_VIRT_RULES             = 62
RUNTIME_RELOAD_CONFIG           = 63

###############################################################################
# Operations On Configuration Changes
STATE_CALL_CFG                  = 70
FILES_COPY_FROM_OS              = 71
ZEROTIER_CONFIGURE              = 72
AIRSHARK_CONFIGURE              = 73
TELEMETRY_SERVICE               = 74
APPLY_WAIT_ONLINE_FIX           = 75
FILES_COPY_USER                 = 76
FILES_COPY_TO_MNT               = 77
STARTUP_CALL_EARLY_START        = 78
STRUCT_RELOAD_NETWORK           = 79
STRUCT_RELOAD_WIFI              = 80
TRAFFIC_RELOAD_FIREWALL         = 81
DHCP_RELOAD                     = 82
STATE_MAKE_EXEC                 = 83

###############################################################################
# Manipulate Chute Container
STATE_NET_STOP                  = 84
STATE_CREATE_BRIDGE             = 85
STATE_CALL_STOP                 = 86
STATE_CALL_START                = 87
STATE_CALL_FREEZE               = 88
STATE_CALL_CLEANUP              = 89
STATE_FILES_START               = 90
STATE_NET_START                 = 91
STATE_REMOVE_BRIDGE             = 92

STATE_SAVE_CHUTE                = 95
RESOURCE_SET_ALLOCATION         = 96

RECONFIGURE_PROXY               = 98
SNAP_INSTALL                    = 99
COAP_CHANGE_PROCESSES           = 100


class Plan:
    """
        Helper class to hold onto the actual plan data associated with each plan
    """
    def __init__(self, func, *args):
        """
            Takes a tuple of (function, (args)) of actions to perform at some point.
        """
        self.func = func
        self.args = args

    def __repr__(self):
        return "<%r>" % (self.func)

    def __eq__(self, o):
        """Implementing equal function so we can do 'if a in b' logic"""
        if(not self.func is o.func):
            return False
        if(self.args != o.args):
            return False
        return True


class PlanMap:
    """
        This class helps build a dependency graph required to determine what steps are
        required to update a Chute from a previous version of its configuration.
    """
    def __init__(self, name):
        """Hold onto a name object so we know what we are referencing with this PlanMap."""
        self.name = name

        # Hold onto all available plans here.
        self.plans = []
        self.abortPlans = []

        # workingPlans is implemented as a heapq. All of the other plan lists
        # are plain lists.
        self.maxPriorityReturned = 0
        self.startedAbort = False
        self.workingPlans = []
        self.workingAbortPlans = []

        self.skipFunctions = []

    def addPlans(self, priority, todoPlan, abortPlan=[]):
        """
            Adds new Plan objects into the list of plans for this PlanMap.

            Arguments:
                @priority   : The priority number (1 is done first, 99 done last - see PRIORITYFLAGS section at top of this file)
                @todoPlan   : A tuple of (function, (args)), this is the function that completes the actual task requested
                              the args can either be a single variable, a tuple of variables, or None.
                @abortPlan  : A tuple of (function, (args)) or a list of tuple or None.
                              This is what should be called if a plan somewhere in the chain
                              fails and we need to undo the work we did here - this function is only called if a higher priority
                              function fails (ie we were called, then something later on fails that would cause us to undo everything
                              we did to setup/change the Chute).
        """
        # It is OK to call addPlans out of order during the plan generation
        # phase, but if we have already started execution and add something out
        # of order, it indicates a programming error.
        if priority < self.maxPriorityReturned:
            raise Exception("Added plan out of order during execution.")

        # They can provide multiple abortPlans in a list, or 1 in a tuple, or none at all empty list
        # But internally the abortPlan should be either None or a list (even if the list is size 1)
        if(isinstance(abortPlan, tuple)):
            abortP = [Plan(*abortPlan)]
        elif(isinstance(abortPlan, list)):
            # See if there is no plans at all
            if(len(abortPlan) == 0):
                abortP = None
            else:
                abortP = [Plan(*a) for a in abortPlan]
        else:
            raise Exception('BadAbortPlan', 'Plan should be tuple, list of tuples, or empty')

        todoP = Plan(*todoPlan)

        # Now add into the set
        self.plans.append((priority, todoP, abortP))
        heapq.heappush(self.workingPlans, (priority, todoP, abortP))

    def addMap(self, other):
        """
            Takes another PlanMap object and appends whatever the plans are into this plans object.
        """
        # Make sure to extend NOT append these new plans!
        self.plans.extend(other.plans)

        for item in other.plans:
            heapq.heappush(self.workingPlans, item)

    def sort(self):
        """
            Sorts the plans based on priority.
        """
        # Sort by the Priority (first index in tuple)
        self.plans.sort(key=lambda tup: tup[0])

    def registerSkip(self, func):
        """
            Register this function as one to skip execution on, if provided it shouldn't return
            the (func, args) tuple as a result from the getNextTodo function.
        """
        self.skipFunctions.append(func)

    def getNextTodo(self):
        """
        Like an iterator function, it returns each element in the list of plans in order.

        Returns:
            (function, args) : Each todo is returned just how the user first added it
            None             : None is returned when there are no more todo's
        """
        if len(self.workingPlans) == 0:
            return None
        else:
            prio, todo, abt = heapq.heappop(self.workingPlans)
            self.maxPriorityReturned = prio

            # After popping the next plan, check if this is a skipped function.
            # If so, then get the next plan.
            if todo.func in self.skipFunctions:
                return self.getNextTodo()
            else:
                self.abortPlans.append(abt)
                return (todo.func, todo.args)

    def getNextAbort(self):
        """
        Like an iterator function, it returns each element in the list of abort plans in order.

        Returns:
            (function, args) : Each todo is returned just how the user first added it
            None             : None is returned when there are no more todo's
        """
        # Check if this is the first time calling the function
        if not self.startedAbort:
            ###################################################################################
            # If so we generate the abort list right now
            # The reason we do this is that depending on how far along the plan got, we have
            # to abort different things, and some functions will exist in multiple abort plans
            # so we need to call stuff in the proper order
            ###################################################################################

            # Skip the last stage and iterate in reverse order.
            for stage in reversed(self.abortPlans[:-1]):
                # If nothing keep looking
                if not stage:
                    continue

                # This should be a list of Plan() objects
                for a in stage:
                    # See if we are already going to do this Plan()
                    if a not in self.workingAbortPlans:
                        self.workingAbortPlans.append(a)

            # Lastly, set the started flag, so we don't initialize the list again.
            self.startedAbort = True

        if len(self.workingAbortPlans) == 0:
            return None
        else:
            abt = self.workingAbortPlans.pop(0)
            return (abt.func, abt.args)

    def __repr__(self):
        return "<%s %r: %d Plans>" % (self.__class__.__name__, self.name, len(self.plans))

    def __str__(self):
        ret = "%r:\n" % self.name
        for p, todopl, abortpl in self.plans:
            ret += "  %d: %r || %r\n" % (p, todopl, abortpl)
        return ret
