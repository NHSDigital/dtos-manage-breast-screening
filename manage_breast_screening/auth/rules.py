"""
Define rules and permissions for access control.

This file is automatically imported by rules.apps.AutodiscoverRulesConfig
"""

import rules

from .models import Permission, Role


def user_has_any_role(role, *other_roles):
    roles = [role, *other_roles, Role.SUPERUSER]

    @rules.predicate
    def check(user):
        # TODO: customise user model to add a cachable role attribute
        return any(group.name in roles for group in user.groups.all())

    return check


# fmt: off

rules.add_perm(Permission.VIEW_PARTICIPANT_DATA, user_has_any_role(Role.CLINICAL, Role.ADMINISTRATIVE))
rules.add_perm(Permission.PERFORM_MAMMOGRAM_APPOINTMENT, user_has_any_role(Role.CLINICAL))

# fmt: on
