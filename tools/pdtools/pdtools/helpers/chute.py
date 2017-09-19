import re

from six.moves import input


def get_name():
    print("")
    print("Chute Name")
    print("")
    print("This name will be used on the router status page and chute store.")
    print("Please use only lowercase letters, numbers, and hypens.")
    print("")
    while True:
        name = input("name: ")
        if len(name) == 0:
            continue

        match = re.match("[a-z][a-z0-9\-]*", name)
        if match is None:
            print("The name does not meet Paradrop's requirements for chute names.")
            print("Please use only lowercase letters, numbers, and hypens.")
            continue

        return name


def get_description():
    print("")
    print("Chute Description")
    print("")
    print("Enter a description for the chute. This will be displayed in")
    print("the chute store.")
    print("")
    while True:
        desc = input("description: ")
        if len(desc) == 0:
            continue

        return desc


def get_chute_type():
    print("")
    print("Chute Type")
    print("")
    print("Paradrop has two types of chutes. Light chutes are based on a base")
    print("image that is optimized for a particular language such as Python or")
    print("JavaScript and use the language-specific package manager (pip or npm)")
    print("to install dependencies. Normal chutes give you more flexibility to")
    print("install dependencies but require that you write your own Dockerfile.")
    print("")
    print("Valid types: light, normal")
    valid = set(["light", "normal"])
    while True:
        ctype = input("type [normal]: ").lower()
        if len(ctype) == 0:
            ctype = "normal"

        if ctype not in valid:
            print("Valid types: light, normal")
            continue

        return ctype


def get_base_name():
    print("")
    print("Base Image Name")
    print("")
    print("Enter the name of the base image to use. This depends on the")
    print("programming language that you intend to use.")
    print("")
    print("Valid choices: node, python2")
    valid = set(["node", "python2"])
    while True:
        name = input("image [python2]: ").lower()
        if len(name) == 0:
            name = "python2"

        if name not in valid:
            print("Valid choices: node, python2")
            continue

        return name


def get_command(use=None):
    print("")
    print("Entry Point")
    print("")
    print("This is the entry point of your application. Paradrop will run this")
    print("file when it starts your chute.")
    print("")

    default = None
    if use == "node":
        default = "index.js"
    elif use == "python2":
        default = "main.py"

    entry = input("entry point [{}]: ".format(default))
    if len(entry) == 0:
        entry = default

    parts = []
    if use == "node":
        parts.append("node")

    elif use == "python2":
        parts.append("python2")

        # Unbuffered output is preferred for streaming log messages.
        parts.append("-u")

    parts.append(entry)

    # If the entrypoint contains a space, we will need to use the array form
    # for specifying the command.
    use_array = (" " in entry)

    if use_array:
        return parts
    else:
        return " ".join(parts)


def build_chute():
    chute = {
        'version': 1,
        'config': {}
    }

    chute['name'] = get_name()
    chute['description'] = get_description()
    chute['type'] = get_chute_type()

    if chute['type'] == "light":
        chute['use'] = get_base_name()
        chute['command'] = get_command(use=chute['use'])

    return chute
