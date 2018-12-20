"""
Implement self-provisioning. This runs when the node starts up and detects
that it is not provisioned but is configured with a provision key.
It will attempt to contact the controller using the provision key. If
successful, the node will download some configuration and the assigned
node key.
"""
import os

import yaml

from paradrop.base import nexus, settings
from paradrop.core.agent.http import PDServerRequest
from paradrop.core.config import devices, zerotier
from paradrop.lib.utils import pdosq


def can_provision():
    """
    Check if self-provisioning is possible.

    We need to be able to read in the batch ID and key in order to provision
    the node.
    """
    conf = read_provisioning_conf()
    for field in ["batch_id", "batch_key"]:
        if conf.get(field, None) is None:
            return False

    return True


def provision_self(update_manager):
    """
    Provision the node.

    Returns a deferred.
    """
    name = "node-{:x}".format(devices.get_hardware_serial())

    conf = read_provisioning_conf()
    batch_id = conf.get("batch_id", None)
    batch_key = conf.get("batch_key", None)

    def cbresponse(response):
        router = response.data['router']
        nexus.core.provision(router['_id'])
        nexus.core.saveKey(router['password'], 'apitoken')
        nexus.core.jwt_valid = True

        batch = response.data['batch']
        hostconfig_patch = batch.get("hostconfig_patch", [])
        zerotier_networks = batch.get("zerotier_networks", [])
        update_manager.add_provision_update(hostconfig_patch, zerotier_networks)

        write_provisioning_result(response.data)

    data = {
        "name": name,
        "key": batch_key,
        "zerotier_address": zerotier.getAddress()
    }

    request = PDServerRequest('/api/batches/{}/provision'.format(batch_id))
    d = request.post(**data)
    d.addCallback(cbresponse)
    return d


def read_provisioning_conf():
    """
    Read provisioning information from the configuration file.

    This file will exist on startup if the node is to be self-provisioned.
    """
    path = os.path.join(settings.CONFIG_HOME_DIR, "provision.yaml")
    return pdosq.read_yaml_file(path, default={})


def read_provisioning_result():
    """
    Read provisioning result from the filesystem.
    """
    path = os.path.join(settings.CONFIG_HOME_DIR, "provisioned.yaml")
    return pdosq.read_yaml_file(path, default={})


def write_provisioning_result(result):
    """
    Write provisioning result to a persistent file.
    """
    path = os.path.join(settings.CONFIG_HOME_DIR, "provisioned.yaml")
    with open(path, "w") as output:
        output.write(yaml.safe_dump(result, default_flow_style=False))
