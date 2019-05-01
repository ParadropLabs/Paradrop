import base64

from io import BytesIO

import requests


class Camera(object):
    def __init__(self, device_id, host):
        """
        Initialize Camera device object.

        device_id: string that uniquely identifies the device (e.g. MAC address)
        host: host name or IP address
        """
        self.device_id = device_id
        self.host = host

    def __repr__(self):
        return "Camera({})".format(self.device_id)

    def get_image(self):
        """
        Get an image from the camera.

        Returns image data as a BytesIO object.
        """
        url = "http://{}/image.jpg".format(self.host)

        encoded = base64.b64encode('admin:'.encode('utf-8')).decode('ascii')

        headers = {
            'Authorization': 'Basic ' + encoded
        }

        result = requests.get(url, headers=headers)
        if result.ok:
            return BytesIO(result.content)

        else:
            return None
