import os


def getAuthorizedKeys(user="paradrop"):
    homeDir = os.path.join("/home", user)
    if not os.path.isdir(homeDir):
        raise Exception("No home directory found for user {}".format(user))

    path = os.path.join(homeDir, ".ssh", "authorized_keys")
    if not os.path.isfile(path):
        return []

    keys = []
    with open(path, 'r') as source:
        for line in source:
            keys.append(line.strip())
    return keys


def writeAuthorizedKeys(keys, user="paradrop"):
    homeDir = os.path.join("/home", user)
    if not os.path.isdir(homeDir):
        raise Exception("No home directory found for user {}".format(user))

    sshDir = os.path.join(homeDir, ".ssh")
    if not os.path.exists(sshDir):
        os.mkdir(sshDir)

    path = os.path.join(sshDir, "authorized_keys")
    with open(path, "w") as output:
        for key in keys:
            output.write(key + "\n")


def addAuthorizedKey(key, user="paradrop"):
    keys = getAuthorizedKeys(user=user)

    for existing in keys:
        if key == existing:
            raise Exception("Key already exists")

    # One thing we avoid by rewriting the entire file is checking whether the
    # last line of the file had a newline or not.
    keys.append(key)
    writeAuthorizedKeys(keys, user=user)
