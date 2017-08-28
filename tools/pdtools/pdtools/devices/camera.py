import base64
import cStringIO

import requests


class Camera(object):
    def __init__(self, host):
        self.host = host

    def get_image(self):
        """
        Get an image from the camera.

        Returns image data as a StringIO object.
        """
        url = "http://{}/image.jpg".format(self.host)

        encoded = base64.b64encode('admin:'.encode('utf-8')).decode('ascii')

        headers = {
            'Authorization': 'Basic ' + encoded
        }

        result = requests.get(url, headers=headers)
        if result.ok:
            return cStringIO.StringIO(result.content)

        else:
            return None
