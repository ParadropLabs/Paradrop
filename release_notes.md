Release notes for 0.1 (August 14, 2015)
--------------------------------------

Features with this release:
* Applications ("chutes") can be deployed in Docker containers with a configurable network setup.
* A command line utility (pdtools) can install, start, stop, and delete chutes.
* pdtools can also fetch logs from chute operations.
* New chutes are created by writing a YAML configuration file ([examples](https://github.com/ParadropLabs/Example-Apps)).
* Chutes can bring up one or more WiFi ESSIDs, which include a DHCP server and optional DNS overrides.
* Running chutes persist after rebooting the device including their networking configuration.
* Our build script (pdbuild.sh) sets up everything needed to start developing for Paradrop under a virtual machine.
* Build tools are fully supported for Ubuntu 14.04 and up.

Known issues:
* Installing Instance Tools using _pdbuild.sh install_ many times may cause the filesystem to fill up, simple solution [here](https://github.com/ParadropLabs/Paradrop/issues/4).

Features planned for the next release:
* Vagrant for virtual machine development testing to be cross-platform.
* Full support for Paradrop to configure instance as a real usable Wi-Fi router.
* Full support running on ARM architecture.
* Host level architectural support for more advanced configuration and networking.
* Grouping capabilities for sets of instances to work together.
