"""
Resource optimization functions.
"""

#from scipy.optimize import linprog


def allocate(reservations, total=1.0):
    """
    Allocate resources among slices with specified and unspecified reservations.

    Returns a new list of values with the following properties:
    - Every value is >= the corresponding input value.
    - The result sums to `total`.

    Examples:
    allocate([0.25, None, None]) -> [0.5, 0.25, 0.25]
    allocate([0.4, None, None]) -> [0.6, 0.2, 0.2]
    allocate([0.2, 0.2, 0.2]) -> [0.33, 0.33, 0.33]
    allocate([None, None, None]) -> [0.33, 0.33, 0.33]
    allocate([0.5, 0.5, 0.5]) -> ERROR
    """
    n = len(reservations)
    if n <= 0:
        return []

    remaining = total
    for r in reservations:
        if r is not None:
            remaining -= r

    result = list(reservations)

    # Divide the remaining resources among all slices.
    if remaining > 0:
        share = float(remaining) / n
        for i in range(n):
            if result[i] is None:
                result[i] = share
            else:
                result[i] += share
    elif remaining < 0:
        raise Exception("Resource allocation is infeasible (total {} > {})".format(
            sum(result), total))

    return result


#
# The optimize function requires scipy.  It might be useful later.
#

#def optimize(reservations, ub=1):
#    n = len(reservations)
#
#    # In case some reservations are unspecified (None), calculate the remaining
#    # share and divide it evenly among the unspecified buckets.
#    #
#    # Example:
#    # [0.2, None, None] -> [0.2, 0.4, 0.4]
#    floor = allocate(reservations, ub)
#    print(floor)
#
#    # Coefficients for the objective function.  We want to maximize the sum, but
#    # linprog does minimization, hence the negative.
#    c = [-1] * n
#
#    # Constraints (A_ub * x <= b_ub).
#    A_ub = []
#    b_ub = []
#
#    for i in range(n):
#        # Competition constraint (sum of all others <= ub-reservation[i]).
#        # If all others (j != i) use up their allocated resource, there must
#        # be enough left over for reservation[i].
#        row = [0] * n
#        for j in range(n):
#            # Sum of limit[j] for j != i
#            if j != i:
#                row[j] = 1
#
#        # ...is <= ub-reservations[i].
#        A_ub.append(row)
#        b_ub.append(ub-floor[i])
#
#    # Set the upper and lower bounds:
#    # (reservations[i] or fair share) <= x[i] <= ub
#    bounds = [(floor[i], ub) for i in range(n)]
#
#    result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds)
#    return result
