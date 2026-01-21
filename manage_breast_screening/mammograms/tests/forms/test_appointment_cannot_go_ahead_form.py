from urllib.parse import urlencode

import pytest
from django.http import QueryDict

from manage_breast_screening.participants.models.appointment import (
    AppointmentStatusNames,
)
from manage_breast_screening.participants.tests.factories import AppointmentFactory

from ...forms import AppointmentCannotGoAheadForm


@pytest.mark.django_db
class TestAppointmentCannotGoAheadForm:
    @pytest.mark.parametrize(
        "decision,reinvite_value", [("True", True), ("False", False)]
    )
    def test_reinvite_reflects_form_data(self, decision, reinvite_value, clinical_user):
        appointment = AppointmentFactory()
        assert not appointment.reinvite

        form_data = QueryDict(
            urlencode(
                {
                    "stopped_reasons": ["failed_identity_check"],
                    "decision": decision,
                },
                doseq=True,
            )
        )
        form = AppointmentCannotGoAheadForm(form_data, instance=appointment)
        form.is_valid()
        form.save(current_user=clinical_user)
        appointment.refresh_from_db()
        assert appointment.reinvite == reinvite_value

    def test_updates_status(self, clinical_user):
        appointment = AppointmentFactory()

        form_data = QueryDict(
            urlencode(
                {
                    "stopped_reasons": ["failed_identity_check"],
                    "decision": "True",
                },
                doseq=True,
            )
        )
        form = AppointmentCannotGoAheadForm(form_data, instance=appointment)
        form.is_valid()
        form.save(current_user=clinical_user)

        assert (
            appointment.statuses.filter(
                name=AppointmentStatusNames.ATTENDED_NOT_SCREENED,
                created_by=clinical_user,
            ).count()
            == 1
        )
