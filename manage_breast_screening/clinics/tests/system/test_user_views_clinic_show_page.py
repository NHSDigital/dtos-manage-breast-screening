import re
from datetime import datetime, timezone

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.clinics.tests.factories import ClinicFactory
from manage_breast_screening.core.system_test_setup import SystemTestCase
from manage_breast_screening.core.utils.date_formatting import format_date, format_time
from manage_breast_screening.core.utils.string_formatting import (
    format_age,
    format_nhs_number,
)
from manage_breast_screening.participants.models import AppointmentStatus
from manage_breast_screening.participants.tests.factories import AppointmentFactory


class TestUserViewsClinicShowPage(SystemTestCase):
    @pytest.fixture(autouse=True)
    def before(self):
        today = datetime.now(timezone.utc).replace(hour=9, minute=0)
        self.clinic = ClinicFactory(starts_at=today, setting__name="West London BSS")

    def test_user_views_clinic_show_page(self):
        self.given_there_are_appointments()
        self.given_i_am_on_the_clinic_list()
        self.when_i_click_on_the_clinic()
        self.then_i_should_see_the_clinic_show_page()
        self.and_i_can_see_remaining_appointments()

        self.when_i_click_on_checked_in()
        self.then_i_can_see_checked_in_appointments()
        self.when_i_click_on_complete()
        self.then_i_can_see_completed_appointments()
        self.when_i_click_on_all()
        self.then_i_can_see_all_appointments()

        self.when_i_check_in_an_appointment()
        self.then_the_appointment_is_checked_in()
        self.and_the_appointments_remain_in_the_same_order()

        self.given_an_appointment_has_extra_needs()
        self.and_i_reload_the_clinic_show_page()
        self.then_i_can_see_the_appointment_tagged_as_special()

    def given_there_are_appointments(self):
        self.confirmed_appointment = AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            clinic_slot__starts_at=datetime.now(timezone.utc).replace(hour=9, minute=0),
            current_status=AppointmentStatus.CONFIRMED,
            screening_episode__participant__first_name="Janet",
            screening_episode__participant__last_name="Confirmed",
        )
        self.checked_in_appointment = AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            clinic_slot__starts_at=datetime.now(timezone.utc).replace(
                hour=9, minute=30
            ),
            current_status=AppointmentStatus.CHECKED_IN,
        )
        self.screened_appointment = AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            clinic_slot__starts_at=datetime.now(timezone.utc).replace(
                hour=10, minute=45
            ),
            current_status=AppointmentStatus.SCREENED,
        )

    def given_i_am_on_the_clinic_list(self):
        self.page.goto(self.live_server_url + reverse("clinics:index"))

    def when_i_click_on_the_clinic(self):
        self.page.get_by_role("link", name="West London BSS").click()

    def then_i_should_see_the_clinic_show_page(self):
        expect(self.page).to_have_url(re.compile(f"/clinics/{self.clinic.pk}"))
        heading = self.page.get_by_role("heading", level=1)
        expect(heading).to_contain_text("West London BSS")
        expect(heading).to_contain_text(self.clinic.get_risk_type_display())

    def and_i_can_see_remaining_appointments(self):
        remaining_link = self.page.get_by_role("link", name=re.compile("Remaining"))
        count_span = remaining_link.locator(".app-count")
        expect(count_span).to_contain_text("2")
        rows = self.page.locator("table.nhsuk-table tbody tr").all()
        self._expect_rows_to_match_appointments(
            rows, [self.confirmed_appointment, self.checked_in_appointment]
        )

    def when_i_click_on_checked_in(self):
        self.page.get_by_role("link", name=re.compile("Checked in")).click()

    def then_i_can_see_checked_in_appointments(self):
        checked_in_link = self.page.get_by_role("link", name=re.compile("Checked in"))
        count_span = checked_in_link.locator(".app-count")
        expect(count_span).to_contain_text("1")
        rows = self.page.locator("table.nhsuk-table tbody tr").all()
        self._expect_rows_to_match_appointments(rows, [self.checked_in_appointment])

    def when_i_click_on_complete(self):
        self.page.get_by_role("link", name=re.compile("Complete")).click()

    def then_i_can_see_completed_appointments(self):
        complete_link = self.page.get_by_role("link", name=re.compile("Complete"))
        count_span = complete_link.locator(".app-count")
        expect(count_span).to_contain_text("1")
        rows = self.page.locator("table.nhsuk-table tbody tr").all()
        self._expect_rows_to_match_appointments(rows, [self.screened_appointment])

    def when_i_click_on_all(self):
        self.page.get_by_role("link", name=re.compile("All")).click()

    def then_i_can_see_all_appointments(self):
        all_link = self.page.get_by_role("link", name=re.compile("All"))
        count_span = all_link.locator(".app-count")
        expect(count_span).to_contain_text("3")
        rows = self.page.locator("table.nhsuk-table tbody tr").all()
        self._expect_rows_to_match_appointments(
            rows,
            [
                self.confirmed_appointment,
                self.checked_in_appointment,
                self.screened_appointment,
            ],
        )

    def when_i_check_in_an_appointment(self):
        self.page.get_by_role("button", name=re.compile("Check in")).click()

    def then_the_appointment_is_checked_in(self):
        row = self.page.locator("tr").filter(has_text="Janet Confirmed")
        expect(row.locator(".nhsuk-tag").filter(has_text="Checked in")).to_be_visible()

    def and_the_appointments_remain_in_the_same_order(self):
        self.when_i_click_on_all()
        rows = self.page.locator("table.nhsuk-table tbody tr").all()
        expected_times = [
            format_time(self.confirmed_appointment.clinic_slot.starts_at),
            format_time(self.checked_in_appointment.clinic_slot.starts_at),
            format_time(self.screened_appointment.clinic_slot.starts_at),
        ]
        for row, expected_time in zip(rows, expected_times):
            expect(row.locator("td").nth(0)).to_have_text(expected_time)

    def _expect_rows_to_match_appointments(self, rows, appointments):
        assert len(rows) == len(appointments)
        for row, appointment in zip(rows, appointments):
            expect(row.locator("td").nth(0)).to_have_text(
                format_time(appointment.clinic_slot.starts_at)
            )
            expect(row.locator("td").nth(1).locator("p").nth(0)).to_contain_text(
                appointment.screening_episode.participant.full_name
            )
            expect(row.locator("td").nth(1).locator("p").nth(1)).to_contain_text(
                format_nhs_number(appointment.screening_episode.participant.nhs_number)
            )
            expect(row.locator("td").nth(2)).to_contain_text(
                format_date(appointment.screening_episode.participant.date_of_birth)
            )
            expect(row.locator("td").nth(2)).to_contain_text(
                format_age(appointment.screening_episode.participant.age())
            )
            expect(row.locator("td").nth(3)).to_contain_text(
                appointment.current_status.get_state_display()
            )

    def given_an_appointment_has_extra_needs(self):
        self.extra_needs_appointment = AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            clinic_slot__starts_at=datetime.now(timezone.utc).replace(
                hour=11, minute=10
            ),
            screening_episode__participant__first_name="Janet",
            screening_episode__participant__last_name="Special Appointment",
            screening_episode__participant__extra_needs=["Wheelchair user"],
        )

    def then_i_can_see_the_appointment_tagged_as_special(self):
        row = self.page.locator("tr").filter(has_text="Janet Special Appointment")
        expect(
            row.locator(".nhsuk-tag").filter(has_text="Special appointment")
        ).to_be_visible()

    def and_i_reload_the_clinic_show_page(self):
        self.page.reload()
