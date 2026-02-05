from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
)

from ..system_test_setup import SystemTestCase


class TestTakeImages(SystemTestCase):
    def test_renders_image_stream_container_with_sse_attributes(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.when_i_visit_the_take_images_page()

        self.then_i_see_the_image_stream_container()
        self.and_the_container_has_the_correct_stream_url()
        self.and_i_see_the_no_images_message()

    def and_there_is_an_appointment(self):
        self.appointment = AppointmentFactory(
            clinic_slot__clinic__setting__provider=self.current_provider,
        )

    def when_i_visit_the_take_images_page(self):
        self.page.goto(
            self.live_server_url
            + reverse("mammograms:take_images", kwargs={"pk": self.appointment.pk})
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
        expect(self.page.get_by_text("No images received yet")).to_be_visible()
