import json

from mock import Mock
from nose.tools import assert_raises

from paradrop.lib.api import pdrest
from .pdmock import do_nothing


class APIDecoratorUser(object):
    def __init__(self):
        self.rest = Mock()
        self.rest.postprocess = Mock()
        self.rest.failprocess = Mock()

    @pdrest.APIDecorator(requiredArgs=["name"], optionalArgs=["stuff"])
    def runNotDoneYet(self, apiPkg, **kwargs):
        apiPkg.setNotDoneYet()

    @pdrest.APIDecorator()
    def runSuccess(self, apiPkg, **kwargs):
        apiPkg.setSuccess(0)

    @pdrest.APIDecorator()
    def runFailure(self, apiPkg, **kwargs):
        apiPkg.setFailure("failure")


def test_fake_resource():
    """
    Test _FakeResource class
    """
    resource = pdrest._FakeResource("hello")

    request = Mock()
    assert resource.render(request) == "hello"


def test_maybe_resource():
    """
    Test maybeResource function
    """
    method = Mock()
    request = Mock()
    resource = pdrest.maybeResource(do_nothing)()
    resource.render(request)


def test_api_resource():
    """
    Test APIResource class
    """
    resource = pdrest.APIResource()
    resource.register("method", "method", do_nothing)

    request = Mock()

    request.method = "method"
    request.path = "method"
    result = resource._get_callback(request)
    assert result[0] == do_nothing

    resource.getChild("method", request)

    resource.unregister(regex="method")
    
    # After unregister, the callback should be gone.
    result = resource._get_callback(request)
    assert result[0] is None

    resource.getChild("method", request)
    
    resource.children = Mock(name="what")
    result = resource.getChild("method", request)
    resource.getChild("method", request)


def test_api_package():
    """
    Test APIPackage class
    """
    request = Mock()
    apiPkg = pdrest.APIPackage(request)

    apiPkg.setNotDoneYet()
    assert apiPkg.result is None

    apiPkg.setSuccess(0)
    assert apiPkg.result

    apiPkg.setFailure("failure")
    assert apiPkg.result is False


def test_api_decorator():
    """
    Test APIDecorator
    """
    content = {
        'name': "Test",
        'stuff': "stuff"
    }

    request = Mock()
    request.content = Mock()
    request.content.read = Mock(return_value=json.dumps(content))

    apiPkg = pdrest.APIPackage(request)
    user = APIDecoratorUser()

    # Test the NOT_DONE_YET branch of code in APIDecorator.
    user.runNotDoneYet(request)

    # TODO: These fail because of missing variables (failureKey, failureDict,
    # etc.) Where are those supposed to come from?
#    user.runSuccess(request)
#    assert user.rest.postprocess.call_count == 1
#
#    apiPkg.countFailure = True
#    user.runFailure(reques)
#    assert user.rest.failprocess.call_count == 1
#
#    apiPkg.countFailure = False
#    user.runFailure(request)
#    assert user.rest.failprocess.call_count == 2

    # Try test with missing required field
    del content['name']
    request.content.read = Mock(return_value=json.dumps(content))
    user.runNotDoneYet(request)


