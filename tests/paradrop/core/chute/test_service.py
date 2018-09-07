from paradrop.core.chute.chute import Chute
from paradrop.core.chute.service import Service


def test_Service():
    chute = Chute(name="test", version="1")

    # Test a service with no name of its own.
    service = Service(chute=chute)
    assert service.get_container_name() == "test"
    assert service.get_image_name() == "test:1"

    # Test a named service.
    service = Service(chute=chute, name="main")
    assert service.get_container_name() == "test-main"

    # Test a service that pulls an external image.
    service = Service(chute=chute, type="image", image="mongo:3.0")
    assert service.get_image_name() == "mongo:3.0"


def test_Service_create_specification():
    service = Service()

    spec = service.create_specification()
    assert spec['type'] == 'normal'
    assert 'environment' in spec
