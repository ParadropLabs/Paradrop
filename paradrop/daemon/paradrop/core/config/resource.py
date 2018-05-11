from paradrop.core.chute.chute_storage import ChuteStorage
from paradrop.lib.misc import resopt


def computeResourceAllocation(chutes):
    service_names = []
    service_cpu_fractions = []
    allocation = {}
    for chute in chutes:
        if not chute.isRunning():
            continue

        for service in chute.get_services():
            service_names.append(service.get_container_name())

            cpu_fraction = service.requests.get('cpu-fraction', None)
            service_cpu_fractions.append(cpu_fraction)

    # Use the optimizer to allocate cpu fractions and fill in unspecified
    # (None) values.  The result is a vector that sums to one.
    new_cpu_fractions = resopt.allocate(service_cpu_fractions, total=1.0)

    n = len(service_names)
    for i in range(n):
        # Convert the fraction to an integer.  We multiply by 1024*n so that
        # they all center around 1024, which is what Docker assigns to
        # containers by default.
        cpu_shares = int(round(new_cpu_fractions[i] * 1024 * n))

        # Keep it above 2.  Docker treats 0 and 1 as special values.
        cpu_shares = max(cpu_shares, 2)

        name = service_names[i]
        allocation[name] = {
            'cpu_shares': cpu_shares
        }

    return allocation


def getResourceAllocation(update):
    """
    Allocate compute resources for chutes.

    Sets cache variables "newResourceAllocation" and "oldResourceAllocation".
    """
    chuteStore = ChuteStorage()
    chutes = chuteStore.getChuteList()

    old_allocation = computeResourceAllocation(chutes)

    # Insert the new chute into the list and replace the old version if it
    # existed.
    chutes.insert(0, update.new)
    for i in range(1, len(chutes)):
        if chutes[i].name == update.new.name:
            del chutes[i]
            break

    new_allocation = computeResourceAllocation(chutes)

    update.cache_set('newResourceAllocation', new_allocation)
    update.cache_set('oldResourceAllocation', old_allocation)
