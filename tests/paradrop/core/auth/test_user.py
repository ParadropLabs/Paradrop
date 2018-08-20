from paradrop.core.auth import user


def test_User():
    user1 = user.User("user1", "localhost")
    user1_copy = user.User("user1", "localhost")

    # Test equality
    assert user1 == user1_copy
    assert user1_copy == user1

    assert user1 != user2
    assert user2 != user1

    # Test internal user
    internal = user.User.get_internal_user()
    assert internal.role == "owner"


def test_User_get_highest_role():
    roles = ["trusted", "admin", "owner"]
    assert user.User.get_highest_role(roles) == "owner"

    roles = ["trusted", "admin", "guest"]
    assert user.User.get_highest_role(roles) == "admin"

    roles = ["trusted", "user", "guest"]
    assert user.User.get_highest_role(roles) == "trusted"
