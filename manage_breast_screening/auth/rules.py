"""
Define rules and permissions for access control.

This file is automatically imported by rules.apps.AutodiscoverRulesConfig
"""

import rules

from .models import Permission, Role


def _user_has_role(user, role):
    if not user.current_provider:
        return False

    cache_key = f"_has_role_{role}_{user.current_provider.pk}"
    if not hasattr(user, cache_key):
        result = user.assignments.filter(
            provider=user.current_provider, roles__contains=[role]
        ).exists()
        setattr(user, cache_key, result)
    return getattr(user, cache_key)


@rules.predicate
def is_clinical(user):
    return _user_has_role(user, Role.CLINICAL.value)


@rules.predicate
def is_administrative(user):
    return _user_has_role(user, Role.ADMINISTRATIVE.value)


rules.add_perm(Permission.VIEW_PARTICIPANT_DATA, is_clinical | is_administrative)
