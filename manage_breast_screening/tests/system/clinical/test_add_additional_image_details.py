import re

from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.participants.tests.factories import AppointmentFactory

from ..system_test_setup import SystemTestCase


class TestAddAdditionalImageDetails(SystemTestCase):
    def test_add_additional_image_details(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_for_my_provider()
        self.and_i_am_on_the_add_additional_image_details_page()

        self.when_i_enter_the_number_of_images_taken()
        self.and_i_click_on_continue()
        self.then_i_should_be_on_the_check_information_page()
        self.and_the_message_says_image_details_added()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_for_my_provider()
        self.and_i_am_on_the_add_additional_image_details_page()
        self.then_the_accessibility_baseline_is_met()

    def and_there_is_an_appointment_for_my_provider(self):
        self.appointment = AppointmentFactory(
            clinic_slot__clinic__setting__provider=self.current_provider
        )

    def and_i_am_on_the_add_additional_image_details_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:add_additional_image_details",
                kwargs={"pk": self.appointment.pk},
            )
        )
        self.expect_url(
            "mammograms:add_additional_image_details", pk=self.appointment.pk
        )

    def when_i_enter_the_number_of_images_taken(self):
        self.page.get_by_label("RMLO").fill("1")
        self.page.get_by_label("RCC").fill("0")
        self.page.get_by_label("Right Eklund").fill("0")
        self.page.get_by_label("LMLO").fill("0")
        self.page.get_by_label("LCC").fill("0")
        self.page.get_by_label("Left Eklund").fill("0")

    def and_i_click_on_continue(self):
        self.page.get_by_text("Continue").click()

    def then_i_should_be_on_the_check_information_page(self):
        path = reverse(
            "mammograms:check_information",
            kwargs={"pk": self.appointment.pk},
        )
        expect(self.page).to_have_url(re.compile(path))
        self.assert_page_title_contains("Check Information")

    def and_the_message_says_image_details_added(self):
        alert = self.page.get_by_role("alert")
        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Added image details")
