import os

from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.dicom.tests.factories import (
    ImageFactory,
    StudyFactory,
)
from manage_breast_screening.gateway.tests.factories import (
    GatewayActionFactory,
    RelayFactory,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
)

from ..system_test_setup import SystemTestCase


class TestGatewayImages(SystemTestCase):
    def test_renders_no_images_content(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.when_i_visit_the_take_images_page()

        self.then_i_see_the_image_stream_container()
        self.and_the_container_has_the_correct_stream_url()
        self.and_i_see_the_no_images_message()
        self.and_i_see_the_images_troubleshooting_content()

    def test_renders_images(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_gateway_images_are_enabled()
        self.and_there_are_images_for_the_appointment()
        self.when_i_visit_the_take_images_page()

        self.then_i_see_the_image_stream_container()
        self.and_i_see_the_images()

        self.when_i_fill_in_additional_details_for_the_images()
        self.and_i_click_confirm_images()
        self.then_i_see_the_image_counts_on_the_check_information_page()

    def and_there_is_an_appointment(self):
        self.appointment = AppointmentFactory(
            clinic_slot__clinic__setting__provider=self.current_provider,
        )

    def and_gateway_images_are_enabled(self):
        os.environ["GATEWAY_IMAGES_ENABLED"] = "true"
        RelayFactory(provider=self.appointment.provider)

    def when_i_visit_the_take_images_page(self):
        self.page.goto(
            self.live_server_url
            + reverse("mammograms:gateway_images", kwargs={"pk": self.appointment.pk})
        )

    def then_i_see_the_image_stream_container(self):
        container = self.page.locator("[data-module='app-image-stream']")
        expect(container).to_be_visible()

    def and_the_container_has_the_correct_stream_url(self):
        container = self.page.locator("[data-module='app-image-stream']")
        expected_url = reverse(
            "mammograms:appointment_images_stream", kwargs={"pk": self.appointment.pk}
        )
        expect(container).to_have_attribute("data-stream-url", expected_url)

    def and_i_see_the_no_images_message(self):
        expect(
            self.page.get_by_text(
                "Mammography images will appear below once they have been received"
            )
        ).to_be_visible()

    def and_i_see_the_images_troubleshooting_content(self):
        expect(self.page.get_by_text("Troubleshoot issues with images")).to_be_visible()
        expect(
            self.page.get_by_text("Technical issues with the mammogram machine")
        ).to_be_visible()

    def and_there_are_images_for_the_appointment(self):
        study = StudyFactory()
        GatewayActionFactory.create(
            appointment=self.appointment,
            id=study.source_message_id,
        )
        ImageFactory.create(series__study=study, laterality="R", view_position="MLO")
        ImageFactory.create(series__study=study, laterality="R", view_position="CC")
        ImageFactory.create(series__study=study, laterality="R", view_position="CC")
        ImageFactory.create(series__study=study, laterality="L", view_position="MLO")
        ImageFactory.create(series__study=study, laterality="L", view_position="CC")

    def and_i_see_the_images(self):
        expect(self.page.get_by_text("1× RMLO")).to_be_visible()
        expect(self.page.get_by_text("2× RCC")).to_be_visible()
        expect(self.page.get_by_text("1× LMLO")).to_be_visible()
        expect(self.page.get_by_text("1× LCC")).to_be_visible()

    def when_i_fill_in_additional_details_for_the_images(self):
        self.page.get_by_label("Notes for reader (optional)").fill(
            "Some additional details"
        )

    def and_i_click_confirm_images(self):
        self.page.get_by_role("button", name="Confirm images").click()

    def then_i_see_the_image_counts_on_the_check_information_page(self):
        expect(
            self.page.get_by_role("heading", name="Check information")
        ).to_be_visible()
        expect(self.page.get_by_text("1× RMLO")).to_be_visible()
        expect(self.page.get_by_text("2× RCC")).to_be_visible()
        expect(self.page.get_by_text("1× LMLO")).to_be_visible()
        expect(self.page.get_by_text("1× LCC")).to_be_visible()
