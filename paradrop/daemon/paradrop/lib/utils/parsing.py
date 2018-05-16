def str_to_numeric(s):
    """
    Convert a string to a numeric type.

    Returns either an int or a float depending on the apparent type of the
    string.
    """
    try:
        return int(s)
    except ValueError:
        return float(s)
