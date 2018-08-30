import getpass
import os
import tempfile

import builtins
import yaml


LOCAL_DEFAULT_USERNAME = "paradrop"
LOCAL_DEFAULT_PASSWORD = ""


def format_result(data):
    """
    Format a result from an API call for printing.
    """
    if data is None or data == []:
        return ""
    return yaml.safe_dump(data, default_flow_style=False)


def open_text_editor(data):
    if data is None:
        data = ""

    fd, path = tempfile.mkstemp()
    os.close(fd)

    with open(path, 'w') as output:
        output.write(data)

    # Get modified time before calling editor.
    orig_mtime = os.path.getmtime(path)

    editor = os.environ.get("EDITOR", "vim")
    os.spawnvpe(os.P_WAIT, editor, [editor, path], os.environ)

    with open(path, 'r') as source:
        data = source.read()

    # Check if the file has been modified, and if it has, send the update.
    new_mtime = os.path.getmtime(path)
    if new_mtime == orig_mtime:
        data = None

    os.remove(path)
    return data


def open_yaml_editor(data, description):
    if data is None:
        data = {}

    fd, path = tempfile.mkstemp()
    os.close(fd)

    with open(path, 'w') as output:
        if len(data) > 0:
            output.write(yaml.safe_dump(data, default_flow_style=False))
        output.write("\n")
        output.write("# You are editing the configuration for the {}.\n".format(description))
        output.write("# Blank lines and lines starting with '#' will be ignored.\n")
        output.write("# Save and exit to apply changes; exit without saving to discard.\n")

    # Get modified time before calling editor.
    orig_mtime = os.path.getmtime(path)

    editor = os.environ.get("EDITOR", "vim")
    os.spawnvpe(os.P_WAIT, editor, [editor, path], os.environ)

    with open(path, 'r') as source:
        data = source.read()
        new_data = yaml.safe_load(data)

    # If result is null, convert to an empty dict before sending to router.
    if new_data is None:
        new_data = {}

    # Check if the file has been modified.
    new_mtime = os.path.getmtime(path)
    changed = (new_mtime != orig_mtime)

    os.remove(path)
    return new_data, changed


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


class LoginGatherer(object):
    """
    LoginGatherer is an iterator that produces username/password tuples.

    On the first iteration, it returns a default username/password combination
    for convenience. On subsequent iterations, it prompts the user for input.

    The class method prompt() can be used directly in a loop for situations
    where the default is not desired.

    Usage examples:

    for username, password in LoginGatherer(netloc):
        ...

    while True:
        username, password = LoginGatherer.prompt(netloc)
    """
    def __init__(self, netloc):
        self.first = True
        self.netloc = netloc

    def __iter__(self):
        self.first = True
        return self

    def __next__(self):
        if self.first:
            self.first = False
            return (LOCAL_DEFAULT_USERNAME, LOCAL_DEFAULT_PASSWORD)
        else:
            return LoginGatherer.prompt(self.netloc)

    def next(self):
        """
        Get the next username and password pair.
        """
        return self.__next__()

    @classmethod
    def prompt(cls, netloc):
        """
        Prompt the user to enter a username and password.

        The netloc argument is presented in the prompt, so that the user knows
        the relevant authentication domain.
        """
        print("Please enter your username and password for {}."
              .format(netloc))
        username = builtins.input("Username: ")
        password = getpass.getpass("Password: ")
        return (username, password)
