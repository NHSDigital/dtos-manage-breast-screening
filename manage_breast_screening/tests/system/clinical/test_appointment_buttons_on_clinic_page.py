import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.clinics.models import Clinic
from manage_breast_screening.clinics.tests.factories import ClinicFactory
from manage_breast_screening.participants.models import AppointmentStatus
from manage_breast_screening.participants.tests.factories import AppointmentFactory

from ..system_test_setup import SystemTestCase


class TestAppointmentButtons(SystemTestCase):
    @pytest.fixture(autouse=True)
    def before(self):
        today = datetime.now(timezone.utc).replace(hour=9, minute=0)
        self.clinic_start_time = today

    def test_user_starts_an_appointment(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_a_clinic_exists_that_is_run_by_my_provider()
        self.and_there_are_appointments()
        self.and_i_am_on_the_clinic_show_page()
        self.when_i_check_in_an_appointment()
        self.then_i_see_that_it_is_checked_in()
        self.when_i_start_the_appointment()
        self.then_i_should_be_on_the_confirm_identity_page()

    def and_a_clinic_exists_that_is_run_by_my_provider(self):
        user_assignment = self.current_user.assignments.first()
        self.clinic = ClinicFactory(
            starts_at=self.clinic_start_time,
            setting__name="West London BSS",
            setting__provider=user_assignment.provider,
            risk_type=Clinic.RiskType.ROUTINE_RISK,
        )

    def and_there_are_appointments(self):
        tzinfo = ZoneInfo("Europe/London")
        self.confirmed_appointment = AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            starts_at=datetime.now().replace(hour=9, minute=0, tzinfo=tzinfo),
            current_status=AppointmentStatus.CONFIRMED,
            first_name="Janet",
            last_name="Confirmed",
        )
        self.another_confirmed_appointment = AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            starts_at=datetime.now().replace(hour=9, minute=15, tzinfo=tzinfo),
            first_name="Also",
            last_name="Confirmed",
            current_status=AppointmentStatus.CONFIRMED,
        )
        self.checked_in_appointment = AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            starts_at=datetime.now().replace(hour=9, minute=30, tzinfo=tzinfo),
            current_status=AppointmentStatus.CHECKED_IN,
        )
        self.screened_appointment = AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            starts_at=datetime.now().replace(hour=10, minute=45, tzinfo=tzinfo),
            current_status=AppointmentStatus.SCREENED,
        )
        self.in_progress_appointment = AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            starts_at=datetime.now().replace(hour=11, minute=00, tzinfo=tzinfo),
            current_status=AppointmentStatus.IN_PROGRESS,
        )

    def and_i_am_on_the_clinic_show_page(self):
        self.page.goto(
            self.live_server_url
            + reverse("clinics:show", kwargs={"pk": self.clinic.pk})
        )
        self.assert_page_title_contains("Routine risk screening clinic")

    def when_i_check_in_an_appointment(self):
        check_in_link = self.page.get_by_text("Check in").first
        self.appointment_row = (
            self.page.locator(".nhsuk-table__row").filter(has=check_in_link).first
        )
        check_in_link.click()

    def then_i_see_that_it_is_checked_in(self):
        expect(self.appointment_row).to_contain_text("Checked in")

    def and_there_is_a_start_appointment_link(self):
        link = self.appointment_row.get_by_role("link").filter(
            has_text="Start appointment"
        )
        expect(link).to_be_attached()

    def when_i_start_the_appointment(self):
        self.appointment_row.get_by_text("Start appointment").click()

    def then_i_should_be_on_the_confirm_identity_page(self):
        path = reverse(
            "mammograms:confirm_identity",
            kwargs={"pk": self.confirmed_appointment.pk},
        )
        expect(self.page).to_have_url(re.compile(path))
        self.assert_page_title_contains("Confirm identity")
