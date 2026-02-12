from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)

from ..system_test_setup import SystemTestCase


class TestAddPregnancyAndBreastfeeding(SystemTestCase):
    def test_adding_pregnancy_and_breastfeeding(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_record_medical_information_page()

        self.when_i_click_add_pregnancy_and_breastfeeding()
        self.then_i_see_the_pregnancy_and_breastfeeding_form()

        self.when_i_click_save()
        self.then_i_see_validation_error_for_missing_statuses()

        self.when_i_select_no_for_pregnancy_and_breastfeeding()
        self.and_i_click_save()

        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_message_says_pregnancy_and_breastfeeding_added()
        self.and_the_pregnancy_and_breastfeeding_is_displayed_as_not_pregnant()

        self.when_i_click_change_pregnancy_and_breastfeeding()
        self.then_i_see_the_pregnancy_and_breastfeeding_form()

        self.when_i_select_yes_for_pregnancy()
        self.and_enter_a_due_date()
        self.and_i_click_save()

        self.then_i_am_back_on_the_medical_information_page()
        self.and_the_message_says_pregnancy_and_breastfeeding_updated()
        self.and_the_pregnancy_and_breastfeeding_is_displayed_as_pregnant()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        self.and_i_am_on_the_add_pregnancy_and_breastfeeding_page()
        self.then_the_accessibility_baseline_is_met()

    def and_there_is_an_appointment(self):
        self.participant = ParticipantFactory(first_name="Angela", last_name="Jones")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(
            screening_episode=self.screening_episode,
            clinic_slot__clinic__setting__provider=self.current_provider,
        )

    def and_i_am_on_the_record_medical_information_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": self.appointment.pk},
            )
        )

    def and_i_am_on_the_add_pregnancy_and_breastfeeding_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:add_pregnancy_and_breastfeeding",
                kwargs={"pk": self.appointment.pk},
            )
        )

    def when_i_click_add_pregnancy_and_breastfeeding(self):
        self.page.get_by_role(
            "link", name="Enter pregnancy and breastfeeding details"
        ).click()

    def when_i_click_change_pregnancy_and_breastfeeding(self):
        self.page.get_by_role("link", name="Change pregnancy and breastfeeding").click()

    def then_i_see_the_pregnancy_and_breastfeeding_form(self):
        expect(self.page.get_by_text("Pregnancy and breastfeeding")).to_be_visible()
        self.assert_page_title_contains("Pregnancy and breastfeeding")

    def when_i_select_no_for_pregnancy_and_breastfeeding(self):
        fieldset = self.page.get_by_role("group", name="Is Angela Jones pregnant?")
        fieldset.get_by_label("No", exact=True).click()
        fieldset = self.page.get_by_role(
            "group", name="Are they currently breastfeeding?"
        )
        fieldset.get_by_label("No", exact=True).click()

    def when_i_select_yes_for_pregnancy(self):
        fieldset = self.page.get_by_role("group", name="Is Angela Jones pregnant?")
        fieldset.get_by_label("Yes", exact=True).click()

    def and_enter_a_due_date(self):
        self.page.get_by_label("Approximate due date", exact=True).fill(
            "due in November"
        )

    def and_i_click_save(self):
        self.page.get_by_text("Save").click()

    when_i_click_save = and_i_click_save

    def then_i_see_validation_error_for_missing_statuses(self):
        self.expect_validation_error(
            error_text="Select whether they are currently pregnant or not",
            fieldset_legend="Is Angela Jones pregnant?",
            field_label="Yes",
        )
        self.expect_validation_error(
            error_text="Select whether they are currently breastfeeding or not",
            fieldset_legend="Are they currently breastfeeding?",
            field_label="Yes",
        )

    def then_i_am_back_on_the_medical_information_page(self):
        self.expect_url("mammograms:record_medical_information", pk=self.appointment.pk)

    def and_the_message_says_pregnancy_and_breastfeeding_added(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Added pregnancy and breastfeeding")

    def and_the_message_says_pregnancy_and_breastfeeding_updated(self):
        alert = self.page.get_by_role("alert")

        expect(alert).to_contain_text("Success")
        expect(alert).to_contain_text("Updated pregnancy and breastfeeding")

    def and_the_pregnancy_and_breastfeeding_is_displayed_as_not_pregnant(self):
        self.and_the_pregnancy_and_breastfeeding_is_displayed(
            """
            Not pregnant
            Not breastfeeding
            """
        )

    def and_the_pregnancy_and_breastfeeding_is_displayed_as_pregnant(self):
        self.and_the_pregnancy_and_breastfeeding_is_displayed(
            """
            Currently pregnant
            Timeframe: due in November
            Not breastfeeding
            """
        )

    def and_the_pregnancy_and_breastfeeding_is_displayed(self, expected_text):
        heading = self.page.get_by_role("heading").filter(has_text="Other information")
        section = self.page.locator(".nhsuk-card").filter(has=heading)
        expect(section).to_be_visible()

        row = section.locator(
            ".nhsuk-summary-list__row", has_text="Pregnancy and breastfeeding"
        )
        value = row.locator(".nhsuk-summary-list__value")
        expect(value).to_have_text(expected_text)
