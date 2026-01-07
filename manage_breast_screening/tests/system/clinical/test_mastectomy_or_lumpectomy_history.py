from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.core.utils.string_formatting import format_nhs_number
from manage_breast_screening.participants.models import AppointmentStatus
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)

from ..system_test_setup import SystemTestCase


class TestRecordingMastectomyOrLumpectomy(SystemTestCase):
    def test_adding_mastectomy_or_lumpectomy(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.and_i_see_the_appointment_status_bar()
        self.when_i_click_on_mastectomy_or_lumpectomy()
        self.then_i_see_the_add_mastectomy_or_lumpectomy_form()
        self.and_i_see_the_appointment_status_bar()

        self.when_i_click_save()
        self.then_i_see_validation_errors_for_missing_mastectomy_or_lumpectomy_details()

        self.when_i_provide_mastectomy_or_lumpectomy_details()
        self.and_i_click_save()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_mastectomy_or_lumpectomy_is_listed()
        self.and_the_message_says_mastectomy_or_lumpectomy_added()

        self.when_i_click_change()
        self.then_i_see_the_edit_mastectomy_or_lumpectomy_form()
        self.when_i_update_additional_details()
        self.and_i_click_save()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_mastectomy_or_lumpectomy_is_updated()
        self.and_the_message_says_mastectomy_or_lumpectomy_updated()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.when_i_click_on_mastectomy_or_lumpectomy()
        self.then_the_accessibility_baseline_is_met()

    def and_there_is_an_appointment(self):
        self.participant = ParticipantFactory(first_name="Janet", last_name="Williams")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(
            screening_episode=self.screening_episode,
            clinic_slot__clinic__setting__provider=self.current_provider,
            current_status_params={
                "name": AppointmentStatus.STARTED,
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

    def when_i_click_on_mastectomy_or_lumpectomy(self):
        self.page.get_by_role("button").filter(
            has_text="Mastectomy or lumpectomy"
        ).click()

    def then_i_see_the_add_mastectomy_or_lumpectomy_form(self):
        expect(
            self.page.get_by_text("Add details of mastectomy or lumpectomy")
        ).to_be_visible()
        expect(
            self.page.get_by_text(
                "Add breast cancer details if that was the reason for this surgery."
            )
        ).to_be_visible()
        link = self.page.get_by_role(
            "link", name="Add breast cancer details"
        ).get_attribute("href")
        assert link == reverse(
            "mammograms:add_breast_cancer_history_item",
            kwargs={"pk": self.appointment.pk},
        )

    def and_i_see_the_appointment_status_bar(self):
        status_bar = self.page.locator("div.app-status-bar")
        expect(status_bar).to_contain_text(
            format_nhs_number(self.participant.nhs_number)
        )
        expect(status_bar).to_contain_text(self.participant.full_name)

    def then_i_see_validation_errors_for_missing_mastectomy_or_lumpectomy_details(self):
        self.expect_validation_error(
            error_text="Select which procedure they have had in the right breast",
            fieldset_legend="Right breast",
            field_label="Lumpectomy",
        )
        self.expect_validation_error(
            error_text="Select which procedure they have had in the left breast",
            fieldset_legend="Left breast",
            field_label="Lumpectomy",
        )
        self.expect_validation_error(
            error_text="Select any other surgery they have had in the right breast",
            fieldset_legend="Right breast",
            field_label="Reconstruction",
        )
        self.expect_validation_error(
            error_text="Select any other surgery they have had in the left breast",
            fieldset_legend="Left breast",
            field_label="Reconstruction",
        )
        self.expect_validation_error(
            error_text="Select the reason for surgery",
            fieldset_legend="Why was this surgery done?",
            field_label="Risk reduction",
        )

    def when_i_provide_mastectomy_or_lumpectomy_details(self):
        self.page.locator(
            "input[name='right_breast_procedure'] + label", has_text="No procedure"
        ).click()
        self.page.locator(
            "input[name='left_breast_procedure'] + label",
            has_text="Mastectomy (no tissue remaining)",
        ).click()
        self.page.locator(
            "input[name='right_breast_other_surgery'] + label",
            has_text="Reconstruction",
        ).click()
        self.page.locator(
            "input[name='right_breast_other_surgery'] + label",
            has_text="Symmetrisation",
        ).click()
        self.page.locator(
            "input[name='left_breast_other_surgery'] + label",
            has_text="No other surgery",
        ).click()
        self.page.get_by_label("Year of surgery (optional)", exact=True).fill("2000")
        self.page.get_by_label("Other reason", exact=True).click()
        self.page.get_by_label("Provide details", exact=True).fill(
            "Other reason for surgery text"
        )
        self.page.get_by_label("Additional details (optional)", exact=True).fill(
            "additional details for test of mastectomy or lumpectomy details"
        )

    def and_i_click_save(self):
        self.page.get_by_text("Save").click()

    when_i_click_save = and_i_click_save

    def then_i_am_back_on_the_medical_information_page(self):
        self.expect_url("mammograms:record_medical_information", pk=self.appointment.pk)

    def and_the_mastectomy_or_lumpectomy_is_listed(self):
        heading = self.page.get_by_role("heading").filter(
            has_text="Mastectomy or lumpectomy"
        )
        expect(heading).to_be_attached()

        section = self.page.locator("section").filter(has=heading)
        expect(section).to_be_attached()

        row = section.locator(".app-nested-info__row", has_text="Procedures")

        expect(row).to_contain_text("Right breast No procedure")
        expect(row).to_contain_text("Left breast Mastectomy (no tissue remaining)")

    def and_the_message_says_mastectomy_or_lumpectomy_added(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Added mastectomy or lumpectomy")

    def when_i_click_change(self):
        self.page.get_by_text("Change mastectomy or lumpectomy item").click()

    def then_i_see_the_edit_mastectomy_or_lumpectomy_form(self):
        expect(
            self.page.get_by_text("Edit details of mastectomy or lumpectomy")
        ).to_be_visible()
        self.assert_page_title_contains("Edit details of mastectomy or lumpectomy")

    def when_i_update_additional_details(self):
        self.page.get_by_label("Additional details (optional)", exact=True).fill(
            "updated additional details for test of mastectomy or lumpectomy details"
        )

    def and_the_mastectomy_or_lumpectomy_is_updated(self):
        heading = self.page.get_by_role("heading").filter(
            has_text="Mastectomy or lumpectomy"
        )
        section = self.page.locator("section").filter(has=heading)
        row = section.locator(".app-nested-info__row", has_text="Additional details")

        expect(row).to_contain_text(
            "updated additional details for test of mastectomy or lumpectomy details"
        )

    def and_the_message_says_mastectomy_or_lumpectomy_updated(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Updated mastectomy or lumpectomy")
