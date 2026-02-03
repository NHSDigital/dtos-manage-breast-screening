import re

from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.participants.tests.factories import AppointmentFactory

from ..system_test_setup import SystemTestCase


class TestMultipleImagesInformation(SystemTestCase):
    LCC_LEGEND = "3 Left CC images were taken. Were the additional images repeats?"
    RMLO_LEGEND = "2 Right MLO images were taken. Was the additional image a repeat?"

    def test_multiple_images_information_flow(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_for_my_provider()
        self.and_i_am_on_the_add_image_details_page()
        self.when_i_fill_in_image_counts(rmlo=2, lcc=3)
        self.and_i_click_on_continue()
        self.then_i_should_be_on_the_multiple_images_information_page()

        self.when_i_click_on_continue()
        self.then_i_should_see_lcc_validation_error()
        self.and_i_should_see_rmlo_validation_error()

        self.when_i_complete_the_form()
        self.and_i_click_on_continue()
        self.then_i_should_be_on_the_check_information_page()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_for_my_provider()
        self.and_i_am_on_the_add_image_details_page()
        self.when_i_fill_in_image_counts(rmlo=2, lcc=3)
        self.and_i_click_on_continue()
        self.then_i_should_be_on_the_multiple_images_information_page()
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

    def when_i_fill_in_image_counts(
        self, rmlo=0, rcc=0, right_eklund=0, lmlo=0, lcc=0, left_eklund=0
    ):
        self.page.get_by_label("RMLO").fill(str(rmlo))
        self.page.get_by_label("RCC").fill(str(rcc))
        self.page.get_by_label("Right Eklund").fill(str(right_eklund))
        self.page.get_by_label("LMLO").fill(str(lmlo))
        self.page.get_by_label("LCC").fill(str(lcc))
        self.page.get_by_label("Left Eklund").fill(str(left_eklund))

    def and_i_click_on_continue(self):
        self.page.get_by_role("button", name="Continue").first.click()

    def when_i_click_on_continue(self):
        self.and_i_click_on_continue()

    def then_i_should_be_on_the_multiple_images_information_page(self):
        self.expect_url(
            "mammograms:add_multiple_images_information", pk=self.appointment.pk
        )
        self.assert_page_title_contains("Add image information")

    def then_i_should_see_lcc_validation_error(self):
        self.expect_validation_error(
            error_text="Select whether the additional Left CC images were repeats",
            field_label="Yes, all images were repeats",
            fieldset_legend=self.LCC_LEGEND,
        )

    def and_i_should_see_rmlo_validation_error(self):
        self.expect_validation_error(
            error_text="Select whether the additional Right MLO images were repeats",
            field_label="Yes, it was a repeat",
            fieldset_legend=self.RMLO_LEGEND,
        )

    def when_i_complete_the_form(self):
        self.fill_in_series(
            self.LCC_LEGEND,
            "Yes, all images were repeats",
            "Patient moved during exposure",
        )
        self.fill_in_series(
            self.RMLO_LEGEND,
            "Yes, it was a repeat",
            "Motion blur affecting image quality",
        )

    def fill_in_series(self, legend_text, repeat_type_label, reason_label):
        fieldset = self.get_fieldset_by_legend(legend_text)
        fieldset.get_by_label(repeat_type_label).check()
        fieldset.get_by_label(reason_label).check()

    def then_i_should_be_on_the_check_information_page(self):
        path = reverse(
            "mammograms:check_information",
            kwargs={"pk": self.appointment.pk},
        )
        expect(self.page).to_have_url(re.compile(path))
        self.assert_page_title_contains("Check information")
