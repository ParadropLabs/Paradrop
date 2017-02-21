"""
Utilities for reading from data structures.
"""

def getValue(struct, path, default=None):
    """
    Read a value from the data structure.

    Arguments:
    struct can comprise one or more levels of dicts and lists.
    path should be a string using dots to separate levels.
    default will be returned if the path cannot be traced.

    Example:
    getValue({'a': [1, 2, 3]}, "a.1") -> 2
    getValue({'a': [1, 2, 3]}, "a.3") -> None
    """
    parts = path.split(".")

    try:
        current = struct
        for part in parts:
            if isinstance(current, list):
                part = int(part)
            current = current[part]
        return current
    except:
        return default
