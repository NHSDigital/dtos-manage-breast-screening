from unittest.mock import MagicMock

import pytest
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory

from manage_breast_screening.core.models import AuditLog
from manage_breast_screening.core.views.generic import (
    AddWithAuditView,
    UpdateWithAuditView,
)
from manage_breast_screening.users.models import User
from manage_breast_screening.users.tests.factories import UserFactory


def apply_middleware(request):
    for middleware_class in [SessionMiddleware, MessageMiddleware]:
        middleware = middleware_class(get_response=MagicMock())
        middleware.process_request(request)
    return request


class DummyForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.CharField()

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)

    def create(self):
        return UserFactory.create(
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            nhs_uid="create_uid",
            email=self.cleaned_data["email"],
        )

    def update(self):
        return UserFactory.create(
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            nhs_uid="update_uid",
            email=self.cleaned_data["email"],
        )


class AddView(AddWithAuditView):
    form_class = DummyForm
    thing_name = "test"
    success_url = "/success"


class UpdateView(UpdateWithAuditView):
    form_class = DummyForm
    thing_name = "test"
    success_url = "/success"


class TestAddWithAuditView:
    def test_success_message_content(self):
        obj = UserFactory.build()

        assert AddView().get_success_message_content(obj) == "Added test"

    def test_get_context_data(self):
        request = RequestFactory().get("/")
        context = AddView(request=request).get_context_data()

        assert context["heading"] == "Add test"
        assert context["page_title"] == "Add test"

    @pytest.mark.django_db
    def test_audits_if_form_valid(self):
        request = apply_middleware(RequestFactory().post("/"))
        request.user = UserFactory()
        form = DummyForm(
            {"first_name": "abc", "last_name": "def", "email": "test@example.com"}
        )

        assert form.is_valid()
        AddView(request=request).form_valid(form)

        last_audit = AuditLog.objects.last()
        assert last_audit is not None
        assert last_audit.content_type == ContentType.objects.get_for_model(User)
        assert last_audit.actor == request.user
        assert last_audit.operation == AuditLog.Operations.CREATE
        assert last_audit.snapshot == {
            "email": "test@example.com",
            "first_name": "abc",
            "last_name": "def",
            "is_staff": False,
            "is_active": True,
            "last_login": None,
            "nhs_uid": "create_uid",
        }
        assert last_audit.system_update_id is None


class TestUpdateWithAuditView:
    def test_success_message_content(self):
        obj = UserFactory.build()

        assert UpdateView().get_success_message_content(obj) == "Updated test"

    def test_get_context_data(self):
        obj = UserFactory.build()
        request = RequestFactory().get("/")
        view = UpdateView(request=request)
        view.object = obj

        context = view.get_context_data()

        assert context["heading"] == "Edit test"
        assert context["page_title"] == "Edit test"

    @pytest.mark.django_db
    def test_audits_if_form_valid(self):
        request = apply_middleware(RequestFactory().post("/"))
        request.user = UserFactory()
        form = DummyForm(
            {"first_name": "new", "last_name": "name", "email": "test@example.com"}
        )

        assert form.is_valid()
        UpdateView(request=request).form_valid(form)

        last_audit = AuditLog.objects.last()
        assert last_audit is not None
        assert last_audit.content_type == ContentType.objects.get_for_model(User)
        assert last_audit.actor == request.user
        assert last_audit.operation == AuditLog.Operations.UPDATE
        assert last_audit.snapshot == {
            "email": "test@example.com",
            "first_name": "new",
            "last_name": "name",
            "is_staff": False,
            "is_active": True,
            "last_login": None,
            "nhs_uid": "update_uid",
        }
        assert last_audit.system_update_id is None
