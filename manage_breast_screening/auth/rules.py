"""
Define rules and permissions for access control.

This file is automatically imported by rules.apps.AutodiscoverRulesConfig
"""

import rules

from .models import Permission, Role


@rules.predicate
def is_clinical(user):
    if not user.current_provider:
        return False

    return user.assignments.filter(
        provider=user.current_provider, roles__contains=[Role.CLINICAL.value]
    ).exists()


@rules.predicate
def is_administrative(user):
    if not user.current_provider:
        return False

    return user.assignments.filter(
        provider=user.current_provider, roles__contains=[Role.ADMINISTRATIVE.value]
    ).exists()


@rules.predicate
def is_sysadmin(user):
    return getattr(user, "is_sysadmin", False)


rules.add_perm(Permission.VIEW_PARTICIPANT_DATA, is_clinical | is_administrative)
