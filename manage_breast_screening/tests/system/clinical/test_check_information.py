import re
from datetime import datetime, timezone

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.clinics.models import Clinic
from manage_breast_screening.clinics.tests.factories import ClinicFactory
from manage_breast_screening.participants.models.appointment import (
    AppointmentStatusNames,
)
from manage_breast_screening.participants.tests.factories import AppointmentFactory

from ..system_test_setup import SystemTestCase


class TestCheckInformation(SystemTestCase):
    @pytest.fixture(autouse=True)
    def before(self):
        today = datetime.now(timezone.utc).replace(hour=9, minute=0)
        self.clinic_start_time = today

    def test_check_information(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_a_clinic_exists_that_is_run_by_my_provider()
        self.and_there_is_an_appointment_for_the_clinic()
        self.and_i_am_on_the_check_information_page()

        self.and_i_click_on_complete_screening()
        self.then_i_should_be_on_the_clinic_page()
        self.and_the_message_says_image_details_added()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_a_clinic_exists_that_is_run_by_my_provider()
        self.and_there_is_an_appointment_for_the_clinic()
        self.and_i_am_on_the_check_information_page()
        self.then_the_accessibility_baseline_is_met()

    def and_there_is_a_clinic_exists_that_is_run_by_my_provider(self):
        user_assignment = self.current_user.assignments.first()
        self.clinic = ClinicFactory(
            starts_at=self.clinic_start_time,
            setting__name="West London BSS",
            setting__provider=user_assignment.provider,
            risk_type=Clinic.RiskType.ROUTINE_RISK,
        )

    def and_there_is_an_appointment_for_the_clinic(self):
        self.appointment = AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            clinic_slot__clinic__setting__provider=self.current_provider,
            current_status=AppointmentStatusNames.IN_PROGRESS,
        )

    def and_i_am_on_the_check_information_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:check_information",
                kwargs={"pk": self.appointment.pk},
            )
        )
        self.expect_url("mammograms:check_information", pk=self.appointment.pk)

    def and_i_click_on_complete_screening(self):
        self.page.get_by_text("Complete screening and return to clinic").click()

    def then_i_should_be_on_the_clinic_page(self):
        path = reverse(
            "clinics:show",
            kwargs={"pk": self.clinic.pk},
        )
        expect(self.page).to_have_url(re.compile(path))
        self.assert_page_title_contains("Routine risk screening clinic")

    def and_the_message_says_image_details_added(self):
        alert = self.page.get_by_role("alert")
        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text(
            f"{self.appointment.participant.full_name} has been screened"
        )
