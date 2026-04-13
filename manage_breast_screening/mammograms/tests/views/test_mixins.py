import pytest
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import reverse
from django.views import View

from manage_breast_screening.mammograms.views.mixins import InProgressAppointmentMixin
from manage_breast_screening.participants.models.appointment import (
    AppointmentStatusNames,
)


@pytest.mark.django_db
class TestInProgressAppointmentMixin:
    class DummyView(InProgressAppointmentMixin, View):
        def get(self, request, pk):
            return HttpResponse(status=201)

    @pytest.fixture
    def dummy_request(self):
        return RequestFactory().get("/foo")

    @pytest.fixture
    def dummy_view(self):
        return self.DummyView.as_view()

    def test_current_appointment_owner_allowed(
        self, in_progress_appointment, dummy_request, dummy_view, clinical_user
    ):
        dummy_request.user = clinical_user
        response = dummy_view(request=dummy_request, pk=in_progress_appointment.pk)

        assert response.status_code == 201

    def test_other_users_redirected(
        self,
        dummy_request,
        dummy_view,
        appointment,
        clinical_user,
        another_clinical_user,
    ):
        appointment.status = AppointmentStatusNames.IN_PROGRESS
        appointment.status_changed_by = another_clinical_user
        appointment.save()

        dummy_request.user = clinical_user
        response = dummy_view(request=dummy_request, pk=appointment.pk)

        assert response.status_code == 302
        assert response.headers["location"] == reverse(
            "mammograms:show_appointment",
            kwargs={"pk": appointment.pk},
        )

    def test_unpermitted_roles_not_allowed(
        self, dummy_request, dummy_view, appointment, administrative_user
    ):
        """
        Non-permitted users shouldn't be able to access the view regardless,
        as they won't be allowed to start the appointment, but the mixin rechecks
        the permission on every request just to be safe.
        """
        appointment.status = AppointmentStatusNames.IN_PROGRESS
        appointment.status_changed_by = administrative_user
        appointment.save()

        dummy_request.user = administrative_user

        with pytest.raises(PermissionDenied):
            dummy_view(request=dummy_request, pk=appointment.pk)
