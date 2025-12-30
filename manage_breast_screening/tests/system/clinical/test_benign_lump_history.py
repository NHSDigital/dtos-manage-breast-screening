from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.core.utils.string_formatting import format_nhs_number
from manage_breast_screening.participants.models import AppointmentStatus
from manage_breast_screening.participants.models.medical_history.benign_lump_history_item import (
    BenignLumpHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    BenignLumpHistoryItemFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)

from ..system_test_setup import SystemTestCase


class TestBenignLumpHistory(SystemTestCase):
    def test_adding_a_benign_lump_history_item(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.when_i_click_on_benign_lumps()
        self.then_i_see_the_add_benign_lump_history_form()
        self.and_i_see_the_appointment_status_bar()
        self.when_i_try_to_save_without_entering_benign_lump_details()
        self.then_i_see_validation_errors_for_missing_benign_lump_details()

        self.when_i_select_procedures_for_each_breast()
        self.and_i_enter_the_year_and_select_a_location()
        self.and_i_enter_additional_details()
        self.and_i_click_save_benign_lump_history()
        self.then_i_see_a_validation_error_for_missing_location_details()

        self.when_i_enter_the_location_details()
        self.and_i_click_save_benign_lump_history()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_benign_lump_history_item_is_listed()
        self.and_the_message_says_benign_lump_history_added()

    def test_updating_a_benign_lump_history_item(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_there_is_a_benign_lump_history_item()
        self.and_i_am_on_the_record_medical_information_page()
        self.then_i_see_a_change_link_for_the_benign_lump_history_item()

        self.when_i_click_on_the_change_link_for_the_benign_lump_history_item()
        self.when_i_update_the_form_details()
        self.and_i_click_save_benign_lump_history()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_benign_lump_history_item_is_updated()
        self.and_the_message_says_benign_lump_history_updated()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.when_i_click_on_benign_lumps()
        self.then_the_accessibility_baseline_is_met()

    def and_there_is_an_appointment(self):
        self.participant = ParticipantFactory(first_name="Sonia", last_name="Dhillon")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(
            screening_episode=self.screening_episode,
            clinic_slot__clinic__setting__provider=self.current_provider,
            current_status_params={
                "name": AppointmentStatus.IN_PROGRESS,
                "created_by": self.current_user,
            },
        )

    def and_i_am_on_the_record_medical_information_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": self.appointment.pk},
            )
        )

    def and_i_see_the_appointment_status_bar(self):
        status_bar = self.page.locator("div.app-status-bar")
        expect(status_bar).to_contain_text(
            format_nhs_number(self.participant.nhs_number)
        )
        expect(status_bar).to_contain_text(self.participant.full_name)

    def when_i_click_on_benign_lumps(self):
        self.page.get_by_role("button").filter(has_text="Benign lumps").click()

    def then_i_see_the_add_benign_lump_history_form(self):
        expect(self.page.get_by_text("Add details of benign lumps")).to_be_visible()
        self.assert_page_title_contains("Add details of benign lumps")

    def when_i_try_to_save_without_entering_benign_lump_details(self):
        self.page.get_by_role("button", name="Save").click()

    def then_i_see_validation_errors_for_missing_benign_lump_details(self):
        self.expect_validation_error(
            error_text="Select which procedures they have had in the left breast",
            fieldset_legend="Left breast",
            field_label="Needle biopsy",
        )
        self.expect_validation_error(
            error_text="Select which procedures they have had in the right breast",
            fieldset_legend="Right breast",
            field_label="Needle biopsy",
        )
        self.expect_validation_error(
            error_text="Select where the tests and treatment were done",
            fieldset_legend="Where were the tests and treatment done?",
            field_label="At an NHS hospital",
        )

    def when_i_select_procedures_for_each_breast(self):
        right_fieldset = self.page.get_by_role(
            "group", name="Right breast", exact=False
        )
        right_fieldset.get_by_label("Needle biopsy", exact=True).check()
        right_fieldset.get_by_label("Lump removed", exact=True).check()

        left_fieldset = self.page.get_by_role("group", name="Left breast", exact=False)
        left_fieldset.get_by_label("Lump removed", exact=True).check()

    def and_i_enter_the_year_and_select_a_location(self):
        self.page.get_by_label("Year of procedure (optional)", exact=True).fill("2022")
        self.page.get_by_label("At an NHS hospital", exact=True).click()

    def when_i_enter_the_location_details(self):
        self.page.locator("#id_nhs_hospital_details").fill(
            "St Thomas' Hospital, London"
        )

    def and_i_enter_additional_details(self):
        self.page.get_by_label("Additional details (optional)", exact=True).fill(
            "Participant described no complications following any of the procedures."
        )

    def and_i_click_save_benign_lump_history(self):
        self.page.get_by_role("button", name="Save").click()

    def then_i_see_a_validation_error_for_missing_location_details(self):
        self.expect_validation_error(
            error_text="Provide details about where the surgery and treatment took place",
            fieldset_legend="Where were the tests and treatment done?",
            field_label="Provide details",
            field_name="nhs_hospital_details",
        )

    def then_i_am_back_on_the_medical_information_page(self):
        self.expect_url("mammograms:record_medical_information", pk=self.appointment.pk)

    def and_the_benign_lump_history_item_is_listed(self):
        key = self.page.locator(
            ".nhsuk-summary-list__key",
            has=self.page.get_by_text("Benign lump history", exact=True),
        )
        row = self.page.locator(".nhsuk-summary-list__row").filter(has=key)

        expect(row).to_contain_text("Right breast: Needle biopsy, Lump removed")
        expect(row).to_contain_text("Left breast: Lump removed")
        expect(row).to_contain_text("2022")
        expect(row).to_contain_text("At an NHS hospital: St Thomas' Hospital, London")
        expect(row).to_contain_text(
            "Participant described no complications following any of the procedures."
        )

    def and_the_message_says_benign_lump_history_added(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Added benign lumps")

    def and_there_is_a_benign_lump_history_item(self):
        self.benign_lump_history_item = BenignLumpHistoryItemFactory(
            appointment=self.appointment,
            left_breast_procedures=[BenignLumpHistoryItem.Procedure.NEEDLE_BIOPSY],
            right_breast_procedures=[BenignLumpHistoryItem.Procedure.NO_PROCEDURES],
            procedure_year=2019,
            procedure_location=BenignLumpHistoryItem.ProcedureLocation.PRIVATE_CLINIC_UK,
            procedure_location_details="Private Hospital London",
            additional_details="Initial details about the procedure.",
        )

    def then_i_see_a_change_link_for_the_benign_lump_history_item(self):
        key = self.page.locator(
            ".nhsuk-summary-list__key",
            has=self.page.get_by_text("Benign lump history", exact=True),
        )
        row = self.page.locator(".nhsuk-summary-list__row").filter(has=key)

        expect(row).to_contain_text("Change")

    def when_i_click_on_the_change_link_for_the_benign_lump_history_item(self):
        key = self.page.locator(
            ".nhsuk-summary-list__key",
            has=self.page.get_by_text("Benign lump history", exact=True),
        )
        row = self.page.locator(".nhsuk-summary-list__row").filter(has=key)
        row.get_by_role("link", name="Change").click()

    def when_i_update_the_form_details(self):
        # Update to match the expected values in and_the_benign_lump_history_item_is_listed
        right_fieldset = self.page.get_by_role(
            "group", name="Right breast", exact=False
        )
        right_fieldset.get_by_label("No procedures", exact=True).uncheck()
        right_fieldset.get_by_label("Needle biopsy", exact=True).check()
        right_fieldset.get_by_label("Lump removed", exact=True).check()

        left_fieldset = self.page.get_by_role("group", name="Left breast", exact=False)
        left_fieldset.get_by_label("Needle biopsy", exact=True).uncheck()
        left_fieldset.get_by_label("Lump removed", exact=True).check()

        self.page.get_by_label("Year of procedure (optional)", exact=True).fill("2022")
        self.page.get_by_label("At an NHS hospital", exact=True).click()
        self.page.locator("#id_nhs_hospital_details").fill(
            "St Thomas' Hospital, London"
        )
        self.page.get_by_label("Additional details (optional)", exact=True).fill(
            "Participant described no complications following any of the procedures."
        )

    def and_the_benign_lump_history_item_is_updated(self):
        self.and_the_benign_lump_history_item_is_listed()

    def and_the_message_says_benign_lump_history_updated(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Updated benign lumps")
