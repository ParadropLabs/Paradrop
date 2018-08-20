class User(object):
    role_priorities = {
        "guest": 0,
        "user": 1,
        "trusted": 2,
        "admin": 3,
        "owner": 4
    }

    def __init__(self, name, domain, role="user"):
        self.name = name
        self.domain = domain
        self.role = role

    def __eq__(self, other):
        if isinstance(other, User):
            return (self.name == other.name and self.domain == other.domain)
        elif isinstance(other, basestring):
            return self.name == other
        else:
            return False

    @classmethod
    def get_internal_user(user):
        """
        Create a User object for internal usage.

        This user will have unlimited privileges.
        """
        return user("__paradrop__", "localhost", role="owner")

    @staticmethod
    def get_highest_role(roles):
        x = zip((User.role_priorities[r] for r in roles), roles)
        x.sort(reverse=True)
        return x[0][1]
