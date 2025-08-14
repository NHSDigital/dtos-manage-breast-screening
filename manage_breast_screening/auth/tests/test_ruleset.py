import pytest

from ..ruleset import RuleSet, combine


def always_true_predicate(user, obj):
    return True


def always_false_predicate(user, obj):
    return False


def user_attribute_predicate(user, obj):
    return user.first_name == "Alice"


def object_predicate(user, obj):
    return obj["belongs_to"] == user


@pytest.mark.django_db
class TestRuleSet:
    def test_empty_ruleset(self, user):
        ruleset = RuleSet()

        assert not ruleset.has_perm(user=user, perm="foo.bar")
        assert not ruleset.has_perm(user=user, perm="foo.bar", obj={})
        assert not ruleset.has_module_perms(user=user, app_label="foo")

    def test_always_true_predicate(self, user):
        ruleset = RuleSet({"foo.bar": always_true_predicate})

        assert ruleset.has_perm(user=user, perm="foo.bar")
        assert not ruleset.has_perm(user=user, perm="foo.baz")

    def test_user_attribute_predicate(self, user):
        ruleset = RuleSet({"foo.bar": user_attribute_predicate})

        user.first_name = "Alice"
        assert ruleset.has_perm(user=user, perm="foo.bar")

        user.first_name = "Bob"
        assert not ruleset.has_perm(user=user, perm="foo.bar")

    def test_module_perms(self, user):
        ruleset = RuleSet({"foo.bar": user_attribute_predicate})

        user.first_name = "Alice"
        assert ruleset.has_module_perms(user=user, app_label="foo")
        assert not ruleset.has_module_perms(user=user, app_label="bar")

        user.first_name = "Bob"
        assert not ruleset.has_module_perms(user=user, app_label="foo")
        assert not ruleset.has_module_perms(user=user, app_label="bar")

    def test_partially_satisfied_predicates(self, user):
        ruleset = RuleSet(
            {"foo.bar": combine(always_true_predicate, always_false_predicate)}
        )

        assert not ruleset.has_perm(user=user, perm="foo.bar")
        assert not ruleset.has_module_perms(user=user, app_label="foo")

    def test_all_satisfied_predicates(self, user):
        ruleset = RuleSet(
            {"foo.bar": combine(always_true_predicate, user_attribute_predicate)}
        )
        user.first_name = "Alice"

        assert ruleset.has_perm(user=user, perm="foo.bar")
        assert ruleset.has_module_perms(user=user, app_label="foo")

    def test_object_predicate(self, user):
        ruleset = RuleSet({"foo.bar": object_predicate})

        owned = {"belongs_to": user}
        not_owned = {"belongs_to": "abc"}

        assert ruleset.has_perm(user=user, perm="foo.bar", obj=owned)
        assert not ruleset.has_perm(user=user, perm="foo.bar", obj=not_owned)
