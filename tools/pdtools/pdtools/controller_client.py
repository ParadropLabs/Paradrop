import os
from simplejson.scanner import JSONDecodeError
from six.moves.urllib.parse import urlparse

from .authenticated_client import AuthenticatedClient
from .config import PdtoolsConfig
from .devices.camera import Camera
from .util import LoginGatherer


LOCAL_DEFAULT_USERNAME = "paradrop"
LOCAL_DEFAULT_PASSWORD = ""

PARADROP_API_TOKEN = os.environ.get("PARADROP_API_TOKEN", None)
PARADROP_CHUTE_NAME = os.environ.get("PARADROP_CHUTE_NAME", None)

PDSERVER_URL = os.environ.get('PDSERVER_URL', 'https://paradrop.org')


class ControllerClient(AuthenticatedClient):
    """
    Client for interacting with a cloud controller.
    """
    def __init__(self, host=PDSERVER_URL):
        super(ControllerClient, self).__init__("cloud", PDSERVER_URL)
        self.host = host
        self.base_url = host + "/api"
        #self.base_url = "http://{}/api".format(host)

    def claim_node(self, token):
        """
        Claim ownership of a node using a claim token.
        """
        url = self.base_url + "/routers/claim"
        data = {
            "claim_token": token
        }
        return self.request("POST", url, json=data)

    def create_node(self, name, orphaned=False, claim=None):
        """
        Create a new node tracked by the controller.
        """
        url = self.base_url + "/routers"
        data = {
            "name": name,
            "orphaned": orphaned
        }
        if claim is not None:
            data['claim'] = claim
        return self.request("POST", url, json=data)

    def create_user(self, name, email, password, password2):
        """
        Create a new user account on the controller.
        """
        url = self.base_url + "/users"
        data = {
            "name": name,
            "email": email,
            "password": password,
            "confirmPassword": password2
        }
        return self.request("POST", url, json=data)

    def delete_node(self, name):
        """
        Delete a node tracked by the controller.
        """
        node = self.find_node(name)
        if node is not None:
            url = "{}/routers/{}".format(self.base_url, node['_id'])
            return self.request("DELETE", url)
        else:
            return None

    def find_group(self, name):
        """
        Find a group by name or id.
        """
        # If this client object is ever used for multiple requests during its
        # lifetime, we could consider caching the group list locally for a
        # better response time. Then we need to add cache invalidation to all
        # of the methods that might affect the group list.
        groups = self.list_groups()
        for group in groups:
            if group['_id'] == name or group['name'] == name:
                return group
        return None

    def find_node(self, name):
        """
        Find a node by name or id.
        """
        # If this client object is ever used for multiple requests during its
        # lifetime, we could consider caching the node list locally for a
        # better response time. Then we need to add cache invalidation to all
        # of the methods that might affect the node list.
        nodes = self.list_nodes()
        for node in nodes:
            if node['_id'] == name or node['name'] == name:
                return node
        return None

    def group_add_node(self, group_name, node_name):
        """
        Add a node to a group.
        """
        group = self.find_group(group_name)
        if group is None:
            raise Exception("Group was not found")
        node = self.find_node(node_name)
        if node is None:
            raise Exception("Node was not found")

        url = "{}/groups/{}/addRouter".format(self.base_url, group['_id'])
        data = {
            'router_id': node['_id']
        }
        return self.request("POST", url, json=data)

    def list_groups(self):
        """
        List groups that the user belongs to.
        """
        url = self.base_url + "/groups"
        return self.request("GET", url)

    def list_nodes(self):
        """
        List nodes that the user owns or has access to.
        """
        url = self.base_url + "/routers"
        return self.request("GET", url)

    def save_node(self, node):
        """
        Save changes to a node object.
        """
        url = "{}/routers/{}".format(self.base_url, node['_id'])
        return self.request("PUT", url, json=node)
