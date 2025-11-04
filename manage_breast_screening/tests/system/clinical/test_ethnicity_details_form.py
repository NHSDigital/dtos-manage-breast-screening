import re

from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)

from ..system_test_setup import SystemTestCase


class TestEthnicityDetailsForm(SystemTestCase):
    def test_entering_ethnicity_details_for_a_participant(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_viewing_an_appointment()
        self.when_i_click_on_enter_ethnicity_details()
        self.then_i_am_on_the_ethnicity_details_form()

        self.when_i_submit_the_form()
        self.then_i_see_an_error()

        self.when_i_select_an_ethnicity("Chinese")
        self.and_i_submit_the_form()
        self.then_i_should_be_back_on_the_appointment()
        self.and_the_ethnicity_is_updated_to("Asian or Asian British (Chinese)")

        self.when_i_click_the_change_ethnicity_link()
        self.then_i_am_on_the_ethnicity_details_form()
        self.and_the_saved_ethnicity_is_selected("Chinese")
        self.when_i_select_an_ethnicity("Any other White background")
        self.and_i_submit_the_form()
        self.then_i_should_be_back_on_the_appointment()
        self.and_the_ethnicity_is_updated_to("White (any other White background)")

        self.when_i_click_the_change_ethnicity_link()
        self.and_i_prefer_not_to_say()
        self.and_i_submit_the_form()
        self.then_i_should_be_back_on_the_appointment()
        self.and_the_ethnicity_is_updated_to("Prefer not to say")

    def test_entering_ethnicity_description_provided_by_the_participant(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_viewing_an_appointment()
        self.when_i_click_on_enter_ethnicity_details()
        self.then_i_am_on_the_ethnicity_details_form()

        self.when_i_select_an_ethnicity("Any other White background")
        self.and_i_enter_an_ethnicity_description_provided_by_the_participant(
            "any_other_white_background_details", "White ethnicity description"
        )
        self.and_i_submit_the_form()
        self.then_i_should_be_back_on_the_appointment()
        self.and_the_ethnicity_is_updated_to("White (White ethnicity description)")

        self.when_i_click_the_change_ethnicity_link()
        self.when_i_select_an_ethnicity("Any other Asian background")
        self.and_i_skip_entering_ethnicity_description()
        self.and_i_submit_the_form()
        self.then_i_should_be_back_on_the_appointment()
        self.and_the_ethnicity_is_updated_to(
            "Asian or Asian British (any other Asian background)"
        )

    def and_there_is_an_appointment(self):
        self.participant = ParticipantFactory(ethnic_background_id="")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(
            screening_episode=self.screening_episode,
            clinic_slot__clinic__setting__provider=self.current_provider,
        )

    def and_i_am_viewing_an_appointment(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:participant_details",
                kwargs={"pk": self.appointment.pk},
            )
        )

    def when_i_click_on_enter_ethnicity_details(self):
        self.page.get_by_role("link", name="Enter ethnicity details").click()

    def then_i_am_on_the_ethnicity_details_form(self):
        expect(self.page).to_have_url(
            re.compile(
                reverse(
                    "participants:edit_ethnicity",
                    kwargs={"pk": self.participant.pk},
                )
            )
        )
        self.assert_page_title_contains("Ethnicity")

    def when_i_submit_the_form(self):
        self.page.get_by_role("button", name="Save and continue").click()

    def then_i_see_an_error(self):
        error_summary = self.page.locator(".nhsuk-error-summary")
        expect(error_summary).to_contain_text("Select an ethnic background")
        inline_error = self.page.locator("span.nhsuk-error-message")
        expect(inline_error).to_contain_text("Select an ethnic background")

    def when_i_select_an_ethnicity(self, ethnicity: str):
        self.page.get_by_label(ethnicity).check()

    def and_i_submit_the_form(self):
        self.page.get_by_role("button", name="Save and continue").click()

    def then_i_should_be_back_on_the_appointment(self):
        expect(self.page).to_have_url(
            re.compile(
                reverse(
                    "mammograms:participant_details",
                    kwargs={"pk": self.appointment.pk},
                )
            )
        )

    def and_the_ethnicity_is_updated_to(self, expected_ethnicity):
        ethnicity_row = self.page.locator(".nhsuk-summary-list__row").filter(
            has_text="Ethnicity"
        )
        expect(ethnicity_row).to_contain_text(expected_ethnicity)

    def when_i_click_the_change_ethnicity_link(self):
        self.page.get_by_role("link", name="Change ethnicity").click()

    def and_the_saved_ethnicity_is_selected(self, ethnicity: str):
        expect(self.page.get_by_label(ethnicity)).to_be_checked()

    def and_i_prefer_not_to_say(self):
        self.page.get_by_label("Prefer not to say").check()

    def and_i_enter_an_ethnicity_description_provided_by_the_participant(
        self, field_name: str, description: str
    ):
        self.page.locator(f"input[name='{field_name}']").fill(description)

    def and_i_skip_entering_ethnicity_description(self):
        pass
