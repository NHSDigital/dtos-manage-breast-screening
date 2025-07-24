import re

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.core.system_test_setup import SystemTestCase
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)


class TestEditingSpecialAppointments(SystemTestCase):
    @pytest.fixture(autouse=True)
    def before(self):
        self.participant = ParticipantFactory(first_name="Janet", last_name="Williams")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(screening_episode=self.screening_episode)

    def test_setting_up_a_special_appointment(self):
        self.given_i_am_on_the_appointment_show_page()
        self.when_i_click_on_make_special_appointment()
        self.and_i_add_a_reason()
        self.and_i_select_no_reasons_are_temporary()
        self.and_i_submit_the_form()
        self.then_i_am_back_on_the_appointment()
        self.and_i_see_the_created_special_appointment()

    def test_setting_up_a_special_appointment_with_a_temporary_reason(self):
        self.given_i_am_on_the_appointment_show_page()
        self.when_i_click_on_make_special_appointment()
        self.and_i_add_a_reason()
        self.and_i_select_some_reasons_are_temporary()
        self.and_i_submit_the_form()
        self.then_i_am_back_on_the_appointment()
        self.and_i_see_the_created_special_appointment()

    def test_setting_up_a_special_appointment_with_multiple_reasons(self):
        self.given_i_am_on_the_appointment_show_page()
        self.when_i_click_on_make_special_appointment()
        self.and_i_add_a_reason()
        self.and_i_add_another_reason()
        self.and_i_select_some_reasons_are_temporary()
        self.and_i_submit_the_form()
        self.then_i_select_the_temporary_reason()
        self.and_i_submit_the_form()
        self.then_i_am_back_on_the_appointment()
        self.and_i_see_the_created_special_appointment_with_both_reasons()

    def test_adding_reasons_to_a_special_appointment(self):
        self.given_the_participant_already_has_reasons_set()
        self.and_i_am_on_the_appointment_show_page()
        self.then_i_see_the_special_appointment_banner()

        self.when_i_click_on_the_change_link()
        self.and_i_add_a_reason()
        self.and_i_submit_the_form()
        self.then_i_am_back_on_the_appointment()
        self.and_i_see_the_updated_special_appointment()

    def test_removing_all_reasons_removes_the_banner(self):
        self.given_the_participant_already_has_reasons_set()
        self.and_i_am_on_the_appointment_show_page()
        self.when_i_click_on_the_change_link()
        self.and_i_remove_the_existing_need()
        self.and_i_submit_the_form()
        self.then_i_am_back_on_the_appointment()
        self.and_i_do_not_see_the_special_appointment_banner()

    def test_form_error_when_required_fields_are_missing(self):
        self.given_i_am_on_the_form()
        self.when_i_submit_the_form()
        self.then_i_should_see_an_error_for_the_required_fields()

    def given_the_participant_already_has_reasons_set(self):
        self.participant.extra_needs = {
            "PHYSICAL_RESTRICTION": {
                "details": "Uses wheelchair, needs accessible positioning and additional time for transfers"
            }
        }
        self.participant.save()

    def given_i_am_on_the_appointment_show_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:show_appointment",
                kwargs={"pk": self.appointment.pk},
            )
        )

    def given_i_am_on_the_form(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:provide_special_appointment_details",
                kwargs={"pk": self.appointment.pk},
            )
        )

    and_i_am_on_the_appointment_show_page = given_i_am_on_the_appointment_show_page

    def then_i_see_the_special_appointment_banner(self):
        banner = self.page.locator(".nhsuk-warning-callout")
        expect(banner).to_be_visible()
        expect(banner).to_contain_text("Special appointment")
        expect(banner).to_contain_text(
            "Uses wheelchair, needs accessible positioning and additional time for transfers"
        )

    def and_i_see_the_created_special_appointment(self):
        banner = self.page.locator(".nhsuk-warning-callout")
        expect(banner).to_be_visible()
        expect(banner).to_contain_text("Special appointment")
        expect(banner).to_contain_text("Deaf in one ear")

    def and_i_see_the_created_special_appointment_with_both_reasons(self):
        banner = self.page.locator(".nhsuk-warning-callout")
        expect(banner).to_be_visible()
        expect(banner).to_contain_text("Special appointment")
        expect(banner).to_contain_text("Deaf in one ear")
        expect(banner).to_contain_text("Non-binary")

    def and_i_see_the_updated_special_appointment(self):
        banner = self.page.locator(".nhsuk-warning-callout")
        expect(banner).to_be_visible()
        expect(banner).to_contain_text("Special appointment")
        expect(banner).to_contain_text(
            "Uses wheelchair, needs accessible positioning and additional time for transfers"
        )
        expect(banner).to_contain_text("Deaf in one ear")

    def and_i_do_not_see_the_special_appointment_banner(self):
        banner = self.page.locator(".nhsuk-warning-callout")
        expect(banner).not_to_be_attached()

    def then_i_am_back_on_the_appointment(self):
        expect(self.page).to_have_url(
            re.compile(f"/mammograms/{self.appointment.pk}/start-screening/")
        )

    def when_i_click_on_the_change_link(self):
        banner = self.page.locator(".nhsuk-warning-callout")
        banner.get_by_text("Change").click()

    def and_i_add_a_reason(self):
        self.page.get_by_label("Hearing").click()
        self.page.keyboard.press("Tab")
        self.page.locator("*:focus").fill("Deaf in one ear")

    def and_i_add_another_reason(self):
        self.page.get_by_label("Gender identity").click()
        self.page.keyboard.press("Tab")
        self.page.locator("*:focus").fill("Non-binary")

    def and_i_select_no_reasons_are_temporary(self):
        self.page.get_by_label("No").click()

    def and_i_select_some_reasons_are_temporary(self):
        self.page.get_by_label("Yes").click()

    def and_i_submit_the_form(self):
        self.page.get_by_text("Continue").click()

    when_i_submit_the_form = and_i_submit_the_form

    def and_i_remove_the_existing_need(self):
        self.page.get_by_label("Physical restriction").click()

    def then_i_should_see_an_error_for_the_required_fields(self):
        self.expect_validation_error(
            error_text="Select whether any of the reasons are temporary",
            fieldset_legend="Are any of these reasons temporary?",
            field_label="Yes",
        )

        self.expect_validation_error(
            error_text="Select a reason",
            fieldset_legend="Why does Janet Williams need additional support?",
            field_label="Breast implants",
        )

    def when_i_click_on_make_special_appointment(self):
        self.page.get_by_text("Make special appointment").click()

    def then_i_select_the_temporary_reason(self):
        self.page.get_by_label("Hearing").click()
