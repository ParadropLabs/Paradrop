"""
This module generates a Dockerfile for use with light chutes.
"""

import os
import platform
import re

import six

from io import BytesIO


from paradrop.lib.utils.template import TemplateFormatter


# Map requested image names to officially supported images in Docker Hub.
TARGET_IMAGE_MAP = {
    "go": "golang:1.11",
    "gradle": "gradle:4.2",
    "maven": "maven:3.5",
    "node": "node:8.13",
    "python2": "python:2.7",
    "python3": "python:3.7"
}


# Map machine names to officially supported architecture names in Docker Hub.
TARGET_MACHINE_MAP = {
    "armv7l": "arm32v7",
    "i486": "i386",
    "i586": "i386",
    "i686": "i386",
    "x86_64": "amd64"
}


def get_target_image(requested):
    if requested in TARGET_IMAGE_MAP:
        return TARGET_IMAGE_MAP[requested]
    else:
        return requested


def get_target_machine():
    machine = platform.machine()
    if machine in TARGET_MACHINE_MAP:
        return TARGET_MACHINE_MAP[machine]
    else:
        return machine


class Dockerfile(object):
    requiredFields = ["image", "command"]

    def __init__(self, service):
        """
        service: Service object containing configuration for the image.
        """
        self.service = service

    def getBytesIO(self):
        """
        Geterate a Dockerfile and return as a BytesIO object.
        """
        data = self.getString()
        return BytesIO(data.encode("utf-8"))

    def readTemplate(self, language):
        dirname = os.path.dirname(__file__)
        path = os.path.join(dirname, "templates/Dockerfile-{}.txt".format(language))

        if not os.path.isfile(path):
            raise Exception("No Dockerfile template for {}".format(language))

        with open(path, "r") as source:
            return source.read()

    def getString(self):
        """
        Generate a Dockerfile as a multi-line string.
        """
        # Required fields for generating Dockerfile.
        # Developer tells us what language pack to use and what command to run.
        language = self.service.image
        command = self.service.command

        # Extra build options.
        build = self.service.build
#        image_source = build.get("image_source", "paradrop")
#        image_version = build.get("image_version", "latest")
        packages = build.get("packages", [])

        as_root = self.service.requests.get("as-root", False)

        # Example base image: amd64/node:8.13
        from_image = "{}/{}".format(get_target_machine(),
                get_target_image(language))

        if isinstance(command, six.string_types):
            cmd_string = command
        elif isinstance(command, list):
            cmd_string = "[{}]".format(",".join(
                "\"{}\"".format(v) for v in command))
        else:
            raise Exception("command must be either a string or list of strings")

        template = self.readTemplate(language)
        formatter = TemplateFormatter()
        dockerfile = formatter.format(template,
                cmd=cmd_string,
                drop_root=not as_root,
                has_packages=len(packages) > 0,
                image=from_image,
                packages=" ".join(packages))

        return dockerfile

    def isValid(self):
        """
        Check if configuration is valid.

        Returns a tuple (True/False, None or str).
        """
        # Check required fields.
        for field in Dockerfile.requiredFields:
            if getattr(self.service, field, None) is None:
                return (False, "Missing required field {}".format(field))

        command = self.service.command
        if not isinstance(command, six.string_types + (list, )):
            return (False, "Command must be either a string or list of strings")

        packages = self.service.build.get("packages", [])
        if not isinstance(packages, list):
            return (False, "Packages must be specified as a list")
        for pkg in packages:
            if re.search(r"\s", pkg):
                return (False, "Package name ({}) contains whitespace".format(pkg))

        return (True, None)

    def writeFile(self, path):
        """
        Generate Dockerfile and write to a file.
        """
        data = self.getString()
        with open(path, "w") as output:
            output.write(data)
