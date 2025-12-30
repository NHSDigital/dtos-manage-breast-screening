import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.clinics.models import Clinic
from manage_breast_screening.clinics.tests.factories import ClinicFactory
from manage_breast_screening.core.utils.date_formatting import format_date, format_time
from manage_breast_screening.core.utils.string_formatting import (
    format_age,
    format_nhs_number,
)
from manage_breast_screening.participants.models import AppointmentStatus
from manage_breast_screening.participants.tests.factories import AppointmentFactory
from manage_breast_screening.users.tests.factories import UserFactory

from ..system_test_setup import SystemTestCase


class TestUserViewsClinicShowPage(SystemTestCase):
    @pytest.fixture(autouse=True)
    def before(self):
        today = datetime.now(timezone.utc).replace(hour=9, minute=0)
        self.clinic_start_time = today

    def test_user_views_clinic_show_page(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_a_clinic_exists_that_is_run_by_my_provider()
        self.and_there_are_appointments()
        self.and_i_am_on_the_clinic_list()
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

    def test_user_views_clinic_show_page_with_special_appointments(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_a_clinic_exists_that_is_run_by_my_provider()
        self.and_an_appointment_has_extra_needs()
        self.and_i_am_on_the_clinic_list()
        self.when_i_click_on_the_clinic()
        self.then_i_can_see_the_appointment_tagged_as_special()
        self.when_i_click_on_the_special_appointment()
        self.then_i_can_see_the_special_appointment_banner()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_a_clinic_exists_that_is_run_by_my_provider()
        self.and_there_are_appointments()
        self.and_i_am_on_the_clinic_show_page()
        self.then_the_accessibility_baseline_is_met()

    def test_status_attribution_display(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_a_clinic_exists_that_is_run_by_my_provider()
        self.and_i_have_an_appointment_in_progress()
        self.and_there_are_appointments_in_various_statuses_with_attributed_users()
        self.and_i_am_on_the_clinic_show_page()
        self.when_i_click_on_all()
        self.then_i_can_see_status_attribution_for_these_appointments()

    def and_a_clinic_exists_that_is_run_by_my_provider(self):
        user_assignment = self.current_user.assignments.first()
        self.clinic = ClinicFactory(
            starts_at=self.clinic_start_time,
            setting__name="West London BSS",
            setting__provider=user_assignment.provider,
            risk_type=Clinic.RiskType.ROUTINE_RISK,
        )

    def and_there_are_appointments(self):
        tzinfo = ZoneInfo("Europe/London")
        self.confirmed_appointment = AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            starts_at=datetime.now().replace(hour=9, minute=0, tzinfo=tzinfo),
            current_status=AppointmentStatus.CONFIRMED,
            first_name="Janet",
            last_name="Confirmed",
        )
        self.another_confirmed_appointment = AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            starts_at=datetime.now().replace(hour=9, minute=15, tzinfo=tzinfo),
            first_name="Also",
            last_name="Confirmed",
            current_status=AppointmentStatus.CONFIRMED,
        )
        self.checked_in_appointment = AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            starts_at=datetime.now().replace(hour=9, minute=30, tzinfo=tzinfo),
            current_status=AppointmentStatus.CHECKED_IN,
        )
        self.screened_appointment = AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            starts_at=datetime.now().replace(hour=10, minute=45, tzinfo=tzinfo),
            current_status=AppointmentStatus.SCREENED,
        )
        self.in_progress_appointment = AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            starts_at=datetime.now().replace(hour=11, minute=00, tzinfo=tzinfo),
            current_status=AppointmentStatus.STARTED,
        )

    def and_i_am_on_the_clinic_list(self):
        self.page.goto(self.live_server_url + reverse("clinics:index"))
        self.assert_page_title_contains("Today’s clinics")
        heading = self.page.get_by_role("heading", level=1)
        expect(heading).to_contain_text(self.current_provider.name)

    def and_i_am_on_the_clinic_show_page(self):
        self.page.goto(
            self.live_server_url
            + reverse("clinics:show", kwargs={"pk": self.clinic.pk})
        )
        self.assert_page_title_contains("Routine risk screening clinic")

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
        expect(count_span).to_contain_text("4")
        rows = self.page.locator("table.nhsuk-table tbody tr").all()
        self._expect_rows_to_match_appointments(
            rows,
            [
                self.confirmed_appointment,
                self.another_confirmed_appointment,
                self.checked_in_appointment,
                self.in_progress_appointment,
            ],
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
        expect(count_span).to_contain_text("5")
        rows = self.page.locator("table.nhsuk-table tbody tr").all()
        self._expect_rows_to_match_appointments(
            rows,
            [
                self.confirmed_appointment,
                self.another_confirmed_appointment,
                self.checked_in_appointment,
                self.screened_appointment,
                self.in_progress_appointment,
            ],
        )

    def when_i_check_in_an_appointment(self):
        self.page.get_by_role(
            "button", name=re.compile("Check in Janet Confirmed")
        ).click()

    def then_the_appointment_is_checked_in(self):
        row = self.page.locator("tr").filter(has_text="Janet Confirmed")
        expect(row.locator(".nhsuk-tag").filter(has_text="Checked in")).to_be_visible()

    def and_the_appointments_remain_in_the_same_order(self):
        self.when_i_click_on_all()
        rows = self.page.locator("table.nhsuk-table tbody tr").all()
        expected_times = [
            format_time(self.confirmed_appointment.clinic_slot.starts_at),
            format_time(self.another_confirmed_appointment.clinic_slot.starts_at),
            format_time(self.checked_in_appointment.clinic_slot.starts_at),
            format_time(self.screened_appointment.clinic_slot.starts_at),
        ]
        for row, expected_time in zip(rows, expected_times):
            expect(row.locator("td").nth(0)).to_have_text(expected_time)

    def _expect_rows_to_match_appointments(self, rows, appointments):
        assert len(rows) == len(appointments)
        for row, appointment in zip(rows, appointments):
            expected_status_tag = (
                "In progress"
                if appointment.current_status.is_in_progress()
                else appointment.current_status.get_name_display()
            )
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
            expect(row.locator("td").nth(3)).to_contain_text(expected_status_tag)

    def and_an_appointment_has_extra_needs(self):
        self.extra_needs_appointment = AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            clinic_slot__starts_at=datetime.now(timezone.utc).replace(
                hour=11, minute=10
            ),
            current_status=AppointmentStatus.CONFIRMED,
            screening_episode__participant__first_name="Janet",
            screening_episode__participant__last_name="Special Appointment",
            screening_episode__participant__extra_needs={
                "PHYSICAL_RESTRICTION": {"details": "Wheelchair user"}
            },
        )

    def then_i_can_see_the_appointment_tagged_as_special(self):
        row = self.page.locator("tr").filter(has_text="Janet Special Appointment")
        expect(
            row.locator(".nhsuk-tag").filter(has_text="Special appointment")
        ).to_be_visible()

    def when_i_click_on_the_special_appointment(self):
        row = self.page.locator("tr").filter(has_text="Janet Special Appointment")
        row.locator("a", has_text="View appointment").click()

    def then_i_can_see_the_special_appointment_banner(self):
        banner = self.page.locator(".nhsuk-warning-callout")
        expect(banner).to_be_visible()
        expect(banner).to_contain_text("Special appointment")
        expect(banner).to_contain_text("Wheelchair user")

    def and_there_are_appointments_in_various_statuses_with_attributed_users(self):
        # Create users for attribution
        user_screened = UserFactory(first_name="Bob", last_name="User")
        user_cancelled = UserFactory(first_name="Charlie", last_name="User")

        # CONFIRMED status
        self.confirmed_appointment = AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            current_status=AppointmentStatus.CONFIRMED,
            first_name="Participant",
            last_name="Confirmed",
        )

        # SCREENED status
        self.screened_appointment = AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            first_name="Participant",
            last_name="Screened",
        )
        self.screened_appointment.statuses.create(
            name=AppointmentStatus.SCREENED,
            created_by=user_screened,
        )

        # CANCELLED status
        self.cancelled_appointment = AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            first_name="Participant",
            last_name="Cancelled",
        )
        self.cancelled_appointment.statuses.create(
            name=AppointmentStatus.CANCELLED,
            created_by=user_cancelled,
        )

    def then_i_can_see_status_attribution_for_these_appointments(self):
        confirmed_row = self.page.locator("tr").filter(has_text="Participant Confirmed")

        expect(confirmed_row).not_to_contain_text("with")
        expect(confirmed_row).not_to_contain_text("by")

        in_progress_row = self.page.locator("tr").filter(
            has_text="Participant InProgress"
        )

        expect(in_progress_row).to_contain_text(
            f"with {self.current_user.get_short_name()} (you)"
        )

        screened_row = self.page.locator("tr").filter(has_text="Participant Screened")
        expect(screened_row).to_contain_text("by B. User")
        expect(screened_row).not_to_contain_text("(you)")

        cancelled_row = self.page.locator("tr").filter(has_text="Participant Cancelled")
        expect(cancelled_row).to_contain_text("by C. User")
        expect(cancelled_row).not_to_contain_text("(you)")

    def and_i_have_an_appointment_in_progress(self):
        self.in_progress_appointment = AppointmentFactory(
            clinic_slot__clinic=self.clinic,
            first_name="Participant",
            last_name="InProgress",
        )
        self.in_progress_appointment.statuses.create(
            name=AppointmentStatus.STARTED,
            created_by=self.current_user,
        )
