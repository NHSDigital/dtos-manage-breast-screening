"""
Define rules and permissions for access control.

This file is automatically imported by rules.apps.AutodiscoverRulesConfig
"""

import rules

from .models import Role


def user_has_any_role(role, *other_roles):
    roles = [role, *other_roles]

    @rules.predicate
    def check(user):
        # TODO: customise user model to add a cachable role attribute
        return any(group.name in roles for group in user.groups.all())

    return check


# fmt: off

rules.add_perm("participants.view_participant_data", user_has_any_role(Role.CLINICAL, Role.ADMINISTRATIVE))
rules.add_perm("mammograms.perform_mammogram_appointment", user_has_any_role(Role.CLINICAL))

# fmt: on
