import json
from twisted.internet.defer import succeed
from klein import Klein

from . import cors


class PasswordApi(object):
    '''
    For now, we only support set/reset password for the default user: 'paradrop'
    '''
    routes = Klein()

    def __init__(self, password_manager):
        self.password_manager = password_manager


    @routes.route('/clear', methods=['POST'])
    def clear(self, request):
        cors.config_cors(request)
        request.setHeader('Content-Type', 'application/json')
        self.password_manager.reset()
        return json.dumps({'success': True})


    # OPTIONS method for CORS
    @routes.route('/change', methods=['POST', 'OPTIONS'])
    def change(self, request):
        cors.config_cors(request)
        if request.method == 'OPTIONS':
            return succeed(None)

        request.setHeader('Content-Type', 'application/json')
        body = json.loads(request.content.read())
        password = body['password']
        result = self.password_manager.change_password(None, password)
        return json.dumps({'success': result})
