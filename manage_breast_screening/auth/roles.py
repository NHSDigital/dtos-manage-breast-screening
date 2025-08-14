"""
A custom auth backend for role-based access control

This should be added to the AUTHENTICATION_BACKENDS setting.
"""

from enum import StrEnum

from .ruleset import Predicate, RuleSet


def has_role(*roles: str) -> Predicate:
    return lambda user, obj: any(group.name in roles for group in user.groups)


class Role(StrEnum):
    ADMINISTRATIVE = "Administrative"
    CLINICAL = "Clinical"
    SUPERUSER = "Superuser"


ruleset = RuleSet(
    {
        "clinics.view_clinics": has_role(Role.ADMINISTRATIVE, Role.CLINICAL),
        "clinics.manage_clinics": has_role(Role.ADMINISTRATIVE, Role.CLINICAL),
        "participants.view_appointments": has_role(Role.ADMINISTRATIVE, Role.CLINICAL),
        "participants.manage_appointments": has_role(
            Role.ADMINISTRATIVE, Role.CLINICAL
        ),
        "participants.perform_mammogram_appointment": has_role(Role.CLINICAL),
        "participants.manage_medical_information": has_role(Role.CLINICAL),
        "participants.view_participant_data": has_role(
            Role.ADMINISTRATIVE, Role.CLINICAL
        ),
        "participants.manage_participant_data": has_role(
            Role.ADMINISTRATIVE, Role.CLINICAL
        ),
    }
)


class PermissionBackend(object):
    def authenticate(self, *args, **kwargs):
        return None

    def has_perm(self, user, perm, obj=None):
        return ruleset.has_perm(user=user, perm=perm, obj=obj)

    def has_module_perms(self, user, app_label):
        return ruleset.has_module_perms(user=user, app_label=app_label)
