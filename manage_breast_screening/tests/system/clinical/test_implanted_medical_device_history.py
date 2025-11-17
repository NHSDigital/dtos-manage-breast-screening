from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)

from ..system_test_setup import SystemTestCase


class TestImplantedMedicalDeviceHistory(SystemTestCase):
    def test_adding_a_device(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.when_i_click_on_add_a_implanted_medical_device()
        self.then_i_see_the_add_a_implanted_medical_device_form()

        self.when_i_select_hickman_line()
        self.and_i_click_save_device()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_device_is_listed()
        self.and_the_message_says_device_added()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.when_i_click_on_add_a_implanted_medical_device()
        self.then_the_accessibility_baseline_is_met()

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

    def when_i_click_on_add_a_implanted_medical_device(self):
        self.page.get_by_text("Add implanted medical device history").click()

    def then_i_see_the_add_a_implanted_medical_device_form(self):
        expect(
            self.page.get_by_text("Add details of implanted medical device")
        ).to_be_visible()
        self.assert_page_title_contains("Details of the implanted medical device")

    def when_i_select_hickman_line(self):
        self.page.get_by_label("Hickman line", exact=True).click()

    def and_i_click_save_device(self):
        self.page.get_by_text("Save").click()

    def then_i_am_back_on_the_medical_information_page(self):
        self.expect_url("mammograms:record_medical_information", pk=self.appointment.pk)

    def and_the_device_is_listed(self):
        key = self.page.locator(
            ".nhsuk-summary-list__key",
            has=self.page.get_by_text("Implanted medical device history", exact=True),
        )
        row = self.page.locator(".nhsuk-summary-list__row").filter(has=key)
        expect(row).to_contain_text("Hickman line")

    def and_the_message_says_device_added(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Implanted medical device added")
