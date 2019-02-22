###################################################################
# Copyright 2013-2014 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

import errno
import os
import subprocess
import shutil

import six

from distutils import dir_util

# We have to import this for the decorator
from paradrop.base.output import out


# protect the original open function
__open = open

# Since we overwrite everything else, do the same to basename
basename = lambda x: os.path.basename(x)

def getMountCmd():
    return "mount"


def isMount(mnt):
    """This function checks if @mnt is actually mounted."""
    # TODO - need to check if partition and mount match the expected??
    return os.path.ismount(mnt)


def oscall(cmd, get=False):
    """
    This function performs a OS subprocess call.
    All output is thrown away unless an error has occured or if @get is True
    Arguments:
        @cmd: the string command to run
        [get] : True means return (stdout, stderr)
    Returns:
        None if not @get and no error
        (stdout, retcode, stderr) if @get or yes error
    """
    # Since we are already in a deferred chain, use subprocess to block and make the call to mount right HERE AND NOW
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, errors = proc.communicate()
    if(proc.returncode or get):
        return (output, proc.returncode, errors)
    else:
        if(output and output != ""):
            out.verbose('"%s" stdout: "%s"\n' % (cmd, output.rstrip()))
        if(errors and errors != ""):
            out.verbose('"%s" stderr: "%s"\n' % (cmd, errors.rstrip()))
        return None


def getFileType(f):
    if not exists(f):
        return None
    r = oscall('file "%s"' % f, True)
    if(r is not None and isinstance(r, tuple)):
        return r[0]
    else: # pragma: no cover
        return None


def exists(p):
    return os.path.exists(p)


def listdir(p):
    return os.listdir(p)


def unlink(p):
    return os.unlink(p)


def mkdir(p):
    return os.mkdir(p)


def symlink(a, b):
    return os.symlink(a, b)


def ismount(p):
    return os.path.ismount(p)


def fixpath(p):
    """This function is required because if we need to pass a path to something like tarfile,
        we cannot overwrite the function to fix the path, so we need to expose it somehow."""
    return p


def copy(a, b):
    return shutil.copy(a, b)


def move(a, b):
    return shutil.move(a, b)


def remove(path, suppressNotFound=False):
    if (isdir(path)):
        return shutil.rmtree(path)
    else:
        try:
            os.remove(path)
        except OSError as err:
            # Suppress the exception if it is a file not found error and the
            # suppressNotFound flag is set.  Otherwise, re-raise the exception.
            if not suppressNotFound or err.errno != errno.ENOENT:
                raise


def isdir(a):
    return os.path.isdir(a)


def isfile(a):
    return os.path.isfile(a)


def copytree(a, b):
    """shutil's copytree is dumb so use distutils."""
    return dir_util.copy_tree(a, b)


def open(p, mode):
    return __open(p, mode)


def writeFile(filename, line, mode="a"):
    """Adds the following cfg (either str or list(str)) to this Chute's current
        config file (just stored locally, not written to file."""
    try:
        if isinstance(line, list):
            data = "\n".join(line) + "\n"
        elif isinstance(line, six.string_types):
            data = "%s\n" % line
        else:
            out.err("Bad line provided for %s\n" % filename)
            return
        fd = open(filename, mode)
        fd.write(data)
        fd.flush()
        fd.close()

    except Exception as e:
        out.err('Unable to write file: %s\n' % (str(e)))


def write(filename, data, mode="w"):
    """ Writes out a config file to the specified location.
    """
    try:
        fd = open(filename, mode)
        fd.write(data)
        fd.flush()
        fd.close()
    except Exception as e:
        out.err('Unable to write to file: %s\n' % str(e))


def readFile(filename, array=True, delimiter="\n"):
    """
        Reads in a file, the contents is NOT expected to be binary.
        Arguments:
            @filename: absolute path to file
            @array : optional: return as array if true, return as string if False
            @delimiter: optional: if returning as a string, this str specifies what to use to join the lines

        Returns:
            A list of strings, separated by newlines
            None: if the file doesn't exist
    """
    if(not exists(filename)):
        return None

    lines = []
    with open(filename, 'r') as fd:
        while(True):
            line = fd.readline()
            if(not line):
                break
            lines.append(line.rstrip())
    if(array is True):
        return lines
    else:
        return delimiter.join(lines)


def read_sys_file(path, default=None):
    """
    Read a file and return the contents as a string.

    This is best suited for files that store a single line of text such as
    files in /sys/.

    Returns the default value if an error occurs.
    """
    try:
        with open(path, 'r') as source:
            return source.read().strip()
    except:
        return default
