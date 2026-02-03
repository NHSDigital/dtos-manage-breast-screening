import re

from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.participants.tests.factories import AppointmentFactory

from ..system_test_setup import SystemTestCase


class TestAddImageDetails(SystemTestCase):
    def test_add_image_details(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_for_my_provider()
        self.and_i_am_on_the_add_image_details_page()
        self.and_the_take_images_step_is_active()
        self.then_images_taken_count_is(4)
        self.and_repeat_images_message_is_hidden()

        self.when_i_enter_the_number_of_images_taken("RMLO", 2)
        self.then_images_taken_count_is(5)
        self.and_repeat_images_message_is_visible()
        self.when_i_enter_the_number_of_images_taken("RMLO", 0)
        self.then_images_taken_count_is(3)
        self.and_repeat_images_message_is_hidden()

        self.when_i_enter_the_number_of_images_taken("RCC", 20)
        self.then_images_taken_count_is(22)
        self.and_repeat_images_message_is_visible()
        self.when_i_enter_the_number_of_images_taken("RCC", 1)
        self.then_images_taken_count_is(3)
        self.and_repeat_images_message_is_hidden()

        self.when_i_enter_the_number_of_images_taken("Right Eklund", 7)
        self.then_images_taken_count_is(10)
        self.and_repeat_images_message_is_visible()
        self.when_i_enter_the_number_of_images_taken("Right Eklund", 0)
        self.then_images_taken_count_is(3)
        self.and_repeat_images_message_is_hidden()

        self.when_i_enter_the_number_of_images_taken("LMLO", 5)
        self.then_images_taken_count_is(7)
        self.and_repeat_images_message_is_visible()
        self.when_i_enter_the_number_of_images_taken("LMLO", 1)
        self.then_images_taken_count_is(3)
        self.and_repeat_images_message_is_hidden()

        self.when_i_enter_the_number_of_images_taken("LCC", 2)
        self.then_images_taken_count_is(4)
        self.and_repeat_images_message_is_visible()
        self.when_i_enter_the_number_of_images_taken("LCC", 1)
        self.then_images_taken_count_is(3)
        self.and_repeat_images_message_is_hidden()

        self.when_i_enter_the_number_of_images_taken("Left Eklund", 19)
        self.then_images_taken_count_is(22)
        self.and_repeat_images_message_is_visible()
        self.when_i_enter_the_number_of_images_taken("Left Eklund", 0)
        self.then_images_taken_count_is(3)
        self.and_repeat_images_message_is_hidden()

        self.when_i_select_not_all_images_taken()
        self.and_i_select_unable_to_scan_tissue()
        self.and_i_select_partial_mammography()

        self.and_i_click_on_continue()
        self.then_i_should_be_on_the_check_information_page()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_for_my_provider()
        self.and_i_am_on_the_add_image_details_page()
        self.then_the_accessibility_baseline_is_met()

    def and_there_is_an_appointment_for_my_provider(self):
        self.appointment = AppointmentFactory(
            clinic_slot__clinic__setting__provider=self.current_provider
        )

    def and_i_am_on_the_add_image_details_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:add_image_details",
                kwargs={"pk": self.appointment.pk},
            )
        )
        self.expect_url("mammograms:add_image_details", pk=self.appointment.pk)

    def and_the_take_images_step_is_active(self):
        nav = self.page.locator("nav.app-workflow-side-nav")
        expect(nav).to_be_visible()
        current_step = nav.locator(
            ".app-workflow-side-nav__item--current .app-workflow-side-nav__label"
        )
        expect(current_step).to_have_count(1)
        expect(current_step).to_have_text("Take images")

    def when_i_enter_the_number_of_images_taken(self, image_type, count):
        self.page.get_by_label(image_type).fill(str(count))

    def then_images_taken_count_is(self, expected_count):
        expect(self.page.get_by_text(f"Images taken: {expected_count}")).to_be_visible()

    def and_repeat_images_message_is_hidden(self):
        expect(
            self.page.get_by_text(
                "Repeat or extra image details captured on the next screen"
            )
        ).to_be_hidden()

    def and_repeat_images_message_is_visible(self):
        expect(
            self.page.get_by_text(
                "Repeat or extra image details captured on the next screen"
            )
        ).to_be_visible()

    def and_i_click_on_continue(self):
        self.page.get_by_text("Continue").click()

    def then_i_should_be_on_the_check_information_page(self):
        path = reverse(
            "mammograms:check_information",
            kwargs={"pk": self.appointment.pk},
        )
        expect(self.page).to_have_url(re.compile(path))
        self.assert_page_title_contains("Check information")

    def when_i_select_not_all_images_taken(self):
        self.page.get_by_label("Not all mammograms taken").click()

    def and_i_select_unable_to_scan_tissue(self):
        self.page.get_by_label("Unable to scan tissue").click()

    def and_i_select_partial_mammography(self):
        self.page.get_by_label("No, record as 'partial mammography'").click()
