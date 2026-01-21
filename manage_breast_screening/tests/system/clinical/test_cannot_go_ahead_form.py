import re

from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.participants.models.appointment import (
    AppointmentStatusNames,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)

from ..system_test_setup import SystemTestCase


class TestUserSubmitsCannotGoAheadForm(SystemTestCase):
    def test_user_submits_cannot_go_ahead_form(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_cannot_go_ahead_form()
        self.when_i_submit_the_form()
        self.then_i_should_see_validation_errors()

        self.when_i_select_a_reason_for_the_appointment_being_stopped()
        self.and_i_select_other_as_a_reason()
        self.and_i_choose_to_add_the_participant_to_the_reinvite_list()
        self.when_i_submit_the_form()
        self.then_i_see_an_error_for_other_details()

        self.when_i_fill_in_other_details()
        self.when_i_submit_the_form()
        self.then_i_see_the_clinics_page()
        self.and_the_appointment_is_updated()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_cannot_go_ahead_form()
        self.then_the_accessibility_baseline_is_met()

    def and_there_is_an_appointment(self):
        self.participant = ParticipantFactory()
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(
            screening_episode=self.screening_episode,
            clinic_slot__clinic__setting__provider=self.current_provider,
        )

    def and_i_am_on_the_cannot_go_ahead_form(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:appointment_cannot_go_ahead",
                kwargs={"pk": self.appointment.pk},
            )
        )
        self.assert_page_title_contains("Appointment cannot go ahead")

    def when_i_submit_the_form(self):
        self.page.get_by_role("button", name="Continue").click()

    def then_i_should_see_validation_errors(self):
        self.expect_validation_error(
            error_text="A reason for why this appointment cannot continue must be provided",
            fieldset_legend="Why has this appointment been stopped?",
            field_label="Participant did not attend",
        )
        self.expect_validation_error(
            error_text="Select whether the participant needs to be invited for another appointment",
            fieldset_legend="Does the appointment need to be rescheduled?",
            field_label="Yes, add participant to reinvite list",
        )

    def when_i_select_a_reason_for_the_appointment_being_stopped(self):
        self.page.get_by_label("Failed identity check").check()

    def and_i_select_other_as_a_reason(self):
        self.page.get_by_label("Other").check()

    def and_i_choose_to_add_the_participant_to_the_reinvite_list(self):
        self.page.get_by_label("Yes, add participant to reinvite list").click()
        expect(
            self.page.get_by_label("Yes, add participant to reinvite list")
        ).to_be_checked()

    def then_i_see_an_error_for_other_details(self):
        self.expect_validation_error(
            error_text="Explain why this appointment cannot proceed",
            fieldset_legend="Why has this appointment been stopped?",
            field_label="Provide details",
            field_name="other_details",
        )

    def when_i_fill_in_other_details(self):
        self.page.locator("#id_other_details").fill("Explain other choice")

    def then_i_see_the_clinics_page(self):
        expect(self.page).to_have_url(re.compile(reverse("clinics:index")))

    def and_the_appointment_is_updated(self):
        self.appointment.refresh_from_db()
        self.assertEqual(
            self.appointment.current_status.name,
            AppointmentStatusNames.ATTENDED_NOT_SCREENED,
        )
        self.assertEqual(self.appointment.reinvite, True)
        self.assertEqual(
            self.appointment.stopped_reasons,
            {
                "stopped_reasons": ["failed_identity_check", "other"],
                "other_details": "Explain other choice",
            },
        )
