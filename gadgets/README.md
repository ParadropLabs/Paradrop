Gadgets
=======

Gadget snaps correspond to different hardware models. For example, we
could make a gadget snap specifically for Paradrop running on the APU2.
However, in many cases, we can get away with simply using a generic
amd64 gadget. For Paradrop, the real value of the gadget snap comes
from being able to declare automatic interface connections and initial
values for snap settings.  Automatically connecting interfaces means that
when the system boots for the first time, snaps will have appropriate
permissions set, and we do not need to login and run `snap connect`.
There is also the possibility of future support for disabling the first
boot console-conf, better device provisioning, and other features through
the gadget snap.

Building
--------

Gadget snaps are built using snapcraft.

    cd paradrop-amd64
    snapcraft
