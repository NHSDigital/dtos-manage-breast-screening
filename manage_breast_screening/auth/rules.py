"""
Define rules and permissions for access control.

This file is automatically imported by rules.apps.AutodiscoverRulesConfig
"""

import rules

from .models import Permission, Role


@rules.predicate
def is_clinical(user):
    return user.has_role(Role.CLINICAL.value)


@rules.predicate
def is_administrative(user):
    return user.has_role(Role.ADMINISTRATIVE.value)


@rules.predicate
def is_sysadmin(user):
    return getattr(user, "is_sysadmin", False)


rules.add_perm(Permission.VIEW_PARTICIPANT_DATA, is_clinical | is_administrative)
rules.add_perm(Permission.MANAGE_PROVIDER_SETTINGS, is_sysadmin)
