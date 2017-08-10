Snappy Confinement
==================

Snappy confines running applications in two ways: directory isolation
and mandatory access control (MAC). Directory isolation means the
application cannot leave its installed directory. MAC means the
application cannot execute any system commands or access any files it
does not have explicit, predetermined permissions to.

MAC is the more serious hurdle for paradrop development. Snaps declare permissions through an `AppArmor profile <https://wiki.ubuntu.com/AppArmor>`_.

Getting started with Profile Generation
---------------------------------------

Install tools and profiles::

    sudo apt-get install apparmor-profiles apparmor-utils

List active profiles::

    sudo apparmor_status

Profiles in complain mode log behavior, while those in enforce mode actively restrict it.

The following steps assume paradrop is installed on the system and not on a virtualenv.

Create a new, blank profile::

    cd /etc/apparmor.d/
    sudo aa-autodep paradrop

Use aa-complain to put the profile in complain mode::

    sudo aa-complain paradrop

Excercise the application! AppArmor will surreptitiously watch the program in the background and log all behavior. Once finished, use the following command to go through the resulting requests, approve or deny them, and autogenerate a profile::

    sudo aa-logprof

