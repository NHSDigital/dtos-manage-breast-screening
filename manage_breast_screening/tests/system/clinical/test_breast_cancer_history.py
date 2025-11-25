from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)

from ..system_test_setup import SystemTestCase


class TestBreastCancerHistory(SystemTestCase):
    def test_adding_and_editing_breast_cancer_history(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.when_i_click_on_add_breast_cancer_history()
        self.then_i_see_the_add_breast_cancer_history_form()

        self.when_i_select_right_breast()
        self.and_i_select_lumpectomy_in_right_breast()
        self.and_i_select_no_surgery_in_left_breast()
        self.and_i_select_no_other_surgery()
        self.and_i_select_no_radiotherapy()
        self.and_i_select_chemotherapy()
        self.and_i_select_a_private_clinic()
        self.and_i_enter_the_details_of_the_private_clinic()

        self.and_i_click_save()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_history_item_is_added()
        self.and_the_message_says_device_added()

        self.when_i_click_change()
        self.then_i_see_the_edit_breast_cancer_history_form()
        self.when_i_select_breast_radiotherapy_in_right_breast()
        self.and_i_click_save()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_history_item_shows_the_radiotherapy()
        self.and_the_message_says_breast_cancer_history_updated()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.when_i_click_on_add_breast_cancer_history()
        self.then_the_accessibility_baseline_is_met()

    def test_validation_errors(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.when_i_click_on_add_breast_cancer_history()
        self.and_i_click_save()
        self.then_i_am_prompted_to_fill_in_required_fields()

    def and_there_is_an_appointment(self):
        self.participant = ParticipantFactory(first_name="Janet", last_name="Williams")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(
            screening_episode=self.screening_episode,
            clinic_slot__clinic__setting__provider=self.current_provider,
        )

    def and_i_am_on_the_record_medical_information_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": self.appointment.pk},
            )
        )

    def when_i_click_on_add_breast_cancer_history(self):
        self.page.get_by_text("Add breast cancer history").click()

    def then_i_see_the_add_breast_cancer_history_form(self):
        expect(self.page.get_by_text("Add details of breast cancer")).to_be_visible()
        self.assert_page_title_contains("Add details of breast cancer")

    def then_i_see_the_edit_breast_cancer_history_form(self):
        expect(self.page.get_by_text("Edit details of breast cancer")).to_be_visible()
        self.assert_page_title_contains("Edit details of breast cancer")

    def when_i_select_right_breast(self):
        fieldset = self.get_fieldset_by_legend("In which breasts was cancer diagnosed?")
        fieldset.get_by_label("Right breast").click()

    def and_i_click_save(self):
        self.page.get_by_text("Save").click()

    def then_i_am_back_on_the_medical_information_page(self):
        self.expect_url("mammograms:record_medical_information", pk=self.appointment.pk)

    def and_the_history_item_is_added(self):
        key = self.page.locator(
            ".nhsuk-summary-list__key",
            has=self.page.get_by_text("Breast cancer history", exact=True),
        )
        row = self.page.locator(".nhsuk-summary-list__row").filter(has=key)
        expect(row).to_contain_text("Right breast")

    def and_the_message_says_device_added(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Breast cancer history added")

    def and_i_select_lumpectomy_in_right_breast(self):
        fieldset = self.get_fieldset_by_legend(
            "What procedure have they had in their Right breast (or axilla)?"
        )
        fieldset.get_by_label("Lumpectomy").first.click()

    def and_i_select_no_surgery_in_left_breast(self):
        fieldset = self.get_fieldset_by_legend(
            "What procedure have they had in their Left breast (or axilla)?"
        )
        fieldset.get_by_label("No procedure").last.click()

    def and_i_select_no_other_surgery(self):
        fieldset = self.get_fieldset_by_legend(
            "What other surgery have they had in their Right breast (or axilla)?"
        )
        fieldset.get_by_label("No other surgery").click()

        fieldset = self.get_fieldset_by_legend(
            "What other surgery have they had in their Left breast (or axilla)?"
        )
        fieldset.get_by_label("No other surgery").click()

    def and_i_select_no_radiotherapy(self):
        fieldset = self.get_fieldset_by_legend(
            "What treatment have they had in their Right breast (or axilla)?"
        )
        fieldset.get_by_label("No radiotherapy").click()

        fieldset = self.get_fieldset_by_legend(
            "What treatment have they had in their Left breast (or axilla)?"
        )
        fieldset.get_by_label("No radiotherapy").click()

    def and_i_select_chemotherapy(self):
        fieldset = self.get_fieldset_by_legend("Systemic treatments")
        fieldset.get_by_label("Chemotherapy").click()

    def and_i_select_a_private_clinic(self):
        fieldset = self.get_fieldset_by_legend(
            "Where did surgery and treatment take place?"
        )
        fieldset.get_by_label("At a private clinic in the UK").click()

    def and_i_enter_the_details_of_the_private_clinic(self):
        fieldset = self.get_fieldset_by_legend(
            "Where did surgery and treatment take place?"
        )
        fieldset.get_by_label("Provide details").filter(visible=True).fill("Abc clinic")

    def then_i_am_prompted_to_fill_in_required_fields(self):
        self.expect_validation_error(
            error_text="Select which breasts cancer was diagnosed in",
            fieldset_legend="In which breasts was cancer diagnosed?",
            field_label="Right breast",
            field_name="diagnosis_location",
        )

        self.expect_validation_error(
            error_text="Select which procedure they have had in the right breast",
            fieldset_legend="What procedure have they had in their Right breast (or axilla)",
            field_label="Lumpectomy",
            field_name="right_breast_procedure",
        )

    def when_i_click_change(self):
        self.page.get_by_text("Change breast cancer item").click()

    def when_i_select_breast_radiotherapy_in_right_breast(self):
        fieldset = self.get_fieldset_by_legend(
            "What treatment have they had in their Right breast (or axilla)?"
        )
        fieldset.get_by_label("Breast radiotherapy").click()

    def and_the_history_item_shows_the_radiotherapy(self):
        key = self.page.locator(
            ".nhsuk-summary-list__key",
            has=self.page.get_by_text("Breast cancer history", exact=True),
        )
        row = self.page.locator(".nhsuk-summary-list__row").filter(has=key)
        expect(row).to_contain_text("Breast radiotherapy")

    def and_the_message_says_breast_cancer_history_updated(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Breast cancer history updated")
