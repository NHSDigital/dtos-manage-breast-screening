import unittest
from datetime import date

import time_machine
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
from manage_breast_screening.tests.system.system_test_setup import SystemTestCase


@time_machine.travel(date(2025, 1, 1))
class TestRecordingBreastFeatures(SystemTestCase):
    def test_recording_breast_features(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_with_no_medical_information_added()
        self.and_i_am_on_the_record_medical_information_page()
        self.then_i_see_that_there_are_no_breast_features()

        self.when_i_click_on_add_breast_features()
        self.then_i_am_on_the_breast_feature_form()

        self.when_i_click_on_the_right_central_region()
        self.and_i_save_the_form()
        self.then_i_am_back_on_the_record_medical_information_page()
        self.and_i_see_the_feature_is_added()

        self.when_i_click_on_the_view_or_edit_button()
        self.then_i_am_on_the_breast_feature_form()

        self.when_i_save_the_form()
        self.then_i_am_back_on_the_record_medical_information_page()
        self.and_i_see_the_feature_is_added()

    @unittest.skip("Needs additional work")
    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_with_no_medical_information_added()
        self.and_i_am_on_the_record_breast_features_page()
        self.then_the_accessibility_baseline_is_met()

    def and_there_is_an_appointment_with_no_medical_information_added(self):
        self.participant = ParticipantFactory(first_name="Janet", last_name="Williams")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(
            screening_episode=self.screening_episode,
            clinic_slot__clinic__setting__provider=self.current_provider,
            current_status_params={
                "name": AppointmentStatusNames.IN_PROGRESS,
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

    def and_i_am_on_the_record_breast_features_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:record_breast_features",
                kwargs={"pk": self.appointment.pk},
            )
        )

    def then_i_see_that_there_are_no_breast_features(self):
        card = self.page.locator("#breast-features")
        expect(card).to_contain_text(
            "No breast features have been recorded for this participant."
        )

    def when_i_click_on_add_breast_features(self):
        self.page.get_by_text("Add a feature").click()

    def then_i_am_on_the_breast_feature_form(self):
        self.assert_page_title_contains("Record breast features")
        self.expect_url("mammograms:record_breast_features", pk=self.appointment.pk)

    def when_i_click_on_the_right_central_region(self):
        self.page.locator(".app-breast-diagram__regions-right .right_central").click(
            force=True
        )

    def and_i_save_the_form(self):
        self.page.get_by_role("button").filter(has_text="Save").click()

    when_i_save_the_form = and_i_save_the_form

    def then_i_am_back_on_the_record_medical_information_page(self):
        self.expect_url("mammograms:record_medical_information", pk=self.appointment.pk)

    def and_i_see_the_feature_is_added(self):
        card = self.page.locator("#breast-features")
        expect(card).to_contain_text("1 breast feature recorded")

    def when_i_click_on_the_view_or_edit_button(self):
        self.page.get_by_text("View or edit breast features").click()
