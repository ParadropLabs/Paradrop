"""
This file contains constants that may be used safely throughout the
code.  Although Python does not have any native mechanisms for enforcing
read-only variables, a violation of this convention would be easy enough
to spot.

    # Please do not do this.
    from paradrop.base import constants
    constants.IMPORTANT_CONSTANT = "boo"

Some of these variables were moved from paradrop.base.settings in an
effort to clean up that module when it became clear that there were two
types of variables in that module, variables that could reasonably be
considered settings for a user or administrator, and variables that were
actually intended to be constants.

When considering whether to put a new variable here or in the settings
module, consider the following factors:

    1. If a user were to change this setting on a running system, would
    it result in unexpected or undefined behavior?

    2. Should changing the value of this variable be subject to a
    version-controlled code change.

    3. Would an advanced user or administrator have a use case for
    changing this variable?

As an example of something that needs to be a constant, consider
the reserved chute name, RESERVED_CHUTE_NAME, which is used to mark
settings in UCI files as belonging to the system rather than a chute.
If someone were to change this value on a running system, the resulting
behavior would be undefined, so this value belongs in constants rather
than settings.
"""

# Name of section in the settings file for paradrop.base.settings values.
BASE_SETTINGS_SECTION = "base"

# Space-separated list of features that will be passed to chutes through
# environment variable or API call. This allows chutes to check the features of
# the host on which they are running. Update this when significant features are
# added.
DAEMON_FEATURES = "audio hostapd-control"

# Character limit for network interface names. The limit is imposed by the
# operating system.
MAX_INTERFACE_NAME_LEN = 15

# This is not actually a chute, but a reserved name that is used to mark
# settings and changes that belong to the system rather than a chute.
RESERVED_CHUTE_NAME = "__PARADROP__"

# Name of settings file used by paradrop.base.settings.
SETTINGS_FILE_NAME = "settings.ini"
