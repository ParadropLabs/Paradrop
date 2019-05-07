Quick Start
========================

This section goes through the steps to create a ParaDrop account, activate a
ParaDrop node, and install a hello-world chute on the router.

If you have received a device with ParaDrop already installed, you can start
here. If you do not have a ParaDrop-enabled device, please visit the
:doc:`../device/index` section to learn about supported hardware or download
a virtual machine image.

Create a ParaDrop Account
-------------------------

With a free account on the ParaDrop cloud controller, users can manage
one or more ParaDrop nodes through a simple web interface.

1. Signup at https://paradrop.org/signup. You will receive a confirmation
   email from paradrop.org after you finish the signup.
2. Confirm your registration in the email.

Boot the ParaDrop Node
----------------------

Note: some of these steps are specific to the PC Engines APU/APU2 hardware.

1. Using an Ethernet cable, connect the WAN port of the ParaDrop router
   to a modem, switch, or other device with access to the Internet.
2. Connect the power supply. To avoid malfunctioning due to arcing, it is
   recommended to connect the barrel connector to DC jack on the back of the
   router first and connect the adapter to a power outlet second.
3. Allow the router 1-2 minutes to start up, especially on the first boot.
4. Connect a device (laptop, phone, etc.) either to one of the LAN ports on the
   back of the router or to its WiFi network. Typically, the router will be
   preconfigured with an open ESSID called "ParaDrop". If the WiFi network has
   a password, that information will be provided separately.

Activate a ParaDrop Node
------------------------

Activation associates the router with your account on `paradrop.org
<https://paradrop.org>`_ so that you can manage the router and chutes through
the cloud controller. Starting with version 0.13, ParaDrop nodes in most cases
will automatically configure themselves to connect to the cloud controller.

1. Open the node administration panel at http://<node_ip_address>.
   Alternatively, you can open `http://paradrop.io`_ if your device is
   connected to the LAN port of the node or its WiFi network.  You may
   be prompted for a username and password. The default username is
   "paradrop" with an empty password. If a password was configured by
   default, you will have received information about the password with
   the device.
2. Starting with version 0.13, ParaDrop nodes will in most cases
   automatically configure themselves to communicate with the cloud
   controller. In that case, you will see checkmarks appear on the
   "WAMP Router" and "ParaDrop Server" lines of the landing page. Click
   the "View the router on paradrop.org" button to transfer ownership
   of the node to your account on paradrop.org. You may be prompted to
   log in with your ParaDrop account. If checkmarks did not appear
   on the landing page, or you were not able to claim the node,
   proceed to steps 3-6. Otherwise, your node is activated.
3. Navigate to the `Routers List <https://paradrop.org/routers>`_
   page. If your router came with a Claim Token, enter that here and skip
   steps 3-5. Otherwise if you do not have a Claim Token, click Create
   Router. Give your router a unique name and an optional location and
   description to help you remember it and click Submit.
4. On the router page, find the "Router ID" and "Password" fields. You will
   need to copy this information to the router so that it can connect to the
   controller.
5. On the router admin panel (http://<router_ip_address> or `http://paradrop.io`_),
   click the button "Activate the router with a ParaDrop Router ID" or
   "Activate the router with another ParaDrop Router ID" and enter the
   information from the paradrop.org router page. If the activation was
   successful, you should see checkmarks appear on the "WAMP Router"
   and "ParaDrop Server" lines. You may need to refresh the page to see
   the change.
6. After you activate your router, you will see the router status is online at
   https://paradrop.org/routers.

Install a hello-world Chute
---------------------------

1. Make sure you have an activated, online router.
2. Go to the `Chute Store <https://paradrop.org/chutes>`_ page on
   paradrop.org. There you will find some public
   chutes such as the hello-world chute.  You can also create your own
   chutes here.
3. Click on the hello-world chute,  click Install, click your router's name to
   select it, and finally, click Install.
4. That will take you to the router page again where you can click the update
   item to monitor its progress. When the installation is complete, an entry
   will appear under the Chutes list.
5. The hello-world chute starts a webserver, which is accessible at
   http://<router-ip-address>/chutes/hello-world. Once the installation is
   complete, test it in a web browser.
