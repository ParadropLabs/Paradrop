import os

from .authenticated_client import AuthenticatedClient
from .errors import ControllerConnectionError


LOCAL_DEFAULT_USERNAME = "paradrop"
LOCAL_DEFAULT_PASSWORD = ""

PARADROP_API_TOKEN = os.environ.get("PARADROP_API_TOKEN", None)
PARADROP_CHUTE_NAME = os.environ.get("PARADROP_CHUTE_NAME", None)

PDSERVER_URL = os.environ.get('PDSERVER_URL', 'https://paradrop.org')


class ControllerClient(AuthenticatedClient):
    """
    Client for interacting with a cloud controller.
    """

    connection_error_type = ControllerConnectionError

    def __init__(self, host=PDSERVER_URL):
        super(ControllerClient, self).__init__("cloud", PDSERVER_URL)
        self.host = host
        self.base_url = host + "/api"
        #self.base_url = "http://{}/api".format(host)

    def claim_node(self, token, name=None):
        """
        Claim ownership of a node using a claim token.
        """
        url = self.base_url + "/routers/claim"
        data = {
            "claim_token": token
        }
        if name is not None and len(name) > 0:
            data['name'] = name
        return self.request("POST", url, json=data)

    def create_chute(self, name, description, public=False):
        """
        Create a new chute in the store.
        """
        url = self.base_url + "/chutes"
        data = {
            "name": name,
            "description": description,
            "public": public
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

    def create_version(self, name, config):
        """
        Create a new chute version.
        """
        chute = self.find_chute(name)
        if chute is None:
            return None

        url = "{}/chutes/{}/versions".format(self.base_url, chute['_id'])
        data = {
            "chute_id": chute['_id'],
            "config": config
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

    def find_chute(self, name):
        """
        Find a chute by name or id.
        """
        # If this client object is ever used for multiple requests during its
        # lifetime, we could consider caching the group list locally for a
        # better response time. Then we need to add cache invalidation to all
        # of the methods that might affect the group list.
        chutes = self.list_chutes()
        for chute in chutes:
            if chute['_id'] == name or chute['name'] == name:
                return chute
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

    def find_update(self, node_id, update_id):
        """
        Find a node update.
        """
        url = "{}/routers/{}/updates/{}".format(self.base_url, node_id, update_id)
        return self.request("GET", url)

    def follow_chute(self, chute_name, node_name):
        """
        Follow updates to a chute.

        The node will automatically update when new versions of the chute are
        created.
        """
        chute = self.find_chute(chute_name)
        if chute is None:
            raise Exception("Chute was not found")
        node = self.find_node(node_name)
        if node is None:
            raise Exception("Node was not found")

        data = {
            "node_id": node['_id']
        }

        url = "{}/chutes/{}/watchers".format(self.base_url, chute['_id'])
        return self.request("POST", url, json=data)

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

    def install_chute(self, chute_name, node_name, select_version=None):
        """
        Install a chute from the store.
        """
        chute = self.find_chute(chute_name)
        if chute is None:
            raise Exception("Chute was not found")
        node = self.find_node(node_name)
        if node is None:
            raise Exception("Node was not found")

        versions = self.list_versions(chute_name)
        if versions is None:
            raise Exception("No version to install")

        version = None
        if select_version is None:
            version = versions[-1]
        else:
            for ver in versions:
                if str(ver['version']) == str(select_version):
                    version = ver
                    break
        if version is None:
            raise Exception("Version not found")

        data = {
            "updateClass": "CHUTE",
            "updateType": "update",
            "chute_id": chute['_id'],
            "router_id": node['_id'],
            "version_id": version['_id'],
            "config": version['config']
        }

        # Important: the server will reject the update if the name field is
        # missing. Version is also not automatically filled in.
        data['config']['name'] = chute['name']
        data['config']['version'] = version['version']

        url = "{}/routers/{}/updates".format(self.base_url, node['_id'])
        return self.request("POST", url, json=data)

    def list_chutes(self):
        """
        List chutes that the user owns or has access to.
        """
        url = self.base_url + "/chutes"
        return self.request("GET", url)

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

    def list_update_messages(self, node_id, update_id):
        """
        List messages from an update.
        """
        url = "{}/routers/{}/updates/{}/messages".format(self.base_url,
                node_id, update_id)
        return self.request("GET", url)

    def list_versions(self, name):
        """
        List nodes that the user owns or has access to.
        """
        chute = self.find_chute(name)
        if chute is None:
            return []

        url = "{}/chutes/{}/versions".format(self.base_url, chute['_id'])
        return self.request("GET", url)

    def save_node(self, node):
        """
        Save changes to a node object.
        """
        url = "{}/routers/{}".format(self.base_url, node['_id'])
        return self.request("PUT", url, json=node)
