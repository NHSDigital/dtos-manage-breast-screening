"""
Scrappy proof of concept of pytest-BDD style (WIP)

- Features in .feature file
- Steps are functions
- Need to double check the handoff of the user session to the Playwright browser: the default page, context fixtures might not work here
- Need some way of remembering objects between steps - check docs for this
- Need to apply the django_db mark
"""

import re

import pytest
from django.test.client import Client
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect
from pytest_bdd import given, scenario, then, when

from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)


@scenario("features/hormone_replacement_therapy.feature", "adding HRT information")
def test_adding_hormone_replacement_therapy():
    pass


@scenario("features/hormone_replacement_therapy.feature", "accessibility check")
def test_accessibility(self):
    pass


# FIXME: temporary workaround to eliminate test classes


@pytest.fixture
def context():
    return {}


def assert_page_title_contains(page, component):
    components = page.title().split(" – ")

    assert components[-1] == "NHS", components
    assert components[-2] == "Manage breast screening", components
    assert components[-3] == component, components


def expect_validation_error(
    page,
    error_text: str,
    field_label: str,
    fieldset_legend: str | None = None,
    field_name: str | None = None,
):
    summary_box = page.locator(".nhsuk-error-summary")
    expect(summary_box).to_contain_text(error_text)
    error_link = summary_box.get_by_text(error_text)
    error_link.click()

    if fieldset_legend:
        fieldset = page.locator("fieldset").filter(has_text=fieldset_legend)
        error_span = fieldset.locator("span").filter(has_text=error_text)
        expect(error_span).to_contain_text(error_text)
        if field_name:
            field = fieldset.get_by_label(field_label, exact=True).and_(
                fieldset.locator(f"[name='{field_name}']")
            )
        else:
            field = fieldset.get_by_label(field_label, exact=True)
    else:
        # No fieldset specified, look for the field directly
        field = page.get_by_label(field_label, exact=True)
        field_container = field.locator("..")
        error_span = field_container.locator(".nhsuk-error-message")
        expect(error_span).to_be_visible()
        expect(error_span).to_contain_text(error_text)

    expect(field).to_be_focused()

    title_components = page.title().split(" – ")
    assert title_components[0].startswith("Error: "), title_components


@given("I am logged in as a clinical user")
def given_i_am_logged_in_as_a_clinical_user(clinical_user, context, live_server):
    client = Client()
    client.force_login(clinical_user)

    session = client.session
    session["login_time"] = timezone.now().isoformat()

    assignment = clinical_user.assignments.first()
    if assignment:
        session["current_provider"] = str(assignment.provider_id)

    session.save()

    # Transfer the session cookie to the playwright browser
    sessionid = client.cookies["sessionid"].value
    context.add_cookies(
        [
            {
                "name": "sessionid",
                "value": sessionid,
                "url": live_server.url,
                "httpOnly": True,
            }
        ]
    )


@given("there is an appointment")
def and_there_is_an_appointment(page, context, current_provider):
    participant = ParticipantFactory(first_name="Angela", last_name="Jones")
    screening_episode = ScreeningEpisodeFactory(participant=participant)
    appointment = AppointmentFactory(
        screening_episode=screening_episode,
        clinic_slot__clinic__setting__provider=current_provider,
    )
    context.update(
        {
            "participant": participant,
            "screening_episode": screening_episode,
            "appointment": appointment,
        }
    )


@given("I am on the record medical information page")
def and_i_am_on_the_record_medical_information_page(page, live_server, context):
    page.goto(
        live_server.url
        + reverse(
            "mammograms:record_medical_information",
            kwargs={"pk": context["appointment"].pk},
        )
    )


@given("I am on the hormone replacement therapy page")
def and_i_am_on_the_add_hormone_replacement_therapy_page(page, live_server, context):
    page.goto(
        live_server.url
        + reverse(
            "mammograms:add_hormone_replacement_therapy",
            kwargs={"pk": context["appointment"].pk},
        )
    )


@when("I click add hormone replacement therapy")
def when_i_click_add_hormone_replacement_therapy(page):
    page.get_by_role(
        "link", name="Enter hormone replacement therapy (HRT) details"
    ).click()


@when("I click change hormone replacement therapy")
def when_i_click_change_hormone_replacement_therapy(page):
    page.get_by_role("link", name="Change hormone replacement therapy").click()


@then("I see the add hormone replacement therapy form")
def then_i_see_the_add_hormone_replacement_therapy_form(page):
    expect(page.get_by_text("Is Angela Jones currently taking HRT?")).to_be_visible()
    assert_page_title_contains(page, "Add hormone replacement therapy")


@then("I see the edit hormone replacement therapy form")
def then_i_see_the_edit_hormone_replacement_therapy_form(page):
    expect(page.get_by_text("Is Angela Jones currently taking HRT?")).to_be_visible()
    page.assert_page_title_contains(page, "Edit hormone replacement therapy")


@when("I select no")
def when_i_select_no(page):
    page.get_by_label("No", exact=True).click()


@when("I select yes")
def when_i_select_yes(page):
    page.get_by_label("Yes", exact=True).click()


@when("I enter a duration")
def and_enter_a_duration(page):
    page.get_by_label("Approximate date started", exact=True).fill("August 2024")


@when("I click continue")
def and_i_click_continue(page):
    page.get_by_text("Continue").click()


@then("I see validation error for missing status")
def then_i_see_validation_error_for_missing_status(page):
    expect_validation_error(
        page,
        error_text="Select whether they are currently taking HRT or not",
        fieldset_legend="Is Angela Jones currently taking HRT?",
        field_label="Yes",
    )


@then("I am back on the medical information page")
def then_i_am_back_on_the_medical_information_page(page, live_server, context):
    path = reverse(
        "mammograms:record_medical_information",
        kwargs={"pk": context["appointment"].pk},
    )
    url = re.compile(f"^{live_server.url}{re.escape(path)}$")
    expect(page).to_have_url(url)


@then("the message says hormone replacement therapy added")
def and_the_message_says_hormone_replacement_therapy_added(page):
    alert = page.get_by_role("alert")

    expect(alert).to_contain_text("Success")
    expect(alert).to_contain_text("Added hormone replacement therapy")


@then("the message says hormone replacement therapy updated")
def and_the_message_says_hormone_replacement_therapy_updated(page):
    alert = page.get_by_role("alert")

    expect(alert).to_contain_text("Success")
    expect(alert).to_contain_text("Updated hormone replacement therapy")


@then("the hormone replacement therapy is displayed as not taken")
def and_the_hormone_replacement_therapy_is_displayed_as_not_taken(page):
    page.and_the_hormone_replacement_therapy_is_displayed("Not taking HRT")


@then("the hormone replacement therapy is displayed")
def and_the_hormone_replacement_therapy_is_displayed(page, expected_text):
    heading = page.get_by_role("heading").filter(has_text="Other information")
    section = page.locator(".nhsuk-card").filter(has=heading)
    expect(section).to_be_visible()

    row = section.locator(
        ".nhsuk-summary-list__row", has_text="Hormone replacement therapy (HRT)"
    )
    value = row.locator(".nhsuk-summary-list__value")
    expect(value).to_have_text(expected_text)
