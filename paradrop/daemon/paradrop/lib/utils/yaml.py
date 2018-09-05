from ruamel.yaml import YAML

from paradrop.core.auth.user import User
from paradrop.core.chute.chute import Chute
from paradrop.core.chute.service import Service


yaml = YAML(typ='safe')

yaml.default_flow_style = False

yaml.register_class(User)
yaml.register_class(Chute)
yaml.register_class(Service)
