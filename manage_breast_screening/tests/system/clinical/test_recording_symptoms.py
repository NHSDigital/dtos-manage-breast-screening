from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)

from ..system_test_setup import SystemTestCase


class TestRecordingSymptoms(SystemTestCase):
    def test_adding_a_symptom(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment()
        # self.and_i_am_on_the_medical_information_page()
        # self.when_i_click_on_add_a_lump()
        # self.then_i_see_the_add_a_lump_form()

        # self.when_i_select_right_breast()
        # self.and_i_select_less_than_three_months()
        # self.and_i_select_no_the_symptom_has_not_been_investigated()
        # self.and_i_click_submit()
        # self.then_i_am_back_on_the_medical_information_page()
        # self.and_the_lump_on_the_right_breast_is_listed()

    def test_editing_and_removing_symptoms(self):
        # self.given_i_am_logged_in_as_a_clinical_user()
        # self.and_there_is_an_appointment()
        # self.and_there_is_a_lump_recorded()
        # self.and_there_is_a_swelling_recorded_on_the_right_breast()
        # self.and_i_am_on_the_medical_information_page()

        # self.when_i_click_to_edit_the_swelling()
        # self.then_i_see_the_swelling_or_shape_change_form()

        # self.when_i_select_left_breast()
        # self.and_i_click_submit()
        # self.then_i_am_back_on_the_medical_information_page()
        # self.and_the_swelling_is_now_on_the_left_breast()

        # self.when_i_delete_the_lump()
        # self.and_i_click_confirm()
        # self.then_i_am_back_on_the_medical_information_page()
        # self.and_i_no_longer_see_the_lump()
        pass

    def and_there_is_an_appointment(self):
        self.participant = ParticipantFactory(first_name="Janet", last_name="Williams")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(screening_episode=self.screening_episode)
        self.provider = self.appointment.provider
