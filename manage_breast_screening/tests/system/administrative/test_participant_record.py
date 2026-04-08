import re
from datetime import datetime
from datetime import timezone as tz

import pytest
from django.urls import reverse
from playwright.sync_api import expect
from pytest_bdd import given, scenario, then, when

from manage_breast_screening.clinics.tests.factories import ClinicSlotFactory
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)


@pytest.mark.system
@pytest.mark.usefixtures("known_datetime", "live_server")
@scenario("features/participant_record.feature", "Viewing the participant record")
def test_viewing_participant_record_from_an_appointment():
    pass


@pytest.mark.system
@pytest.mark.usefixtures("live_server")
@scenario("features/participant_record.feature", "Accessibility check")
def test_accessibility():
    pass


@pytest.fixture
def participant():
    return ParticipantFactory(first_name="Janet", last_name="Williams")


@given(
    "the participant has an upcoming appointment", target_fixture="upcoming_appointment"
)
def and_the_participant_has_an_upcoming_appointment(participant, current_provider):
    clinic_slot = ClinicSlotFactory(
        starts_at=datetime(2025, 1, 2, 11, tzinfo=tz.utc),
        clinic__setting__provider=current_provider,
    )
    screening_episode = ScreeningEpisodeFactory(participant=participant)
    return AppointmentFactory(
        clinic_slot=clinic_slot,
        screening_episode=screening_episode,
    )


@given("the participant has past appointments", target_fixture="past_appointments")
def and_the_participant_has_past_appointments(participant, current_provider):
    clinic_slot_2022 = ClinicSlotFactory(
        starts_at=datetime(2022, 1, 2, 11, tzinfo=tz.utc),
        clinic__setting__provider=current_provider,
    )
    clinic_slot_2019 = ClinicSlotFactory(
        starts_at=datetime(2019, 1, 2, 11, tzinfo=tz.utc),
        clinic__setting__provider=current_provider,
    )
    return [
        AppointmentFactory(
            clinic_slot=clinic_slot_2022,
            screening_episode=ScreeningEpisodeFactory(participant=participant),
        ),
        AppointmentFactory(
            clinic_slot=clinic_slot_2019,
            screening_episode=ScreeningEpisodeFactory(participant=participant),
        ),
    ]


@given("I am viewing the upcoming appointment")
def and_i_am_viewing_the_upcoming_appointment(page, live_server, upcoming_appointment):
    page.goto(
        live_server.url
        + reverse(
            "mammograms:show_appointment",
            kwargs={"pk": upcoming_appointment.pk},
        )
    )


@when("I click on participant details")
def when_i_click_on_participant_details(page):
    page.get_by_role("link", name="Participant", exact=True).click()


@then("I should be on the participant record page")
def then_i_should_be_on_the_participant_record_page(upcoming_appointment, page):
    path = reverse(
        "mammograms:participant_details",
        kwargs={"pk": upcoming_appointment.pk},
    )
    expect(page).to_have_url(re.compile(path))


@then("I should see the participant record")
def and_i_should_see_the_participant_record(page):
    main = page.get_by_role("main")
    expect(main).to_contain_text("Janet Williams")
    expect(main).to_contain_text("Participant details")


@when("I click on the back link")
def when_i_click_on_the_back_link(page):
    page.get_by_role("link", name="Appointment", exact=True).click()


@then("I should be back on the appointment")
def then_i_should_be_back_on_the_appointment(upcoming_appointment, page):
    path = reverse(
        "mammograms:show_appointment",
        kwargs={"pk": upcoming_appointment.pk},
    )
    expect(page).to_have_url(re.compile(path))


@then("I should see the upcoming appointment")
def then_i_should_see_the_upcoming_appointment(upcoming_appointment, page):
    upcoming = page.get_by_test_id("upcoming-appointments-table")
    expect(upcoming).to_be_visible()
    appointment = upcoming.get_by_test_id("appointment-row")
    expect(appointment).to_be_visible()
    expect(appointment).to_contain_text("2 January 2025")


@then("I should see the past appointments")
def then_i_should_see_the_past_appointments(page):
    past = page.get_by_test_id("past-appointments-table")
    expect(past).to_be_visible()
    appointments = past.get_by_test_id("appointment-row").all()
    assert len(appointments) == 2

    expect(appointments[0]).to_contain_text("2 January 2022")
    expect(appointments[1]).to_contain_text("2 January 2019")


@when("I click on the upcoming appointment")
def when_i_click_on_the_upcoming_appointment(page):
    past = page.get_by_test_id("upcoming-appointments-table")
    past.get_by_text("View details").click()


@when("I click on a past appointment")
def when_i_click_on_a_past_appointment(page):
    past = page.get_by_test_id("past-appointments-table")
    past.get_by_text("View details").first.click()


@then("I should be on the past appointment page")
def then_i_should_be_on_the_past_appointment_page(past_appointments, page):
    path = reverse(
        "mammograms:show_appointment",
        kwargs={"pk": past_appointments[0].pk},
    )
    expect(page).to_have_url(re.compile(path))


@then("I should be on the upcoming appointment page")
def then_i_should_be_on_the_upcoming_appointment_page(upcoming_appointment, page):
    path = reverse(
        "mammograms:show_appointment",
        kwargs={"pk": upcoming_appointment.pk},
    )
    expect(page).to_have_url(re.compile(path))
