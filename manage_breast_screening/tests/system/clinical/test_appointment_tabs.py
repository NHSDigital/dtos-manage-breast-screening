from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.auth.models import Role
from manage_breast_screening.clinics.tests.factories import UserAssignmentFactory
from manage_breast_screening.manual_images.services import StudyService
from manage_breast_screening.participants.models.appointment import (
    AppointmentStatusNames,
)
from manage_breast_screening.participants.models.symptom import SymptomType
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    BreastCancerHistoryItemFactory,
    ParticipantFactory,
    ParticipantReportedMammogramFactory,
    ScreeningEpisodeFactory,
    SymptomFactory,
)
from manage_breast_screening.users.tests.factories import UserFactory

from ..system_test_setup import SystemTestCase


class TestAppointmentTabs(SystemTestCase):
    def test_appointment_tabs_when_in_progress_with_someone_else(self):
        """
        When a appointment is in progress with another user,
        should see message about appointment being in progress with another user
        """
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_in_progress_with_someone_else()
        self.and_the_appointment_has_medical_history()
        self.and_i_am_on_the_appointment_show_page()
        self.then_i_should_see_the_demographic_banner()
        self.and_the_message_says_in_progress_with_someone_else()

        self.when_i_change_to_the_participant_details_tab()
        self.then_i_should_see_the_participant_details()
        self.and_the_message_says_in_progress_with_someone_else()

        self.when_i_change_to_the_note_details_tab()
        self.then_i_should_see_the_notes_details()
        self.and_the_message_says_in_progress_with_someone_else()

        self.when_i_change_to_the_medical_information_tab()
        self.then_i_should_see_the_mammogram_history_section()
        self.and_i_should_see_the_symptoms_section()
        self.and_i_should_see_the_medical_history_section()
        self.and_i_should_see_the_breast_features_placeholder()
        self.and_i_should_see_the_other_information_section()
        self.and_the_message_says_in_progress_with_someone_else()

        self.when_i_change_to_the_appointment_details_tab()
        self.then_i_should_see_the_appointment_details()
        self.and_the_message_says_in_progress_with_someone_else()

    def test_appointment_tabs_when_in_progress_with_current_user(self):
        """
        When a appointment is in progress with the current user,
        should not see message about appointment being in progress with another user
        """
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_in_progress_with_current_user()
        self.and_i_am_on_the_appointment_show_page()
        self.then_i_should_see_the_demographic_banner()
        self.and_no_message_says_in_progress_with_someone_else()

        self.when_i_change_to_the_participant_details_tab()
        self.then_i_should_see_the_participant_details()
        self.and_no_message_says_in_progress_with_someone_else()

    def test_appointment_tabs_when_not_in_progress(self):
        """
        When a appointment is not in progress,
        should not see message about appointment being in progress with another user
        """
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_not_in_progress()
        self.and_i_am_on_the_appointment_show_page()
        self.then_i_should_see_the_demographic_banner()
        self.and_no_message_says_in_progress_with_someone_else()

        self.when_i_change_to_the_participant_details_tab()
        self.then_i_should_see_the_participant_details()
        self.and_no_message_says_in_progress_with_someone_else()

    def test_the_images_tab_of_a_completed_appointment(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_a_completed_appointment()
        self.and_i_am_on_the_appointment_show_page()
        self.when_i_change_to_the_images_tab()
        self.then_i_should_see_the_image_counts()
        self.and_no_message_says_in_progress_with_someone_else()

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_a_completed_appointment()
        self.and_i_am_on_the_appointment_show_page()
        self.then_the_accessibility_baseline_is_met()

        self.when_i_change_to_the_participant_details_tab()
        self.then_the_accessibility_baseline_is_met()

        self.when_i_change_to_the_images_tab()
        self.then_i_should_see_the_image_counts()

        self.when_i_change_to_the_note_details_tab()
        self.then_the_accessibility_baseline_is_met()

        self.when_i_change_to_the_appointment_details_tab()
        self.then_the_accessibility_baseline_is_met()

    def and_there_is_an_appointment_in_progress_with_current_user(self):
        self.participant = ParticipantFactory(first_name="Janet", last_name="Williams")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(
            screening_episode=self.screening_episode,
            clinic_slot__clinic__setting__provider=self.current_provider,
            current_status_params={
                "name": AppointmentStatusNames.IN_PROGRESS,
                "created_by": self.current_user,
            },
        )

    def and_there_is_an_appointment_not_in_progress(self):
        another_user = UserFactory.create(first_name="Firstname", last_name="Lastname")
        UserAssignmentFactory.create(user=another_user, roles=[Role.CLINICAL.value])

        self.participant = ParticipantFactory(first_name="Janet", last_name="Williams")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(
            screening_episode=self.screening_episode,
            clinic_slot__clinic__setting__provider=self.current_provider,
            current_status_params={
                "name": AppointmentStatusNames.SCHEDULED,
                "created_by": another_user,
            },
        )

    def and_there_is_a_completed_appointment(self):
        self.participant = ParticipantFactory(first_name="Janet", last_name="Williams")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(
            screening_episode=self.screening_episode,
            clinic_slot__clinic__setting__provider=self.current_provider,
            current_status_params={
                "name": AppointmentStatusNames.SCREENED,
                "created_by": self.current_user,
            },
        )
        self.study = StudyService(
            self.appointment, self.current_user
        ).create_with_default_series()

    def and_there_is_an_appointment_in_progress_with_someone_else(self):
        another_user = UserFactory.create(first_name="Firstname", last_name="Lastname")
        UserAssignmentFactory.create(user=another_user, roles=[Role.CLINICAL.value])

        self.participant = ParticipantFactory(first_name="Janet", last_name="Williams")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(
            screening_episode=self.screening_episode,
            clinic_slot__clinic__setting__provider=self.current_provider,
            current_status_params={
                "name": AppointmentStatusNames.IN_PROGRESS,
                "created_by": another_user,
            },
        )

    def and_i_am_on_the_appointment_show_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:show_appointment",
                kwargs={"pk": self.appointment.pk},
            )
        )

    def then_i_should_see_the_demographic_banner(self):
        expect(self.page.get_by_text("NHS Number")).to_be_visible()

    def and_the_message_says_in_progress_with_someone_else(self):
        alert = self.page.get_by_role("region")
        expect(alert).to_contain_text("Important")
        expect(alert).to_contain_text(
            "This appointment is currently being run by F. Lastname."
        )

    def and_no_message_says_in_progress_with_someone_else(self):
        expect(self.page.get_by_role("region")).not_to_be_attached()

    def when_i_change_to_the_participant_details_tab(self):
        self.when_i_change_to_an_appointment_tab("Participant")

    def then_i_should_see_the_participant_details(self):
        expect(
            self.page.locator(".nhsuk-summary-list__row", has_text="Full name")
        ).to_contain_text("Janet Williams")

    def when_i_change_to_the_note_details_tab(self):
        self.when_i_change_to_an_appointment_tab("Note")

    def then_i_should_see_the_notes_details(self):
        expect(self.page.get_by_text("Save note")).to_be_attached()

    def when_i_change_to_the_appointment_details_tab(self):
        self.when_i_change_to_an_appointment_tab("Appointment")

    def when_i_change_to_the_images_tab(self):
        self.when_i_change_to_an_appointment_tab("Images")

    def then_i_should_see_the_appointment_details(self):
        expect(self.page.get_by_text("Scheduled date and time")).to_be_attached()

    def then_i_should_see_the_image_counts(self):
        expect(self.page.get_by_text("1× RCC")).to_be_attached()
        expect(self.page.get_by_text("1× LCC")).to_be_attached()
        expect(self.page.get_by_text("1× RMLO")).to_be_attached()
        expect(self.page.get_by_text("1× LCC")).to_be_attached()

    def and_the_appointment_has_medical_history(self):
        SymptomType.objects.get_or_create(id=SymptomType.LUMP, name="Lump")
        ParticipantReportedMammogramFactory(appointment=self.appointment)
        SymptomFactory(lump=True, appointment=self.appointment)
        BreastCancerHistoryItemFactory(
            appointment=self.appointment,
            diagnosis_location="RIGHT_BREAST",
        )

    def when_i_change_to_the_medical_information_tab(self):
        self.when_i_change_to_an_appointment_tab("Medical information")

    def then_i_should_see_the_mammogram_history_section(self):
        card = self.page.locator(".nhsuk-card", has_text="Mammogram history")
        expect(card).to_be_visible()
        expect(card).to_contain_text(
            "The last confirmed mammogram and any added manually since then"
        )
        expect(card).to_contain_text("Last known mammograms")
        expect(card).to_contain_text("Added today")
        expect(card).to_contain_text("Date unknown")

    def and_i_should_see_the_symptoms_section(self):
        card = self.page.locator(".nhsuk-card", has_text="Symptoms")
        expect(card).to_be_visible()
        expect(card).to_contain_text("Lump")

    def and_i_should_see_the_medical_history_section(self):
        card = self.page.locator(".nhsuk-card", has_text="Medical history")
        expect(card).to_be_visible()
        expect(card).to_contain_text("Breast cancer")
        expect(card).to_contain_text("Cancer location")
        expect(card).to_contain_text("Right breast")

    def and_i_should_see_the_breast_features_placeholder(self):
        card = self.page.locator(".nhsuk-card", has_text="Breast features")
        expect(card).to_be_visible()
        expect(card).to_contain_text(
            "No breast features have been recorded for this participant."
        )

    def and_i_should_see_the_other_information_section(self):
        card = self.page.locator(".nhsuk-card", has_text="Other information")
        expect(card).to_be_visible()
        row = card.locator(
            ".nhsuk-summary-list__row", has_text="Hormone replacement therapy (HRT)"
        )
        expect(row).to_contain_text("Not provided")

    def when_i_change_to_an_appointment_tab(self, tab_name):
        secondary_nav = self.page.locator(".app-secondary-navigation")
        expect(secondary_nav).to_be_visible()
        appointment_details_tab = secondary_nav.get_by_text(tab_name)
        appointment_details_tab.click()
