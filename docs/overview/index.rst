Introduction
=================

ParaDrop is a platform for edge computing. This is best understood by
comparison with the popular paradigm of cloud computing.

Cloud computing vs. edge computing
------------------------------------

Cloud computing platforms such as Amazon EC2, Microsoft Azure, and Google Cloud
Platform have grown in popularity as solutions for providing ubiquitous access
to services across different user devices.  Cloud computing has benefits for
infrastructure providers, service providers, and end users.  Infrastructure
providers, i.e., cloud platform providers, take advantage of the economies of
scale by managing and operating resources in a centralized manner.  Cloud
computing also provides reliable, scalable, and elastic resources to service
providers.  In addition, end users can access high-performance computing and
large storage resources anywhere with Internet access at any time thanks to the
cloud computing.

Despite all of the benefits of cloud computing, there are some inherent
trade-offs to the approach. Cloud computing requires developers to host
services and data on off-site data centers.  That means that the computing and
storage resources are spatially distant from end-users and out of their
control, which raises issues related to network latency, security, and privacy.
A growing number of high-quality services can benefit from computational tasks
running closer to end-users, especially within their own home or office.  By
moving the computation closer to the users, at the edge of the network,
services can take advantage of the lower latency to provide better
responsiveness and user experience as well as conserve network bandwidth.

Where is the vantage point for edge computing?
------------------------------------------------

There are various options for placing edge computing nodes within the
network.  Hosting options include dedicated compute nodes in the home
or office or on server racks within the ISP network.  ParaDrop takes the
approach of placing the edge computing substrate within the WiFi access
points (APs). The WiFi AP is uniquely suitable for edge computing for
multiple reasons:

- WiFi APs are ubiquitous in homes and businesses and inexpensive to replace.
- WiFi APs are always on and available.
- WiFi APs reside directly on the data path between Internet services and end
  users.

How does it work?
-------------------------------------------------

ParaDrop is a research effort to build a highly programmable edge computing
platform.  The name for the project draws inspiration from the military use
case of airdropping resources into the battlefield wherever they are needed
most. Similarly, ParaDrop enables users and developers to *paradrop* edge
services into the edge of the network as needed. Based on previous research
work exploring the advantages of edge computing, we focus on building a
platform that is friendly to both users and developers alike.

ParaDrop provides a similar runtime environment as the cloud computing platform
to developers so that developers can easily port their services from the cloud
to ParaDrop in part or in whole. It does this through lightweight
containerization powered by Docker, which is already immensely popular in the
cloud computing space. Containers allow developers the flexibility to build
services with the programming languages, libraries, and frameworks they prefer,
while being less resource-intensive than virtual machines. On top of that,
ParaDrop offers a well-defined API that developers can leverage to implement
and deploy interesting capabilities that are only available at the edge.
