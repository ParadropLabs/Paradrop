Provisioning Devices
====================================

Once you've got paradrop up and running on hardware or on a virtual machine you'll need to *provision* the software.
When a brand new router starts for the first time, it doesn't  have a place in the world yet. It doesn't 
even know its name! Additionally, the provisioning process secures your software to you and only you-- its 
an important security step.

The steps listed here are an intermediate process. Provisioning will occur during the installation process, check back
soon for updates. 

Provisioning Routers v0.1
++++++++++++++++++++++++++++

Before you begin, make sure you have an installed version of the CLI tools and an account with paradrop. You will
need to be logged in for every instruction that follows::

    pip install pdtools
    paradrop register

or if you already have pdtools installed::

    paradrop login

Please choose usernames and passwords that are at least 8 characters. 

Create a new router with the server. All of your routers have to have unique names, but
lets use aardvark::

    paradrop router-create aardvark

Once the creation process is finished see all of your owned chutes and routers with::

    paradrop list

If this is your first time, You'll only see your single new router as part of its ``pdid`` (Link forthcoming.)
This is the id of your router to the rest of the world::

    routers
        pd.joe.aardvark

At this point, however, that identity hasn't made it onto the router yet. When you used ``router-create`` to 
name your new router, the server transmitted a wealth of information. To get that information to the router you need to know the host and port of the device. When running locally, ::

    paradrop router-provision aardvark localhost 14231


To see the logs of your router while its running, try::

    paradrop logs aardvark

But be warned! Currently they'll only respond if the router is awake.