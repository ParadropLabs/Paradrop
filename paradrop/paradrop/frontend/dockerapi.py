import docker
from docker import Client
import json

##########################################################################
# docker-py wrapper functions
##########################################################################

def launchApp(path=None, name=None, port_bindings=None, restart_policy=None, fileobj=None):
    """
    This function builds a docker image then creates a container and starts it. 

    :param path: The absolute path to the dockerfile on the host (either path or fileobj must exist but not both).
    :type path: str.
    :param fileobj:  A file object to use as the Dockerfile. (Or a file-like object)
    :type fileobj: file.
    :param name: The name to use for the docker repo (should be unique).
    :type name: str.
    :param port_bindings: (Optional)Port bindings between host and container. i.e. { 80: 9000 }
    :type port_bindings: dict.
    :param restart_policy: (Optional)A dict representing restart policy.
    where "Name" must be one of ['on-failure', always] and "MaximumRetryCount" is an int
    i.e. {"MaximumRetryCount": 0, "Name": "always"}
    :type restart_policy: dict.
    :returns: (str) The Id for the running container.
    """
    c = Client(base_url='unix://var/run/docker.sock')
    name += ":latest"
    for line in c.build(fileobj=fileobj, rm=True, tag=name, path=path):
        for key, value in json.loads(line).iteritems():
            if (key == "stream"): 
                print value,
            elif (isinstance(value, dict)):
                continue
            else:
                print value
    container = c.create_container(
        image=name, 
        host_config=docker.utils.create_host_config(
            port_bindings = port_bindings,
            restart_policy = restart_policy
        )
    )
    print(str(container.get('Id')))
    c.start(container.get('Id'))
    return str(container.get('Id'))

def stopAndRmData(cId, name):
    """
    This function builds a docker image then creates a container and starts it. 

    :param cId: The Id of the container to be removed. 
    :type cId: str.
    :param name: The name of the docker repo to be removed.
    :type name: str.
    :returns: None
    """
    c = Client(base_url='unix://var/run/docker.sock')
    name += ":latest"
    c.stop(container=cId)
    c.remove_container(container=cId)
    c.remove_image(image=name)
