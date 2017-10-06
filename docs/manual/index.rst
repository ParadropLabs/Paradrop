Get Started
========================

This section goes through the steps to create a ParaDrop account, activate a ParaDrop router,
and install a hello-world chute on the router.

Create a ParaDrop account
--------------------------
With a ParaDrop account, users can manage the resources of ParaDrop through a web frontend.

1. Signup at https://www.paradrop.org/signup. You will receive a confirmation email from paradrop.org after you finish the signup.
2. Confirm your registration in the email.

Activate a ParaDrop router
---------------------------
Activation associates the router with your account on
`paradrop.org <https://paradrop.org>`_ so that you can manage the router and chutes through a web frontend.

1. Login to `paradrop.org <https://paradrop.org>`_ if you do not.
2. From the Routers tab, click Create Router. Give your router a unique name and an optional description to help you remember it and click Submit.
3. On the router page, find the "Router ID" and "Password" fields. You will need to copy this information to the router so that it can connect.
4. Open the router portal at http://<router_ip_address> (or http://home.paradrop.org if you are connected to the LAN port of the router or WiFi network). You may be prompted for a username and password. The default login is "paradrop" with an empty password.
5. Click the "Activate the router with a ParaDrop Router ID" button and enter the information from the paradrop.org router page. If the activation was successful, you should see checkmarks appear on the "WAMP Router" and "ParaDrop Server" lines. You may need to refresh the page to see the update.
6. After you activate your router, you will see the router status is online at https://paradrop.org/routers.


Install a hello-world chute
----------------------------
1. Make sure you have an activated, online router.
2. Go to the Chute Store tab on paradrop.org. There you will find some public chutes such as the hello-world chute.  You can also create your own chutes here.
3. Click on the hello-world chute,  click Install, click your router's name to select it, and finally, click Install.
4. That will take you to the router page again where you can click the update item to monitor its progress. When the installation is complete, an entry will appear under the Chutes list.
5. The hello-world chute starts a webserver, which is accessible at http://<router-ip-address>/chutes/hello-world. Once the installation is complete, test it in a web browser.
