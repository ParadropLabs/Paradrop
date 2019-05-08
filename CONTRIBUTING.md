# Contributing to Paradrop

Thank you for your interest in contributing to the Paradrop project.
Since Paradrop has its roots in university research, we are strong
proponents of open sharing and application of knowledge. However, we are
also a very small team, which makes it difficult to accomplish everything
in our vision for Paradrop. Welcome!

## Questions

Please do not file an issue to ask a question. You will receive a
faster response by contacting the Paradrop team directly via email at
<info@paradrop.io>.

As the community grows, we plan to set up a message board for users
and developers to share their questions and ideas publicly.

## Project Structure

The main source code repository (this one) contains the Paradrop daemon
written in Python and the tool set, pdtools, which doubles as both
a command line utility and a library for Python applications to access
the Paradrop API.

For distribution, the Paradrop daemon is built into a snap package to
run on lightweight edge devices running Ubuntu Core. We also build a
Docker image for general use in development environments and servers.
The pdtools module is distributed via PyPi for use on developer machines
and in applications.

There are various other source code repositories related to Paradrop.
These are largely either applications that run on a Paradrop node,
called *chutes* or add-ons that provide additional functionality.
The chutes that we have developed as examples are listed in README.md.
Many chutes are available for easy installation from the [Paradrop Chute
Store](https://paradrop.org/chutes), and some of the flashier chutes
are featured prominently on the [Paradrop homepage](https://paradrop.org).

Here are a few add-ons that extend the capabilities of the Paradrop
platform.  These are all distributed as snaps that can be installed
as needed.

* [governor](https://github.com/ParadropLabs/governor)
  Governor provides access to a few privileged operations on a Snap-based
  system such as reading and writing SSH authorized keys and managing
  installed snaps. Moving these functions out of the Paradrop daemon
  made it easier for us to distribute Paradrop in the Snap store.
* [paradrop-imserve](https://github.com/ParadropLabs/paradrop-imserve)
  The image server acts as a virtual camera by serving images in a
  sequence from an image repository. We use this for developing and
  developing computer vision applications when it would be inconvenient
  to connect a physical camera.
* [paradrop-voice](https://github.com/ParadropLabs/paradrop-voice)
  This module provides text-to-speech and speech recognition
  capabilities. It can be used to detect command words, or it can play
  a prompt and listen for the user's response. This add-on requires
  hardware support for audio.

## How to Contribute

If you have found a bug or want to submit
a feature request, please use the GitHub [issue
tracker](https://github.com/ParadropLabs/Paradrop/issues) for the
Paradrop project.

If you have built an interesting edge computing application, please
let us know so we can feature it on the Paradrop
[homepage](https://paradrop.org).

We welcome pull requests that fix defects or implement new features.
Please make sure your commits are atomic (one bug fix or feature per
commit) and follow our coding conventions. For large changes, we recommend
opening an issue and soliciting feedback from the Paradrop team before
beginning work.  That will help ensure your pull request can be accepted.

## Coding Conventions

### Python

* We use four spaces for indentation.
* When in doubt, follow [PEP 8](https://www.python.org/dev/peps/pep-0008/).

### Git Commit Messages

* Use the present tense ("Add template" instead of "Added template").
* Use the imperative mood ("Update dependencies" instead of "Updates dependencies").
* Limit the first line to 72 characters.
* Reference issues and pull requests if relevant.
