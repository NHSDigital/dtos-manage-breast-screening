import pytest
from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.participants.models.symptom import SymptomType
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)

from ..system_test_setup import SystemTestCase


class TestRecordingSymptoms(SystemTestCase):
    @pytest.fixture(autouse=True)
    def setup_symptom_types(self):
        SymptomType.objects.get_or_create(id=SymptomType.LUMP, name="Lump")
        SymptomType.objects.get_or_create(
            id=SymptomType.SWELLING_OR_SHAPE_CHANGE, name="Swelling or shape change"
        )

    def test_adding_a_symptom(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()
        self.when_i_click_on_add_a_lump()
        self.then_i_see_the_add_a_lump_form()

        self.when_i_select_right_breast()
        self.and_i_select_less_than_three_months()
        self.and_i_select_no_the_symptom_has_not_been_investigated()
        self.and_i_click_save_symptom()
        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_lump_on_the_right_breast_is_listed()

    def and_there_is_an_appointment(self):
        self.participant = ParticipantFactory(first_name="Janet", last_name="Williams")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(screening_episode=self.screening_episode)
        self.provider = self.appointment.provider

    def and_i_am_on_the_record_medical_information_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": self.appointment.pk},
            )
        )

    def when_i_click_on_add_a_lump(self):
        self.page.get_by_text("Add a lump").click()

    def then_i_see_the_add_a_lump_form(self):
        expect(self.page.get_by_text("Details of the lump")).to_be_visible()

    def when_i_select_right_breast(self):
        self.page.get_by_label("Right breast").click()

    def and_i_select_less_than_three_months(self):
        self.page.get_by_label("Less than 3 months").click()

    def and_i_select_no_the_symptom_has_not_been_investigated(self):
        legend = self.page.get_by_text("Has this been investigated?")
        fieldset = self.page.get_by_role("group").filter(has=legend)
        fieldset.get_by_label("No").click()

    def and_i_click_save_symptom(self):
        self.page.get_by_text("Save symptom").click()

    def then_i_am_back_on_the_medical_information_page(self):
        self.expect_url("mammograms:record_medical_information", pk=self.appointment.pk)

    def and_the_lump_on_the_right_breast_is_listed(self):
        key = self.page.locator(
            ".nhsuk-summary-list__key", has=self.page.get_by_text("Lump", exact=True)
        )
        row = self.page.locator(".nhsuk-summary-list__row").filter(has=key)
        expect(row).to_contain_text("Right breast")
