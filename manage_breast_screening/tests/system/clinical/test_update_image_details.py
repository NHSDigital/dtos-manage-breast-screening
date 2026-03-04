import re

from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.manual_images.models import Series, Study
from manage_breast_screening.participants.models.appointment import (
    AppointmentWorkflowStepCompletion,
)
from manage_breast_screening.participants.tests.factories import AppointmentFactory

from ..system_test_setup import SystemTestCase


class TestUpdateImageDetails(SystemTestCase):
    def test_update_image_details(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_with_existing_image_details()
        self.and_i_am_on_the_check_information_page()

        self.when_i_click_take_images_in_the_workflow_nav()
        self.then_i_should_be_on_the_update_image_details_page()
        self.and_the_rmlo_field_reflects_the_db_value()

        self.when_i_update_the_rmlo_count(1)
        self.and_i_click_continue()
        self.then_i_should_be_on_the_check_information_page()
        self.and_the_image_details_show_the_updated_rmlo_count()

    def and_there_is_an_appointment_with_existing_image_details(self):
        self.appointment = AppointmentFactory(
            clinic_slot__clinic__setting__provider=self.current_provider,
        )
        study = Study.objects.create(appointment=self.appointment)
        Series.objects.create(study=study, view_position="MLO", laterality="R", count=3)
        Series.objects.create(study=study, view_position="CC", laterality="R", count=1)
        Series.objects.create(study=study, view_position="MLO", laterality="L", count=1)
        Series.objects.create(study=study, view_position="CC", laterality="L", count=1)
        AppointmentWorkflowStepCompletion.objects.create(
            appointment=self.appointment,
            step_name=AppointmentWorkflowStepCompletion.StepNames.TAKE_IMAGES,
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

    def when_i_click_take_images_in_the_workflow_nav(self):
        nav = self.page.locator("nav.app-workflow-side-nav")
        nav.get_by_text("Take images").click()

    def then_i_should_be_on_the_update_image_details_page(self):
        path = reverse(
            "mammograms:update_image_details",
            kwargs={"pk": self.appointment.pk},
        )
        expect(self.page).to_have_url(re.compile(path))
        self.assert_page_title_contains("Edit image details")

    def and_the_rmlo_field_reflects_the_db_value(self):
        expect(self.page.get_by_label("RMLO")).to_have_value("3")

    def when_i_update_the_rmlo_count(self, count):
        self.page.get_by_label("RMLO").fill(str(count))

    def and_i_click_continue(self):
        self.page.get_by_text("Continue").click()

    def then_i_should_be_on_the_check_information_page(self):
        path = reverse(
            "mammograms:check_information",
            kwargs={"pk": self.appointment.pk},
        )
        expect(self.page).to_have_url(re.compile(path))
        self.assert_page_title_contains("Check information")

    def and_the_image_details_show_the_updated_rmlo_count(self):
        row = self.page.locator(".nhsuk-summary-list__row", has_text="Views taken")
        expect(row.locator(".nhsuk-summary-list__value")).to_contain_text("1× RMLO")
