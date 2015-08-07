Release notes for 0.1 (August 7, 2015)
--------------------------------------

Features with this release:
* Applications ("chutes") can be deployed in Docker containers with a configurable network setup.
* A command line utility (pdtools) can install, start, stop, and delete chutes.
* pdtools can also fetch logs from chute operations.
* New chutes are created by writing a YAML configuration file (examples available).
* Chutes can bring up one or more WiFi ESSIDs, which include a DHCP server and optional DNS overrides.
* Networking options available to chutes are a WAN (virtual eth0) interface, which is provided to all chutes by default, and creation of WiFi APs.
* Running chutes persist after rebooting the device including their networking configuration.
* Our build script (pdbuild.sh) sets up everything needed to start developing for Paradrop under a virtual machine.  This functionality is supported for Ubuntu 14.04 and up.

Features planned for the next release:
* Support running on ARM architecture.
* Support connecting chutes to wired LAN.
* Connect to a web service that allows starting and stopping chutes from the browser.

