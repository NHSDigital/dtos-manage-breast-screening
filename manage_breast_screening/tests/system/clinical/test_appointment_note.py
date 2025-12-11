from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.participants.tests.factories import AppointmentFactory

from ..system_test_setup import SystemTestCase


class TestAppointmentNote(SystemTestCase):
    def test_clinical_user_adds_and_updates_an_appointment_note(self):
        self.initial_note_text = "Participant prefers an evening appointment."
        self.updated_note_text = "Participant prefers morning appointments only."

        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_for_my_provider()
        self.and_i_am_on_the_appointment_note_page()

        self.when_i_save_the_note()
        self.then_i_see_a_validation_error()

        self.when_i_enter_a_note()
        self.and_i_save_the_note()
        self.then_i_see_a_message_confirming_the_save()
        self.and_the_note_field_contains(self.initial_note_text)
        self.and_the_appointment_details_tab_shows_the_note(self.initial_note_text)

        self.when_i_update_the_note()
        self.and_i_save_the_note()
        self.then_i_see_a_message_confirming_the_save()
        self.and_the_note_field_contains(self.updated_note_text)
        self.and_the_appointment_details_tab_shows_the_note(self.updated_note_text)

        self.when_i_click_the_note_change_link()
        self.and_i_click_delete_note()
        self.and_i_click_cancel()
        self.then_the_note_is_not_deleted()

        self.when_i_click_delete_note()
        self.and_i_confirm_deletion()
        self.then_the_note_is_deleted()

    def and_there_is_an_appointment_for_my_provider(self):
        self.appointment = AppointmentFactory(
            clinic_slot__clinic__setting__provider=self.current_provider
        )

    def and_i_am_on_the_appointment_note_page(self):
        self.page.goto(
            self.live_server_url
            + reverse("mammograms:appointment_note", kwargs={"pk": self.appointment.pk})
        )
        self.expect_url("mammograms:appointment_note", pk=self.appointment.pk)

    def then_i_see_a_validation_error(self):
        self.expect_validation_error(
            error_text="Enter a note",
            field_label="Note",
        )

    def when_i_enter_a_note(self):
        self.page.get_by_label("Note").fill(self.initial_note_text)

    def when_i_update_the_note(self):
        secondary_nav = self.page.locator(".app-secondary-navigation")
        expect(secondary_nav).to_be_visible()
        note_tab = secondary_nav.get_by_text("Note")
        note_tab.click()
        field = self.page.get_by_label("Note")
        expect(field).to_have_value(self.initial_note_text)
        field.fill(self.updated_note_text)

    def and_i_save_the_note(self):
        self.page.get_by_role("button", name="Save note").click()
        self.expect_url("mammograms:appointment_note", pk=self.appointment.pk)

    def when_i_save_the_note(self):
        self.and_i_save_the_note()

    def and_the_note_field_contains(self, text):
        expect(self.page.get_by_label("Note")).to_have_value(text)

    def then_i_see_a_message_confirming_the_save(self):
        banner = self.page.locator(".nhsuk-notification-banner--success")
        expect(banner).to_be_visible()
        expect(banner).to_contain_text("Appointment note saved")

    def and_the_appointment_details_tab_shows_the_note(self, text):
        secondary_nav = self.page.locator(".app-secondary-navigation")
        expect(secondary_nav).to_be_visible()
        appointment_details_tab = secondary_nav.get_by_text("Appointment details")
        appointment_details_tab.click()

        note_container = self.page.locator(
            ".nhsuk-warning-callout", has_text="Appointment note"
        )
        expect(note_container).to_be_visible()
        expect(note_container).to_contain_text(text)

    def when_i_click_the_note_change_link(self):
        note_container = self.page.locator(
            ".nhsuk-warning-callout", has_text="Appointment note"
        )
        expect(note_container).to_be_visible()
        change_link = note_container.get_by_role("link", name="Change")
        change_link.click()

    def and_i_click_delete_note(self):
        delete_link = self.page.get_by_role("link", name="Delete appointment note")
        expect(delete_link).to_be_visible()
        delete_link.click()

    def when_i_click_delete_note(self):
        self.and_i_click_delete_note()

    def and_i_click_cancel(self):
        cancel_link = self.page.get_by_role("link", name="Cancel")
        expect(cancel_link).to_be_visible()
        cancel_link.click()

    def then_the_note_is_not_deleted(self):
        expect(self.page.get_by_label("Note")).to_have_value(self.updated_note_text)

    def and_i_confirm_deletion(self):
        delete_button = self.page.get_by_role("button", name="Delete appointment note")
        expect(delete_button).to_be_visible()
        delete_button.click()

    def then_the_note_is_deleted(self):
        banner = self.page.locator(".nhsuk-notification-banner--success")
        expect(banner).to_be_visible()
        expect(banner).to_contain_text("Appointment note deleted")
        expect(self.page.get_by_label("Note")).to_have_value("")
