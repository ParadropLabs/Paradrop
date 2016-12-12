from paradrop.lib.chute import chutestorage
from paradrop.lib.misc import resopt


def computeResourceAllocation(chutes):
    chute_names = []
    chute_cpu_fractions = []
    allocation = {}
    for chute in chutes:
        if not chute.isRunning():
            continue

        resources = getattr(chute, 'resources', {})
        cpu_fraction = resources.get('cpu_fraction', None)

        chute_names.append(chute.name)
        chute_cpu_fractions.append(cpu_fraction)

        allocation[chute.name] = {
            # Pass through prioritize flag: if chutes ask, they get it.
            'prioritize_traffic': resources.get('prioritize_traffic', False)
        }

    # Use the optimizer to allocate cpu fractions and fill in unspecified
    # (None) values.  The result is a vector that sums to one.
    new_cpu_fractions = resopt.allocate(chute_cpu_fractions, total=1.0)

    n = len(chute_names)
    for i in range(n):
        # Convert the fraction to an integer.  We multiply by 1024*n so that
        # they all center around 1024, which is what Docker assigns to
        # containers by default.
        cpu_shares = int(round(new_cpu_fractions[i] * 1024 * n))

        # Keep it above 2.  Docker treats 0 and 1 as special values.
        cpu_shares = max(cpu_shares, 2)

        name = chute_names[i]
        allocation[name].update({
            'cpu_shares': cpu_shares
        })

    return allocation


def getResourceAllocation(update):
    chuteStore = chutestorage.ChuteStorage()
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

    update.new.setCache('newResourceAllocation', new_allocation)
    update.new.setCache('oldResourceAllocation', old_allocation)
