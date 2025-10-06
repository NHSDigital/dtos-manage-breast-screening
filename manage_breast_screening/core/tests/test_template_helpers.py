import pytest
from django.contrib.auth.models import AnonymousUser

from manage_breast_screening.auth.tests.factories import UserFactory
from manage_breast_screening.clinics.tests.factories import UserAssignmentFactory
from manage_breast_screening.core.template_helpers import header_account_items


@pytest.mark.django_db
class TestHeaderAccountItems:
    def test_user_with_no_role(self):
        user = UserFactory.create(first_name="Firstname", last_name="Lastname")
        assert header_account_items(user) == [
            {"text": "LASTNAME, Firstname", "icon": True},
            {"href": "/auth/log-out/", "text": "Log out"},
        ]

    def test_user_with_role(self):
        user = UserFactory.create(first_name="Firstname", last_name="Lastname")
        UserAssignmentFactory.create(clinical=True, user=user)
        assert header_account_items(user) == [
            {"text": "LASTNAME, Firstname (Clinical)", "icon": True},
            {"href": "/auth/log-out/", "text": "Log out"},
        ]

    def test_anonymous_user(self):
        user = AnonymousUser()
        assert header_account_items(user) == [
            {"href": "/auth/log-in/", "text": "Log in"},
        ]
