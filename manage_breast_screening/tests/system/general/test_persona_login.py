from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.auth.models import CLINICAL_PERSONA
from manage_breast_screening.auth.tests.factories import UserFactory
from manage_breast_screening.clinics.tests.factories import UserAssignmentFactory

from ..system_test_setup import SystemTestCase


class TestPersonaLogin(SystemTestCase):
    def test_user_views_clinic_show_page(self):
        self.given_a_persona_exists()
        self.when_i_visit_the_clinics_page()
        self.then_i_am_shown_the_persona_login()
        self.when_i_click_on_the_login_button()
        self.then_i_am_on_the_clinics_page()

    def given_a_persona_exists(self):
        user = UserFactory.create(
            nhs_uid=CLINICAL_PERSONA.username,
            first_name="Per",
            last_name="Sona",
        )
        UserAssignmentFactory.create(user=user, clinical=True)

    def when_i_visit_the_clinics_page(self):
        self.page.goto(self.live_server_url + reverse("clinics:index"))

    def then_i_am_shown_the_persona_login(self):
        expect(self.page).to_have_title("Personas – Manage breast screening – NHS")

    def when_i_click_on_the_login_button(self):
        self.page.get_by_role("button", name="Per Sona").click()

    def then_i_am_on_the_clinics_page(self):
        expect(self.page).to_have_title(
            "Today’s clinics – Manage breast screening – NHS"
        )
