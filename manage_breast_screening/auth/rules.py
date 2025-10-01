"""
Define rules and permissions for access control.

This file is automatically imported by rules.apps.AutodiscoverRulesConfig
"""

import rules

from .models import Permission, Role


@rules.predicate
def is_clinical(user, provider):
    if not provider:
        return False

    return user.assignments.filter(
        provider=provider, roles__contains=[Role.CLINICAL.value]
    ).exists()


@rules.predicate
def is_administrative(user, provider):
    if not provider:
        return False

    return user.assignments.filter(
        provider=provider, roles__contains=[Role.ADMINISTRATIVE.value]
    ).exists()


rules.add_perm(Permission.VIEW_PARTICIPANT_DATA, is_clinical | is_administrative)
rules.add_perm(Permission.PERFORM_MAMMOGRAM_APPOINTMENT, is_clinical)
