"""
Node access rights

Operation             | owner | admin | trusted | guest
-------------------------------------------------------
install a chute       | yes   | yes   | limited | no
update a chute        | yes   | yes   | limited | no
remove a chute        | yes   | yes   | limited | no
change node settings  | yes   | yes   | no      | no
obtain SSH access     | yes   | yes   | no      | no

Trusted users have a limited ability to install, update, and remove chutes.
Trusted users can install any chute so long as it does not conflict with a
currently-installed chute. Trusted users can upgrade or remove chutes that
they have installed. These limitations are designed to allow multiple users
to access a shared node without allowing adverse interactions between users.
"""

def enforce_access_rights(update):
    """
    Check that the update should be allowed.
    """
    if update.old:
        if update.user != update.old.get_owner() and \
                update.user.role not in ["admin", "owner"]:
            raise Exception("Not permitted to modify existing chute {}".format(update.old.name))
