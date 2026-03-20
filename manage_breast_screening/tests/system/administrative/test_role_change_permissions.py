from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import allure
import pytest
from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.auth.models import Role
from manage_breast_screening.clinics.models import Clinic
from manage_breast_screening.clinics.tests.factories import ClinicFactory
from manage_breast_screening.participants.models.appointment import (
    AppointmentStatusNames,
)
from manage_breast_screening.participants.tests.factories import AppointmentFactory

from ..system_test_setup import SystemTestCase


@allure.link("https://nhsd-jira.digital.nhs.uk/browse/DTOSS-10306", "DTOSS-10306")
@allure.epic("DTOSS-1030 - Permissions & Settings V1")
@allure.feature("Clinical and administrative roles")
class TestRoleChangePermissions(SystemTestCase):
    @pytest.fixture(autouse=True)
    def before(self):
        today = datetime.now(timezone.utc).replace(hour=9, minute=0)
        self.clinic_start_time = today

    def test_changing_role_to_clinical_grants_ability_to_start_appointments(self):
        self.given_i_am_logged_in_as_an_administrative_user()
        self.and_a_clinic_exists_that_is_run_by_my_provider()
        self.and_there_are_appointments()
        self.and_i_am_on_the_clinic_show_page()

        self.then_the_scheduled_appointment_row_has_a_check_in_button()
        self.then_the_checked_in_appointment_row_has_no_start_appointment_button()

        self.when_my_role_is_changed_to_clinical()
        self.and_i_am_on_the_clinic_show_page()

        self.then_the_checked_in_appointment_row_has_a_start_appointment_button()

    def and_a_clinic_exists_that_is_run_by_my_provider(self):
        user_assignment = self.current_user.assignments.first()
        self.clinic = ClinicFactory(
            starts_at=self.clinic_start_time,
            setting__provider=user_assignment.provider,
            risk_type=Clinic.RiskType.ROUTINE_RISK,
        )

    def and_there_are_appointments(self):
        tzinfo = ZoneInfo("Europe/London")
        AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            starts_at=datetime.now().replace(hour=9, minute=0, tzinfo=tzinfo),
            current_status=AppointmentStatusNames.SCHEDULED,
            first_name="Janet",
            last_name="Scheduled",
        )
        AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            starts_at=datetime.now().replace(hour=9, minute=15, tzinfo=tzinfo),
            current_status=AppointmentStatusNames.CHECKED_IN,
            first_name="Janet",
            last_name="CheckedIn",
        )

    def and_i_am_on_the_clinic_show_page(self):
        self.page.goto(
            self.live_server_url
            + reverse("clinics:show_clinic", kwargs={"pk": self.clinic.pk})
        )

    def _appointment_row(self, last_name):
        return self.page.locator(".nhsuk-table__row").filter(has_text=last_name)

    def then_the_scheduled_appointment_row_has_a_check_in_button(self):
        row = self._appointment_row("Scheduled")
        expect(row.get_by_text("Check in")).to_be_visible()

    def then_the_checked_in_appointment_row_has_no_start_appointment_button(self):
        row = self._appointment_row("CheckedIn")
        expect(row.get_by_text("Start appointment")).to_be_hidden()

    def when_my_role_is_changed_to_clinical(self):
        assignment = self.current_user.assignments.first()
        assignment.roles = [Role.CLINICAL]
        assignment.save()

    def then_the_checked_in_appointment_row_has_a_start_appointment_button(self):
        row = self._appointment_row("CheckedIn")
        expect(row.get_by_text("Start appointment")).to_be_visible()
