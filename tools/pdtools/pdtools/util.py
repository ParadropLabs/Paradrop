def update_object(obj, path, callback=None):
    """
    Traverse a data structure ensuring all nodes exist.

    obj: expected to be a dictionary
    path: string with dot-separated path components
    callback: optional callback function (described below)

    When update_object reaches the parent of the leaf node, it calls the
    optional callback function. The arguments to the callback function are:

    - parent: dictionary containing the leaf node
    - key: string key for the leaf node in parent
    - created: boolean flag indicating whether any part of the path, including
        the leaf node needed to be created.

    If the callback function is None, update_object will still ensure that all
    components along the path exist. If the leaf needs to be created, it will
    be created as an empty dictionary.

    Example:
    update_object({}, 'foo.bar') -> {'foo': {'bar': {}}}

    Return value: Returns either the return value of callback, or if callback
    is None, returns the value of the leaf node.
    """
    parts = path.split(".")

    current = obj
    parent = obj
    created = False
    for part in parts:
        if len(part) == 0:
            raise Exception("Path ({}) is invalid".format(path))

        if not isinstance(current, dict):
            raise Exception("Cannot set {}, not a dictionary".format(path))

        # Create dictionaries along the way if path nodes do not exist,
        # but make note of the fact that the previous value did not exist.
        if part not in current:
            current[part] = {}
            created = True

        parent = current
        current = parent[part]

    if callback is not None:
        return callback(parent, parts[-1], created)
    else:
        return current
