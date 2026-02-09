from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.clinics.models import Clinic
from manage_breast_screening.core.utils.string_formatting import format_nhs_number
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)

from ..system_test_setup import SystemTestCase


class TestMammogramWorkflow(SystemTestCase):
    def test_completing_workflow(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_appointment_show_page()

        self.when_i_click_start_this_appointment()
        self.then_i_should_be_on_the_confirm_identity_page()
        self.and_i_see_the_appointment_status_bar()
        self.and_the_confirm_identity_step_is_active()

        self.when_i_click_confirm_identity()
        self.then_i_should_be_on_the_record_medical_information_page()
        self.and_i_see_the_appointment_status_bar()
        self.and_the_review_medical_information_step_is_active()

        self.when_i_mark_that_imaging_can_go_ahead()
        self.then_i_should_be_on_the_record_images_page()
        self.and_the_take_images_step_is_active()

        self.when_i_select_yes_2_cc_and_2_mlo()
        self.and_i_click_continue()
        self.then_i_should_be_on_the_check_information_page()

        self.when_i_click_complete_screening()
        self.then_i_should_be_back_on_the_clinic()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_appointment_show_page()

        self.when_i_click_start_this_appointment()
        self.then_the_accessibility_baseline_is_met()

        self.when_i_click_confirm_identity()
        self.then_the_accessibility_baseline_is_met()

        self.when_i_mark_that_imaging_can_go_ahead()
        self.then_the_accessibility_baseline_is_met()

        self.when_i_select_yes_2_cc_and_2_mlo()
        self.and_i_click_continue()
        self.then_the_accessibility_baseline_is_met()

    def and_there_is_an_appointment(self):
        self.participant = ParticipantFactory(first_name="Janet", last_name="Williams")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(
            screening_episode=self.screening_episode,
            clinic_slot__clinic__setting__provider=self.current_provider,
            clinic_slot__clinic__risk_type=Clinic.RiskType.ROUTINE_RISK,
        )

    def and_i_am_on_the_appointment_show_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:show_appointment",
                kwargs={"pk": self.appointment.pk},
            )
        )

    def then_i_should_see_the_demographic_banner(self):
        expect(self.page.get_by_text("NHS Number")).to_be_visible()

    def when_i_change_to_the_participant_details_tab(self):
        self.page.get_by_role("link", name="Participant details").click()

    def and_i_should_see_the_participant_details(self):
        expect(
            self.page.locator(".nhsuk-summary-list__row", has_text="Full name")
        ).to_contain_text("Janet Williams")

    then_i_should_see_the_participant_details = and_i_should_see_the_participant_details

    def when_i_click_start_this_appointment(
        self,
    ):
        self.page.get_by_text("Start this appointment").click()

    def when_i_submit_the_form(self):
        self.page.get_by_role("button", name="Continue").click()

    def then_i_should_be_on_the_confirm_identity_page(self):
        self.expect_url("mammograms:confirm_identity", pk=self.appointment.pk)
        self.assert_page_title_contains("Confirm identity")

    def and_i_see_the_appointment_status_bar(self):
        status_bar = self.page.locator("div.app-status-bar")
        expect(status_bar).to_contain_text(
            format_nhs_number(self.participant.nhs_number)
        )
        expect(status_bar).to_contain_text(self.participant.full_name)

    def then_i_should_be_on_the_record_medical_information_page(self):
        self.expect_url("mammograms:record_medical_information", pk=self.appointment.pk)
        self.assert_page_title_contains("Record medical information")

    def when_i_click_confirm_identity(self):
        self.page.get_by_role("button").filter(
            has_text="Confirm identity"
        ).first.click()

    def when_i_mark_that_imaging_can_go_ahead(self):
        buttons = self.page.get_by_role("button", name="Complete all and continue")
        assert buttons.count() == 2
        buttons.first.click()

    def then_i_should_be_on_the_record_images_page(self):
        self.expect_url("mammograms:take_images", pk=self.appointment.pk)
        self.assert_page_title_contains("Record images taken")

    def then_i_am_prompted_to_answer_can_the_screening_go_ahead(self):
        self.expect_validation_error(
            error_text="This field is required.",
            fieldset_legend="Can the appointment go ahead?",
            field_label="Yes, go to medical information",
        )

    def then_i_am_prompted_to_answer_has_the_participant_shared_medical_info(self):
        self.expect_validation_error(
            error_text="This field is required.",
            fieldset_legend="Has the participant shared any relevant medical information?",
            field_label="Yes",
        )

    def then_i_am_prompted_to_confirm_whether_imaging_can_go_ahead(self):
        self.expect_validation_error(
            error_text="This field is required.",
            fieldset_legend="Can imaging go ahead?",
            field_label="Yes, mark incomplete sections as ‘none’ or ‘no’",
        )

    def and_the_confirm_identity_step_is_active(self):
        self.assert_active_step("Confirm identity")

        expect(self.clickable_steps()).to_have_count(0)

    def and_the_review_medical_information_step_is_active(self):
        self.assert_active_step("Review medical information")

        clickable_steps = self.clickable_steps()
        expect(clickable_steps).to_have_count(1)
        expect(clickable_steps.locator(".app-workflow-side-nav__label")).to_have_text(
            "Confirm identity"
        )

    def and_the_take_images_step_is_active(self):
        self.assert_active_step("Take images")

        clickable_steps = self.clickable_steps()
        expect(clickable_steps).to_have_count(2)
        expect(
            clickable_steps.nth(0).locator(".app-workflow-side-nav__label")
        ).to_have_text("Confirm identity")
        expect(
            clickable_steps.nth(1).locator(".app-workflow-side-nav__label")
        ).to_have_text("Review medical information")

    def assert_active_step(self, expected_active_step_name):
        nav = self.page.locator("nav.app-workflow-side-nav")
        expect(nav).to_be_visible()
        current_step = nav.locator(
            ".app-workflow-side-nav__item--current .app-workflow-side-nav__label"
        )
        expect(current_step).to_have_count(1)
        expect(current_step).to_have_text(expected_active_step_name)

    def clickable_steps(self):
        return self.page.locator(
            "nav.app-workflow-side-nav .app-workflow-side-nav__step--clickable"
        )

    def when_i_select_yes_2_cc_and_2_mlo(self):
        self.page.get_by_label("Yes, 2 CC and 2 MLO").click()

    def and_i_click_continue(self):
        self.page.get_by_text("Continue").click()

    def then_i_should_be_on_the_check_information_page(self):
        self.expect_url("mammograms:check_information", pk=self.appointment.pk)
        self.assert_page_title_contains("Check information")

    def when_i_click_complete_screening(self):
        self.page.get_by_text("Complete screening and return to clinic").click()

    def then_i_should_be_back_on_the_clinic(self):
        self.expect_url("clinics:show", pk=self.appointment.clinic_slot.clinic.pk)
        self.assert_page_title_contains("Routine risk screening clinic")
