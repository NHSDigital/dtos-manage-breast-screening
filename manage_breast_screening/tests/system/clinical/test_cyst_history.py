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


class TestRecordingCyst(SystemTestCase):
    def test_adding_and_changing_cyst(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.and_i_see_the_appointment_status_bar()
        self.when_i_click_on_cysts()
        self.then_i_see_the_add_cyst_form()
        self.and_i_see_the_appointment_status_bar()

        self.when_i_select_no_treatment()
        self.and_i_click_save()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_cyst_is_listed()
        self.and_the_message_says_cyst_added()

        self.when_i_click_change()
        self.then_i_see_the_edit_cyst_form()
        self.when_i_select_drainage_or_removal()
        self.and_i_click_save()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_cyst_is_updated()
        self.and_the_message_says_cyst_updated()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.when_i_click_on_cysts()
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

    def when_i_click_on_cysts(self):
        self.page.get_by_role("button").filter(has_text="Cysts").click()

    def then_i_see_the_add_cyst_form(self):
        expect(self.page.get_by_text("Add details of cysts")).to_be_visible()
        self.assert_page_title_contains("Add details of cysts")

    def and_i_see_the_appointment_status_bar(self):
        status_bar = self.page.locator("div.app-status-bar")
        expect(status_bar).to_contain_text(
            format_nhs_number(self.participant.nhs_number)
        )
        expect(status_bar).to_contain_text(self.participant.full_name)

    def when_i_select_no_treatment(self):
        self.page.get_by_label("No treatment", exact=True).click()

    def and_i_click_save(self):
        self.page.get_by_text("Save").click()

    def then_i_am_back_on_the_medical_information_page(self):
        self.expect_url("mammograms:record_medical_information", pk=self.appointment.pk)

    def and_the_cyst_is_listed(self):
        heading = self.page.get_by_role("heading").filter(has_text="Cysts")
        section = self.page.locator("section").filter(has=heading)
        row = section.locator(".app-nested-info__row", has_text="Treatment")
        expect(row).to_contain_text("No treatment")

    def and_the_message_says_cyst_added(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Added cysts")

    def then_i_see_the_edit_cyst_form(self):
        expect(self.page.get_by_text("Edit details of cysts")).to_be_visible()
        self.assert_page_title_contains("Edit details of cysts")

    def when_i_click_change(self):
        self.page.get_by_text("Change (cysts)").click()

    def when_i_select_drainage_or_removal(self):
        self.page.get_by_label("Drainage or removal").click()

    def and_the_cyst_is_updated(self):
        heading = self.page.get_by_role("heading").filter(has_text="Cysts")
        section = self.page.locator("section").filter(has=heading)
        row = section.locator(".app-nested-info__row", has_text="Treatment")
        expect(row).to_contain_text("Drainage or removal")

    def and_the_message_says_cyst_updated(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Updated cysts")
