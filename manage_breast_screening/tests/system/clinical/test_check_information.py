import re
from datetime import datetime, timezone

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.clinics.models import Clinic
from manage_breast_screening.clinics.tests.factories import ClinicFactory
from manage_breast_screening.manual_images.models import Series, Study
from manage_breast_screening.participants.models.appointment import (
    AppointmentNote,
    AppointmentStatusNames,
)
from manage_breast_screening.participants.models.medical_history.implanted_medical_device_history_item import (
    ImplantedMedicalDeviceHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ImplantedMedicalDeviceHistoryItemFactory,
)

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
        self.and_there_is_medical_information_for_the_appointment()
        self.and_the_appointment_has_images()
        self.and_the_appointment_has_a_note()
        self.and_i_am_on_the_check_information_page()
        self.and_the_personal_details_are_listed()
        self.and_the_medical_information_is_listed()
        self.and_the_image_details_are_listed()
        self.and_the_appointment_details_are_listed()

        self.and_i_click_on_complete_screening()
        self.then_i_should_be_on_the_clinic_page()
        self.and_the_message_says_image_details_added()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_a_clinic_exists_that_is_run_by_my_provider()
        self.and_there_is_an_appointment_for_the_clinic()
        self.and_the_appointment_has_images()
        self.and_the_appointment_has_a_note()
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
            screening_episode__participant__ethnic_background_id="any_other_ethnic_background",
        )

    def and_there_is_medical_information_for_the_appointment(self):
        ImplantedMedicalDeviceHistoryItemFactory.create(
            appointment=self.appointment,
            device=ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE,
            procedure_year=2018,
            device_has_been_removed=True,
            removal_year=2022,
        )

    def and_the_appointment_has_images(self):
        study = Study.objects.create(
            appointment=self.appointment,
            additional_details="Test study details",
        )
        self._add_series(study, "CC", "R", 1)
        self._add_series(study, "CC", "L", 2)
        self._add_series(study, "MLO", "R", 3)
        self._add_series(study, "MLO", "L", 4)
        self._add_series(study, "EKLUND", "R", 5)
        self._add_series(study, "EKLUND", "L", 6)

    def and_the_appointment_has_a_note(self):
        AppointmentNote.objects.create(
            appointment=self.appointment,
            content="Some information about the participant's appointment.",
        )

    def _add_series(self, study, view_position, laterality, count):
        Series.objects.create(
            study=study,
            view_position=view_position,
            laterality=laterality,
            count=count,
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

    def and_the_personal_details_are_listed(self):
        heading = self.page.get_by_role("heading").filter(
            has_text="Personal Information"
        )
        section = self.page.locator(".nhsuk-card").filter(has=heading)
        expect(section).to_be_visible()

        row = section.locator(".nhsuk-summary-list__row", has_text="Ethnicity")
        value = row.locator(".nhsuk-summary-list__value")
        expect(value).to_contain_text("Other ethnic group (any other ethnic group)")

    def and_the_medical_information_is_listed(self):
        heading = self.page.get_by_role("heading").filter(
            has_text="Medical Information"
        )
        section = self.page.locator(".nhsuk-card").filter(has=heading)
        expect(section).to_be_visible()

        row = section.locator(
            ".nhsuk-summary-list__row", has_text="Previous mammograms"
        )
        value = row.locator(".nhsuk-summary-list__value")
        expect(value).to_contain_text("No additional mammograms added")

        row = section.locator(
            ".nhsuk-summary-list__row",
            has_text="Medical history",
        )
        value = row.locator(".nhsuk-summary-list__value")
        expect(value).to_contain_text("Hickman line (2018, removed 2022)")

        row = section.locator(".nhsuk-summary-list__row", has_text="Symptoms")
        value = row.locator(".nhsuk-summary-list__value")
        expect(value).to_contain_text("No symptoms recorded")

    def and_the_image_details_are_listed(self):
        heading = self.page.get_by_role("heading").filter(has_text="21 images taken")
        section = self.page.locator(".nhsuk-card").filter(has=heading)
        expect(section).to_be_visible()

        row = section.locator(".nhsuk-summary-list__row", has_text="Views taken")
        value = row.locator(".nhsuk-summary-list__value")
        expect(value).to_contain_text("1× RCC")
        expect(value).to_contain_text("2× LCC")
        expect(value).to_contain_text("3× RMLO")
        expect(value).to_contain_text("4× LMLO")
        expect(value).to_contain_text("5× Right Eklund")
        expect(value).to_contain_text("6× Left Eklund")

        row = section.locator(".nhsuk-summary-list__row", has_text="Notes for reader")
        value = row.locator(".nhsuk-summary-list__value")
        expect(value).to_contain_text("Test study details")

    def and_the_appointment_details_are_listed(self):
        heading = self.page.get_by_role("heading").filter(
            has_text="Appointment Details"
        )
        section = self.page.locator(".nhsuk-card").filter(has=heading)
        expect(section).to_be_visible()

        row = section.locator(
            ".nhsuk-summary-list__row", has_text="Special appointment"
        )
        value = row.locator(".nhsuk-summary-list__value")
        expect(value).to_have_text("No")

        row = section.locator(".nhsuk-summary-list__row", has_text="Appointment note")
        value = row.locator(".nhsuk-summary-list__value")
        expect(value).to_have_text(
            "Some information about the participant's appointment."
        )

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
