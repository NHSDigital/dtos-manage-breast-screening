from urllib.parse import urlencode

import pytest
from django.http import QueryDict

from manage_breast_screening.participants.tests.factories import AppointmentFactory

from ...forms import AppointmentCannotGoAheadForm


@pytest.mark.django_db
class TestAppointmentCannotGoAheadForm:
    @pytest.mark.parametrize(
        "decision,reinvite_value", [("True", True), ("False", False)]
    )
    def test_reinvite_reflects_form_data(self, decision, reinvite_value):
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
        form.save()
        appointment.refresh_from_db()
        assert appointment.reinvite == reinvite_value
