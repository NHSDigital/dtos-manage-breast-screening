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


class TestReviewingMedicalInformation(SystemTestCase):
    def test_reviewing_each_medical_information_section(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()

        self.then_section_has_to_review_tag("Mammogram history")
        self.when_i_mark_section_as_reviewed("Mammogram history")
        self.then_section_has_reviewed_tag("Mammogram history")
        self.when_i_click_next_section("Mammogram history")
        self.then_the_next_section_is_in_focus("Symptoms", anchor="symptoms")

        self.then_section_has_to_review_tag("Symptoms")
        self.when_i_mark_section_as_reviewed("Symptoms")
        self.then_section_has_reviewed_tag("Symptoms")
        self.when_i_click_next_section("Symptoms")
        self.then_the_next_section_is_in_focus(
            "Medical history", anchor="medical-history"
        )

        self.then_section_has_to_review_tag("Medical history")
        self.when_i_mark_section_as_reviewed("Medical history")
        self.then_section_has_reviewed_tag("Medical history")
        self.when_i_click_next_section("Medical history")
        self.then_the_next_section_is_in_focus(
            "Breast features", anchor="breast-features"
        )

        self.then_section_has_to_review_tag("Breast features")
        self.when_i_mark_section_as_reviewed("Breast features")
        self.then_section_has_reviewed_tag("Breast features")
        self.when_i_click_next_section("Breast features")
        self.then_the_next_section_is_in_focus(
            "Other information", anchor="other-information"
        )

        self.then_section_has_to_review_tag("Other information")
        self.when_i_mark_section_as_reviewed("Other information")
        self.then_section_has_reviewed_tag("Other information")
        self.and_there_is_no_next_section_link("Other information")

    def test_complete_all_and_continue(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()

        self.when_i_click_complete_all_and_continue()
        self.then_i_am_redirected_to_the_images_page()
        self.and_all_sections_are_reviewed()

    def and_there_is_an_appointment(self):
        self.participant = ParticipantFactory()
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

    def then_section_has_to_review_tag(self, section_heading: str):
        card = self._medical_information_card(section_heading)
        expect(card.locator(".app-card-with-status__tag")).to_contain_text("To review")

    def when_i_mark_section_as_reviewed(self, section_heading: str):
        card = self._medical_information_card(section_heading)
        card.get_by_role("button", name="Mark as reviewed").click()

    def then_section_has_reviewed_tag(self, section_heading: str):
        card = self._medical_information_card(section_heading)
        expect(card.locator(".app-card-with-status__tag")).to_contain_text("Reviewed")

    def when_i_click_next_section(self, section_heading: str):
        card = self._medical_information_card(section_heading)
        next_section_control = card.get_by_role("link", name="Next section")
        next_section_control.click()

    def and_there_is_no_next_section_link(self, section_heading: str):
        card = self._medical_information_card(section_heading)
        next_section_control = card.get_by_role("link", name="Next section")
        expect(next_section_control).not_to_be_attached()

    def then_the_next_section_is_in_focus(self, section_heading: str, anchor: str):
        path = reverse(
            "mammograms:record_medical_information", kwargs={"pk": self.appointment.pk}
        )
        expect(self.page).to_have_url(
            re.compile(f"^{self.live_server_url}{re.escape(path)}#{re.escape(anchor)}$")
        )

        heading = self.page.get_by_role("heading", level=2, name=section_heading)
        expect(heading).to_be_in_viewport()

    def when_i_click_complete_all_and_continue(self):
        buttons = self.page.get_by_role("button", name="Complete all and continue")
        assert buttons.count() == 2
        buttons.first.click()

    def then_i_am_redirected_to_the_images_page(self):
        self.expect_url("mammograms:take_images", pk=self.appointment.pk)

    def and_all_sections_are_reviewed(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": self.appointment.pk},
            )
        )
        for section_heading in self._medical_information_sections():
            self.then_section_has_reviewed_tag(section_heading)

    def _medical_information_sections(self):
        return [
            "Mammogram history",
            "Symptoms",
            "Medical history",
            "Breast features",
            "Other information",
        ]

    def _medical_information_card(self, heading: str):
        section_heading = self.page.get_by_role("heading", level=2, name=heading)
        return section_heading.locator(
            "xpath=ancestor::div[contains(@class,'app-card-with-status')][1]"
        )
