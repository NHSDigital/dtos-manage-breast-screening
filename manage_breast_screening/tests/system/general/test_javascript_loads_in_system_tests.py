from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from django.urls import reverse

from manage_breast_screening.clinics.tests.factories import ClinicFactory
from manage_breast_screening.participants.models import AppointmentStatus
from manage_breast_screening.participants.tests.factories import AppointmentFactory

from ..system_test_setup import SystemTestCase


class TestJavascriptLoadsInSystemTests(SystemTestCase):
    def test_check_in_component_initialised(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.when_i_visit_the_clinic_page()
        self.then_the_check_in_component_is_initialised()

    def and_there_is_an_appointment(self):
        assignment = self.current_user.assignments.first()
        self.clinic = ClinicFactory(
            starts_at=datetime.now(timezone.utc).replace(hour=9, minute=0),
            setting__provider=assignment.provider,
        )
        tzinfo = ZoneInfo("Europe/London")
        self.appointment = AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            clinic_slot__starts_at=datetime.now(timezone.utc).replace(
                hour=9, minute=0, tzinfo=tzinfo
            ),
            current_status=AppointmentStatus.SCHEDULED,
        )

    def when_i_visit_the_clinic_page(self):
        self.page.goto(
            self.live_server_url
            + reverse("clinics:show", kwargs={"pk": self.clinic.pk})
        )

    def then_the_check_in_component_is_initialised(self):
        component = self.page.locator('[data-module="app-check-in"]').first
        dataset = component.evaluate("el => el.dataset")
        assert "appCheckInInit" in dataset
