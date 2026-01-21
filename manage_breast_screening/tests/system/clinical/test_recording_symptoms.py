import pytest
from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.core.utils.string_formatting import format_nhs_number
from manage_breast_screening.participants.models.appointment import (
    AppointmentStatusNames,
)
from manage_breast_screening.participants.models.symptom import (
    RelativeDateChoices,
    SymptomType,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
    SymptomFactory,
)

from ..system_test_setup import SystemTestCase


class TestRecordingSymptoms(SystemTestCase):
    @pytest.fixture(autouse=True)
    def setup_symptom_types(self):
        SymptomType.objects.get_or_create(id=SymptomType.LUMP, name="Lump")
        SymptomType.objects.get_or_create(
            id=SymptomType.SWELLING_OR_SHAPE_CHANGE, name="Swelling or shape change"
        )

    def test_adding_a_symptom(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.and_i_see_the_appointment_status_bar()
        self.when_i_click_on_lump()
        self.then_i_see_the_add_a_lump_form()
        self.and_i_see_the_appointment_status_bar()

        self.when_i_select_right_breast()
        self.and_i_enter_the_area()
        self.and_i_select_less_than_three_months()
        self.and_i_select_no_the_symptom_has_not_been_investigated()
        self.and_i_click_save_symptom()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_lump_on_the_right_breast_is_listed()
        self.and_the_message_says_symptom_added()

    def test_changing_a_symptom(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_with_a_symptom_added_in_the_last_three_months()
        self.and_i_am_on_the_record_medical_information_page()
        self.when_i_click_on_change()
        self.then_less_than_three_months_should_be_selected()

        self.when_i_select_three_months_to_a_year()
        self.and_i_click_save_symptom()

        self.then_i_am_back_on_the_medical_information_page()
        self.and_i_see_three_months_to_a_year()

    def test_removing_a_symptom(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_with_a_symptom_added_in_the_last_three_months()
        self.and_i_am_on_the_record_medical_information_page()
        self.when_i_click_on_change()
        self.and_i_click_on_delete_this_symptom()
        self.and_i_confirm_i_want_to_delete_the_symptom()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_message_says_symptom_deleted()
        self.and_the_lump_is_no_longer_listed()

    def test_adding_a_symptom_with_errors(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.when_i_click_on_lump()
        self.and_i_select_less_than_three_months()
        self.and_i_select_no_the_symptom_has_not_been_investigated()
        self.and_i_click_save_symptom()
        self.then_i_am_prompted_to_enter_the_location_of_the_lump()

        self.when_i_select_right_breast()
        self.and_i_click_save_symptom()
        self.then_i_am_prompted_to_enter_the_specific_area()

        self.when_i_enter_the_area()
        self.and_i_click_save_symptom()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_lump_on_the_right_breast_is_listed()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.when_i_click_on_lump()
        self.then_the_accessibility_baseline_is_met()

    def and_there_is_an_appointment(self):
        self.participant = ParticipantFactory(first_name="Janet", last_name="Williams")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(
            screening_episode=self.screening_episode,
            clinic_slot__clinic__setting__provider=self.current_provider,
            current_status_params={
                "name": AppointmentStatusNames.IN_PROGRESS,
                "created_by": self.current_user,
            },
        )

    def and_there_is_an_appointment_with_a_symptom_added_in_the_last_three_months(self):
        self.participant = ParticipantFactory(first_name="Janet", last_name="Williams")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(
            screening_episode=self.screening_episode,
            clinic_slot__clinic__setting__provider=self.current_provider,
        )
        self.symptom = SymptomFactory(
            appointment=self.appointment,
            swelling_or_shape_change=True,
            when_started=RelativeDateChoices.LESS_THAN_THREE_MONTHS,
        )

    def and_i_am_on_the_record_medical_information_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": self.appointment.pk},
            )
        )

    def when_i_click_on_lump(self):
        self.page.get_by_role("button").and_(
            self.page.get_by_text("Lump", exact=True)
        ).click()

    def then_i_see_the_add_a_lump_form(self):
        expect(self.page.get_by_text("Details of the lump")).to_be_visible()
        self.assert_page_title_contains("Details of the lump")

    def and_i_see_the_appointment_status_bar(self):
        status_bar = self.page.locator("div.app-status-bar")
        expect(status_bar).to_contain_text(
            format_nhs_number(self.participant.nhs_number)
        )
        expect(status_bar).to_contain_text(self.participant.full_name)

    def when_i_select_right_breast(self):
        self.page.get_by_label("Right breast", exact=True).click()

    def and_i_enter_the_area(self):
        self.page.get_by_label("Describe the specific area: right breast").filter(
            visible=True
        ).fill("ldq")

    when_i_enter_the_area = and_i_enter_the_area

    def and_i_select_less_than_three_months(self):
        self.page.get_by_label("Less than 3 months").click()

    def when_i_select_three_months_to_a_year(self):
        self.page.get_by_label("3 months to a year").click()

    def and_i_select_no_the_symptom_has_not_been_investigated(self):
        legend = self.page.get_by_text("Has this been investigated?")
        fieldset = self.page.get_by_role("group").filter(has=legend)
        fieldset.get_by_label("No").click()

    def and_i_click_save_symptom(self):
        self.page.get_by_text("Save symptom").click()

    def then_i_am_back_on_the_medical_information_page(self):
        self.expect_url("mammograms:record_medical_information", pk=self.appointment.pk)

    def and_the_lump_on_the_right_breast_is_listed(self):
        key = self.page.locator(
            ".nhsuk-summary-list__key", has=self.page.get_by_text("Lump", exact=True)
        )
        row = self.page.locator(".nhsuk-summary-list__row").filter(has=key)
        expect(row).to_contain_text("Right breast")

    def when_i_click_on_change(self):
        key = self.page.locator(
            ".nhsuk-summary-list__key",
            has=self.page.get_by_text("Swelling or shape change", exact=True),
        )
        row = self.page.locator(".nhsuk-summary-list__row").filter(has=key)
        row.locator(".nhsuk-summary-list__actions").get_by_text(
            "Change swelling or shape change"
        ).click()

    def then_less_than_three_months_should_be_selected(self):
        expect(self.page.get_by_label("Less than 3 months")).to_be_checked()

    def and_i_see_three_months_to_a_year(self):
        key = self.page.locator(
            ".nhsuk-summary-list__key",
            has=self.page.get_by_text("Swelling or shape change", exact=True),
        )
        row = self.page.locator(".nhsuk-summary-list__row").filter(has=key)
        expect(row).to_contain_text("3 months to a year")

    def and_i_click_on_delete_this_symptom(self):
        self.page.get_by_text("Delete this symptom").click()

    def and_i_confirm_i_want_to_delete_the_symptom(self):
        self.page.get_by_text("Delete symptom").click()

    def and_the_lump_is_no_longer_listed(self):
        locator = self.page.locator(
            ".nhsuk-summary-list__key", has=self.page.get_by_text("Lump", exact=True)
        )
        expect(locator).not_to_be_attached()

    def then_i_am_prompted_to_enter_the_location_of_the_lump(self):
        self.expect_validation_error(
            error_text="Select the location of the lump",
            fieldset_legend="Where is the lump located?",
            field_label="Right breast",
        )

    def then_i_am_prompted_to_enter_the_specific_area(self):
        self.expect_validation_error(
            error_text="Describe the specific area where the lump is located",
            fieldset_legend="Where is the lump located?",
            field_label="Describe the specific area: right breast",
            field_name="area_description_right_breast",
        )

    def and_the_message_says_symptom_deleted(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Symptom deleted")
        expect(alert).to_contain_text("Deleted swelling or shape change.")

    def and_the_message_says_symptom_added(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Symptom added")
        expect(alert).to_contain_text("Added lump.")
