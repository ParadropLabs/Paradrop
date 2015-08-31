###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################


###############################################################################
# PRIORITYFLAGS: Define the priority numbers as constants here
###############################################################################

###############################################################################
# Security Checks
STRUCT_SECURITY_CHECK           = 1
TRAFFIC_SECURITY_CHECK          = 2
RESOURCE_SECURITY_CHECK         = 3
FILES_SECURITY_CHECK            = 4
RUNTIME_SECURITY_CHECK          = 5

###############################################################################
# Configuration Generation
NAME_RESV_PART                  = 8
STRUCT_GET_SYSTEM_DEVICES       = 9
STRUCT_GET_HOST_CONFIG          = 10
STRUCT_GET_INT_NETWORK          = 11
STRUCT_GET_OS_NETWORK           = 12
STRUCT_GET_OS_WIRELESS          = 13
STRUCT_GET_VIRT_NETWORK         = 14
RESOURCE_GET_VIRT_CPU           = 15
RESOURCE_GET_VIRT_MEM           = 16
RESOURCE_GET_OS_CONFIG          = 17
TRAFFIC_GET_OS_FIREWALL         = 18
TRAFFIC_GET_DEVELOPER_FIREWALL  = 19
RUNTIME_GET_VIRT_PREAMBLE       = 20
RUNTIME_GET_VIRT_DHCP           = 21
DHCP_GET_VIRT_RULES             = 22

###############################################################################
# Write Configuration Data
NAME_SETUP_DIRS                 = 50
STRUCT_SET_SYSTEM_DEVICES       = 51
STRUCT_SET_OS_WIRELESS          = 52
STRUCT_SET_OS_NETWORK           = 53
TRAFFIC_SET_OS_FIREWALL         = 54
RUNTIME_SET_VIRT_SCRIPT         = 56
RESOURCE_SET_VIRT_QOS           = 57
NAME_MNT_PART                   = 58
STATE_SET_VIRT_CONFIG           = 59
STATE_SET_VIRT_SCRIPT           = 60
DHCP_SET_VIRT_RULES             = 62
RUNTIME_SET_VIRT_DHCP           = 61
RUNTIME_RELOAD_CONFIG           = 63

###############################################################################
# Operations On Configuration Changes
STATE_CALL_CFG                  = 77
FILES_COPY_FROM_OS              = 78
FILES_FETCH                     = 79
STATE_FILES_STOP                = 80
FILES_COPY_USER                 = 81
FILES_COPY_TO_MNT               = 82
STARTUP_CALL_EARLY_START        = 83
STATE_SAVE_CFG                  = 84
STRUCT_RELOAD_NETWORK           = 85
STRUCT_RELOAD_WIFI              = 86
TRAFFIC_RELOAD_FIREWALL         = 87
RESOURCE_RELOAD_QOS             = 88
DHCP_RELOAD                     = 89
STATE_MAKE_EXEC                 = 90

###############################################################################
# Manipulate Chute
STATE_CALL_STOP                 = 91
STATE_CALL_UNFREEZE             = 92
STATE_CALL_START                = 93
STATE_CALL_FREEZE               = 94
STATE_FILES_START               = 96

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
        # Hold onto plans here
        self.plans = []
        self.planPtr = 0
        self.abtPtr = None
        self.abtPlans = []
        self.skipFunctions = []

    def addPlans(self, priority, todoPlan, abortPlan=[]):
        """
            Adds new Plan objects into the list of plans for this PlanMap.
            
            Arguments:
                @priority   : The priority number (1 is done first, 99 done last - see PRIORITYFLAGS section at top of this file)
                @todoPlan   : A tuple of (function, (args)), this is the function that completes the actual task requested
                              the args can either be a single variable, a tuple of variables, or None.
                @abortPlan  : A tuple of (function, (args)) or None. This is what should be called if a plan somewhere in the chain
                              fails and we need to undo the work we did here - this function is only called if a higher priority
                              function fails (ie we were called, then something later on fails that would cause us to undo everything
                              we did to setup/change the Chute).
        """
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

    def addMap(self, other):
        """
            Takes another PlanMap object and appends whatever the plans are into this plans object.
        """
        # Make sure to extend NOT append these new plans!
        self.plans.extend(other.plans)

    def sort(self):
        """
            Sorts the plans based on priority.
        """
        # Sort by the Priority (first index in tuple)
        self.plans = sorted(self.plans, key=lambda tup: tup[0])

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
                None                      : None is returned when there are no more todo's
        """
        # Are there more plans?
        if(self.planPtr == len(self.plans)):
            return None
        else:
            prio, todo, abt = self.plans[self.planPtr]
            self.planPtr += 1
            
            # After we updated the pointer, check if this is a skipped function
            # if so then we should just call getNextTodo again!
            if(todo.func in self.skipFunctions):
                return self.getNextTodo()
            else:
                return (todo.func, todo.args)
    
    def getNextAbort(self):
        """
            Like an iterator function, it returns each element in the list of abort plans in order.
            
            Returns: 
                (function, args) : Each todo is returned just how the user first added it
                None                      : None is returned when there are no more todo's
        """
        # Check if this is the first time calling the function
        if(self.abtPtr == None):
            ###################################################################################
            # If so we generate the abort list right now
            # The reason we do this is that depending on how far along the plan got, we have
            # to abort different things, and some functions will exist in multiple abort plans
            # so we need to call stuff in the proper order
            ###################################################################################
            
            # So start at one minus the todoPlan that failed
            startPoint = self.planPtr - 1

            for prio, todo, abt in self.plans[startPoint::-1]:
                # If nothing keep looking
                if(not abt):
                    continue

                # This should be a list of Plan() objects
                for a in abt:
                    # See if we are already going to do this Plan()
                    if(a not in self.abtPlans):
                        self.abtPlans.append(a)
            
            # Lastly set the abtPtr so we know we can start
            self.abtPtr = 0
        
        # Here occurs after the first time call check
        # Now we actually return each new Plan from abtPlans
        if(self.abtPtr == len(self.abtPlans)):
            return None
        else:
            abt = self.abtPlans[self.abtPtr]
            self.abtPtr += 1
            return (abt.func, abt.args)

    def __repr__(self):
        return "<%s %r: %d Plans>" % (self.__class__.__name__, self.name, len(self.plans))
    
    def __str__(self):
        ret = "%r:\n" % self.name
        for p, todopl, abortpl in self.plans:
            ret += "  %d: %r || %r\n" % (p, todopl, abortpl)
        return ret
