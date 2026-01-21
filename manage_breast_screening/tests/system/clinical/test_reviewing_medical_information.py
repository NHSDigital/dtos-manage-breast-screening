import re

from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.participants.models import AppointmentStatus
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

        for section, anchor, next_section in self._medical_information_sections():
            self.then_section_has_to_review_tag(section)
            self.when_i_mark_section_as_reviewed(section)
            self.then_section_has_reviewed_tag(section)

            self.when_i_click_next_section(section)
            self.then_the_next_section_is_in_focus(next_section, anchor)

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
                "name": AppointmentStatus.IN_PROGRESS,
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
        button = self.page.get_by_role("button", name="Complete all and continue")
        button.click()

    def then_i_am_redirected_to_the_images_page(self):
        self.expect_url("mammograms:awaiting_images", pk=self.appointment.pk)

    def and_all_sections_are_reviewed(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": self.appointment.pk},
            )
        )
        for section_heading, _, _ in self._medical_information_sections():
            self.then_section_has_reviewed_tag(section_heading)

    def _medical_information_sections(self):
        return [
            ("Mammogram history", "symptoms", "Symptoms"),
            ("Symptoms", "medical-history", "Medical history"),
            ("Medical history", "breast-features", "Breast features"),
            ("Breast features", "other-information", "Other information"),
            ("Other information", "other-information", "Other information"),
        ]

    def _medical_information_card(self, heading: str):
        section_heading = self.page.get_by_role("heading", level=2, name=heading)
        return section_heading.locator(
            "xpath=ancestor::div[contains(@class,'app-card-with-status')][1]"
        )
