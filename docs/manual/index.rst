Quick Start
========================

This section goes through the steps to create a ParaDrop account, activate a
ParaDrop router, and install a hello-world chute on the router.

If you have received a device with ParaDrop already installed, you can start
here. If you do not have a ParaDrop-enabled device, please visit the
:doc:`../device/index` section.

Create a ParaDrop account
--------------------------

With a ParaDrop account, users can manage the resources of ParaDrop through a
web frontend.

1. Signup at https://paradrop.org/signup. You will receive a confirmation
   email from paradrop.org after you finish the signup.
2. Confirm your registration in the email.

Boot the router
--------------------

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

Activate a ParaDrop router
---------------------------

Activation associates the router with your account on `paradrop.org
<https://paradrop.org>`_ so that you can manage the router and chutes through
the cloud controller.

1. Login to `paradrop.org <https://paradrop.org>`_.
2. Navigate to the Routers List page. If your router came with a Claim Token,
   enter that here and skip steps 3-5. Otherwise if you do not have a Claim
   Token, click Create Router. Give your router a unique name and an optional
   description to help you remember it and click Submit.
3. On the router page, find the "Router ID" and "Password" fields. You will
   need to copy this information to the router so that it can connect to the
   controller.
4. Open the router portal at http://<router_ip_address> (or http://paradrop.io
   if you are connected to the LAN port of the router or its WiFi network). You
   may be prompted for a username and password. The default login is "paradrop"
   with an empty password.
5. Click the "Activate the router with a ParaDrop Router ID" button and enter
   the information from the paradrop.org router page. If the activation was
   successful, you should see checkmarks appear on the "WAMP Router" and
   "ParaDrop Server" lines. You may need to refresh the page to see the update.
6. After you activate your router, you will see the router status is online at
   https://paradrop.org/routers.

Install a hello-world chute
----------------------------

1. Make sure you have an activated, online router.
2. Go to the Chute Store tab on paradrop.org. There you will find some public
   chutes such as the hello-world chute.  You can also create your own chutes
   here.
3. Click on the hello-world chute,  click Install, click your router's name to
   select it, and finally, click Install.
4. That will take you to the router page again where you can click the update
   item to monitor its progress. When the installation is complete, an entry
   will appear under the Chutes list.
5. The hello-world chute starts a webserver, which is accessible at
   http://<router-ip-address>/chutes/hello-world. Once the installation is
   complete, test it in a web browser.
