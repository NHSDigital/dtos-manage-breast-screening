"""
A way to declare authorization rules in code, inspired by django-rules
https://github.com/dfunckt/django-rules/tree/master
"""

from collections import defaultdict
from functools import reduce
from operator import and_
from typing import Any, Protocol


class Predicate(Protocol):
    """
    A function that takes a user and object (which may be None) and returns True or False
    """

    def __call__(self, user: Any, obj: Any) -> bool: ...


def combine(predicate, *others: Predicate) -> Predicate:
    """
    Combine multiple predicates into a single predicate
    that returns true if ALL of the predicates are true.
    """

    def combined(user, obj):
        results = (other(user, obj) for other in others)
        return reduce(and_, results, predicate(user, obj))

    return combined


class RuleSet:
    def __init__(self, predicates: dict[str, Predicate] | None = None):
        self.app_permissions = defaultdict(list)
        self.permission_predicates = {}

        if predicates:
            for permission, predicate in predicates.items():
                self._set_predicate(permission, predicate)

    def _set_predicate(self, permission: str, predicate: Predicate):
        try:
            app_label, _ = permission.split(".", maxsplit=1)
        except ValueError as e:
            raise ValueError(
                'Permission must have the format "<app_label>.<name>"'
            ) from e

        self.app_permissions[app_label].append(permission)
        self.permission_predicates[permission] = predicate

    def has_perm(self, user, perm, obj=None):
        if not user.is_active:
            return False

        predicate = self.permission_predicates.get(perm)

        return predicate and predicate(user=user, obj=obj)

    def has_module_perms(self, user, app_label):
        if not user.is_active:
            return False

        return any(
            self.has_perm(user, perm, obj=None)
            for perm in self.app_permissions[app_label]
        )
