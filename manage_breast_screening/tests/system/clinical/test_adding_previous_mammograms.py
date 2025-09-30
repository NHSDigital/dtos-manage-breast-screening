import re

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)

from ..system_test_setup import SystemTestCase


class TestAddingPreviousMammograms(SystemTestCase):
    @pytest.fixture(autouse=True)
    def before(self):
        self.participant = ParticipantFactory(first_name="Janet", last_name="Williams")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(screening_episode=self.screening_episode)
        self.provider = self.appointment.provider

    def test_adding_a_mammogram_at_the_same_provider(self):
        """
        If a mammogram was taken at the same provider, but there is an error in the system, the participant can report that it was taken.
        """
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_i_am_on_the_appointment_show_page()
        self.then_i_should_see_no_reported_mammograms()

        self.when_i_click_on_add_mammogram()
        self.then_i_should_be_on_the_add_previous_mammogram_form()

        self.when_i_select_the_same_provider()
        self.and_i_enter_an_exact_date()
        self.and_i_select_yes_same_name()
        self.and_i_enter_additional_information()
        self.and_i_click_continue()
        self.then_i_should_be_back_on_the_appointment()
        self.and_i_should_see_the_mammogram_with_the_same_provider()

    def test_adding_a_mammogram_taken_elsewhere_with_a_different_name(self):
        """
        If a mammogram was taken at another BSU, or elsewhere in the UK, the participant can report that it was taken
        If the mammogram was taken under a different name, the mammographer can record that name.
        """
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_i_am_on_the_appointment_show_page()
        self.then_i_should_see_no_reported_mammograms()

        self.when_i_click_on_add_mammogram()
        self.then_i_should_be_on_the_add_previous_mammogram_form()

        self.when_i_enter_another_location_in_the_uk()
        self.and_i_enter_an_approximate_date()
        self.and_i_enter_a_different_name()
        self.and_i_enter_additional_information()
        self.and_i_click_continue()
        self.then_i_should_be_back_on_the_appointment()
        self.and_i_should_see_the_mammogram_with_the_other_provider_and_name()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_i_am_on_the_add_previous_mammograms_page()
        self.then_the_accessibility_baseline_is_met()

    def and_i_am_on_the_appointment_show_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:show_appointment",
                kwargs={"pk": self.appointment.pk},
            )
        )

    def and_i_am_on_the_add_previous_mammograms_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "participants:add_previous_mammogram",
                kwargs={"pk": self.participant.pk},
            )
        )

    def then_i_should_see_no_reported_mammograms(self):
        expect(self.page.get_by_test_id("mammograms")).to_contain_text("Not known")

    def when_i_click_on_add_mammogram(self):
        self.page.get_by_text("Add mammogram").click()

    def then_i_should_be_on_the_add_previous_mammogram_form(self):
        path = reverse(
            "participants:add_previous_mammogram",
            kwargs={"pk": self.participant.pk},
        )
        expect(self.page).to_have_url(re.compile(path))
        self.assert_page_title_contains("Add details of a previous mammogram")

    def then_i_should_be_back_on_the_appointment(self):
        path = reverse(
            "mammograms:show_appointment",
            kwargs={"pk": self.appointment.pk},
        )
        expect(self.page).to_have_url(re.compile(path))

    def when_i_select_the_same_provider(self):
        option = f"At {self.provider.name}"
        self.page.get_by_label(option).click()

    def and_i_enter_an_exact_date(self):
        self.page.get_by_label("Enter an exact date").click()
        self.page.get_by_label("Day").fill("1")
        self.page.get_by_label("Month").fill("12")
        self.page.get_by_label("Year").fill("2023")

    def and_i_select_yes_same_name(self):
        self.page.get_by_label("Yes").click()

    def and_i_enter_additional_information(self):
        self.page.get_by_label("Additional information (optional)").fill("RR")

    def and_i_click_continue(self):
        self.page.get_by_text("Continue").click()

    def and_i_should_see_the_mammogram_with_the_same_provider(self):
        expected_inner_text = re.compile(
            rf"Added today\n1 December 2023 \(.* ago\)\n{self.provider.name}\nAdditional information: RR"
        )
        expect(self.page.get_by_test_id("mammograms")).to_contain_text(
            expected_inner_text,
            use_inner_text=True,
        )

    def when_i_enter_another_location_in_the_uk(self):
        self.page.get_by_label("Somewhere in the UK").click()
        self.page.get_by_label("Location").first.fill("other place")

    def and_i_enter_an_approximate_date(self):
        self.page.get_by_label("Enter an approximate date").and_(
            self.page.get_by_role("radio")
        ).click()
        self.page.get_by_label("Enter an approximate date").and_(
            self.page.get_by_role("textbox")
        ).fill("a year ago")

    def and_i_enter_a_different_name(self):
        self.page.get_by_label("No, under a different name").click()
        self.page.get_by_label("Enter the previously used name").fill("Taylor Swift")

    def and_i_should_see_the_mammogram_with_the_other_provider_and_name(self):
        expected_inner_text = re.compile(
            r"Added today\nApproximate date: a year ago\nIn the UK: other place\nPrevious name: Taylor Swift\nAdditional information: RR"
        )
        expect(self.page.get_by_test_id("mammograms")).to_contain_text(
            expected_inner_text,
            use_inner_text=True,
        )
