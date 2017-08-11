Overview
=================

This section introduces the background and motivation of ParaDrop.

Cloud computing vs. edge computing?
------------------------------------
Cloud computing platforms, such as Amazon EC2, Microsoft Azure and Google App Engine have become a popular
approach to provide ubiquitous access to services across different user devices.
Cloud computing is beneficial for infrastructure providers, service providers,and users.
Infrastructure providers, i.e., cloud platform providers, take advantage of the economies of scale by
managing and operating resources in a centralized manner.
Cloud computing also provides reliable, scalable, and elastic resources to service providers.
In addition, end users can access high-performance computing and large storage resources anywhere with Internet access at anytime thanks for the cloud computing.

Cloud services require developers to host services, applications, and data on off-site data centers.
That means the computing and storage resources are spatially distant from end-users’ devices.
However, a growing number of high-quality services desire computational tasks to be located nearby.
These services desire for lower latency, greater responsiveness, a better end-user experience,
and more efficient use of network bandwidth.

ParaDrop is a research effort to build an edge computing platform.
The service deployment process of ParaDrop is like "paradrop" some resources from military bases into the battlefields on-demand.
In terms of ParaDrop, users can "paradrop" edge computing services (chutes, short of parachutes) from the cloud on-demand.
And the whole process is transparent to end users.
Based on previous research work on exploring advantages of edge computing,
we focus on building a user-friendly edge computing platform for both normal users and developers.

Where is the vantage point for edge computing?
------------------------------------------------
There are various options to place edge computing nodes.
ParaDrop chooses to place the edge computing substrate in the WiFi access points (APs).
The WiFi AP is a unique platform for edge computing because of multiple reasons:
it is ubiquitous in homes and enterprises,
is always “on” and available,
and sits directly in the data path between Internet resources and the end device.

How to design an efficient, effective, and flexible edge computing platform?
------------------------------------------------------------------------------
ParaDrop provides a similar runtime environment as the cloud computing to developers,
so that developers can easily port some parts of their services from the cloud to the ParaDrop
to take advantages of edge computing.
Through a lightweight virtualization technique based on docker,
ParaDrop provides a flexible environment for developers to build edge computing services with the programming languages,
libraries, and frameworks they prefer.
ParaDrop offers a well-defined API, that developers can leverage to implement and deploy edge computing
services transparent to end users.
