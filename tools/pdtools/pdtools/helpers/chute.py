import os
import re

from six.moves import input


SUPPORTED_BASE_IMAGES = set([
    "go",
    "gradle",
    "maven",
    "node",
    "python2"
])


def get_name():
    print("")
    print("Chute Name")
    print("")
    print("This name will be used on the router status page and chute store.")
    print("Please use only lowercase letters, numbers, and hypens.")
    print("")

    # Guess the project name based on the directory we are in.
    default_name = os.path.basename(os.getcwd())

    while True:
        name = input("name [{}]: ".format(default_name))
        if len(name) == 0:
            name = default_name

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
    print("Valid choices: " + ", ".join(SUPPORTED_BASE_IMAGES))
    while True:
        name = input("image [python2]: ").lower()
        if len(name) == 0:
            name = "python2"

        if name not in SUPPORTED_BASE_IMAGES:
            print("Valid choices: " + ", ".join(SUPPORTED_BASE_IMAGES))
            continue

        return name


def get_command(name="my-app", use=None):
    print("")
    print("Command")
    print("")
    print("This is the command to start your application.")

    default = None
    if use == "go":
        print("For Go applications, it is highly recommended that you use the default.")
        default = "app"
    elif use == "gradle":
        print("For Java applications, you can accept the default and update")
        print("paradrop.yaml after you have decided on the structure of your project.")
        default = "java -cp build/libs/gradle-{name}-1.0-SNAPSHOT.jar com.mycompany.{name}.Main".format(name=name)
    elif use == "maven":
        print("For Java applications, you can accept the default and update")
        print("paradrop.yaml after you have decided on the structure of your project.")
        default = "java -cp target/{name}-1.0-SNAPSHOT.jar com.mycompany.{name}.Main".format(name=name)
    elif use == "node":
        default = "node index.js"
    elif use == "python2":
        default = "python2 -u main.py"
    else:
        default = ""
    print("")

    entry = input("command [{}]: ".format(default))
    if len(entry) == 0:
        entry = default

    return entry


def build_chute():
    main = {}

    chute = {
        'version': 1,
        'services': {
            'main': main
        }
    }

    chute['name'] = get_name()
    chute['description'] = get_description()

    main['type'] = get_chute_type()
    main['source'] = "."

    if main['type'] == "light":
        main['image'] = get_base_name()
        main['command'] = get_command(name=chute['name'], use=main['image'])

    return chute


def build_legacy_chute():
    chute = {
        'version': 1,
        'config': {}
    }

    chute['name'] = get_name()
    chute['description'] = get_description()
    chute['type'] = get_chute_type()

    if chute['type'] == "light":
        chute['use'] = get_base_name()
        chute['command'] = get_command(name=chute['name'], use=chute['use'])

    return chute
