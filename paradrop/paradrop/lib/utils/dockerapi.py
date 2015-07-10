###################################################################
# Copyright 2013-2015 All Rights Reserved
# Authors: The Paradrop Team
###################################################################

from paradrop.lib.utils.output import out, logPrefix
import docker
import json


def startChute(update):
    print update.__dict__
    out.warn('** %s TODO implement me\n' % logPrefix())

    repo = update.name + ":latest"
    dockerfile = update.dockerfile
    name = update.name

    host_config = docker.utils.create_host_config(
        port_bindings={80: 9000},
        restart_policy={"MaximumRetryCount": 0, "Name": "always"}
    )

    c = docker.Client(base_url="unix://var/run/docker.sock")

    for line in c.build(rm=True, tag=repo, fileobj=dockerfile):
        for key, value in json.loads(line).iteritems():
            if (isinstance(value, dict)):
                continue
            else:
                update.pkg.request.write(str(value))
    container = c.create_container(
        image=repo, name=name, host_config=host_config
    )

    out.info("-- %s %s\n" % (logPrefix(), str(container.get('Id'))))
    c.start(container.get('Id'))


def stopChute(update):
    out.warn('** %s TODO implement me\n' % logPrefix())
    c = docker.Client(base_url='unix://var/run/docker.sock')
    repo = update.name + ":latest"
    name = update.name
    c.stop(container=name)
    c.remove_container(container=name)
    c.remove_image(image=repo)
