import pytest
from django.urls import reverse
from playwright.sync_api import expect

from manage_breast_screening.participants.models.appointment import (
    AppointmentStatusNames,
    AppointmentWorkflowStepCompletion,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ScreeningEpisodeFactory,
)
from manage_breast_screening.tests.system.system_test_setup import SystemTestCase


@pytest.mark.usefixtures("known_datetime")
class TestRecordingBreastFeatures(SystemTestCase):
    def test_recording_breast_features(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_with_no_medical_information_added()
        self.and_i_am_on_the_record_medical_information_page()
        self.then_i_see_that_there_are_no_breast_features()

        self.when_i_click_on_add_breast_features()
        self.then_i_am_on_the_breast_feature_form()

        self.when_i_click_on_the_region("Right central")
        self.and_i_see_the_feature_card("Right central")
        self.then_i_see_a_marker_on_the_diagram("?")

        self.when_i_select_a_feature("Mole")
        self.and_i_add_the_feature()
        self.then_i_see_a_marker_on_the_diagram("1")
        self.and_i_see_the_feature_card_is_hidden()
        self.and_i_see_the_key_lists_feature("Mole", "Right central")

        self.when_i_save_the_form()
        self.then_i_am_back_on_the_record_medical_information_page()
        self.and_i_see_the_feature_is_added("Right central")

        self.when_i_click_on_the_view_or_edit_button()
        self.then_i_am_on_the_breast_feature_form()

        self.when_i_save_the_form()
        self.then_i_am_back_on_the_record_medical_information_page()
        self.and_i_see_the_feature_is_added("Right central")

    def test_cancelling_a_pending_feature(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_with_no_medical_information_added()
        self.and_i_am_on_the_record_breast_features_page()

        self.when_i_click_on_the_region("Right central")
        self.and_i_see_the_feature_card("Right central")
        self.then_i_see_a_marker_on_the_diagram("?")

        self.when_i_cancel_the_feature()
        self.then_i_see_no_features_added()

    def test_removing_a_pending_feature(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_with_no_medical_information_added()
        self.and_i_am_on_the_record_breast_features_page()

        self.when_i_click_on_the_region("Right central")
        self.and_i_see_the_feature_card("Right central")
        self.then_i_see_a_marker_on_the_diagram("?")

        self.when_i_remove_the_feature()
        self.then_i_see_no_features_added()

    def test_moving_a_pending_feature_to_a_different_region(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_with_no_medical_information_added()
        self.and_i_am_on_the_record_breast_features_page()

        self.when_i_click_on_the_region("Right central")
        self.and_i_see_the_feature_card("Right central")
        self.then_i_see_a_marker_on_the_diagram("?")
        self.and_i_select_a_feature("Mole")

        self.when_i_click_on_the_region("Left upper inner")
        self.and_i_see_the_feature_card("Left upper inner", "Mole")
        self.then_i_see_a_marker_on_the_diagram("?")

    def test_editing_an_existing_feature_from_diagram(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_with_no_medical_information_added()
        self.and_i_am_on_the_record_breast_features_page()
        self.and_i_have_added_a_feature("Right central", "Mole")

        self.when_i_click_the_marker_on_the_diagram("1")
        self.then_i_see_the_feature_card("Right central", "Mole")

        self.when_i_select_a_feature("Scar")
        self.and_i_save_the_feature()
        self.then_i_see_the_key_lists_feature("Scar", "Right central")

    def test_editing_an_existing_feature_from_key(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_with_no_medical_information_added()
        self.and_i_am_on_the_record_breast_features_page()
        self.and_i_have_added_a_feature("Right central", "Mole")

        self.when_i_click_the_marker_in_the_key("1")
        self.then_i_see_the_feature_card("Right central", "Mole")

    def test_cancelling_an_edit(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_with_no_medical_information_added()
        self.and_i_am_on_the_record_breast_features_page()
        self.and_i_have_added_a_feature("Right central", "Mole")

        self.when_i_click_the_marker_on_the_diagram("1")
        self.then_i_see_the_feature_card("Right central", "Mole")

        self.when_i_cancel_the_feature()
        self.then_i_see_the_feature_card_is_hidden()
        self.and_i_see_a_marker_on_the_diagram("1")
        self.and_i_see_the_key_lists_feature("Mole", "Right central")

    def test_removing_an_existing_feature(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_with_no_medical_information_added()
        self.and_i_am_on_the_record_breast_features_page()
        self.and_i_have_added_a_feature("Right central", "Mole")

        self.when_i_click_the_marker_on_the_diagram("1")
        self.then_i_see_the_feature_card("Right central", "Mole")

        self.when_i_remove_the_feature()
        self.then_i_see_no_features_added()

    def test_clearing_all_features(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_with_no_medical_information_added()
        self.and_i_am_on_the_record_breast_features_page()
        self.and_i_have_added_a_feature("Right central", "Mole")

        self.when_i_clear_all_features()
        self.then_i_see_no_features_added()

    def test_add_validates_feature_selection(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_with_no_medical_information_added()
        self.and_i_am_on_the_record_breast_features_page()

        self.when_i_click_on_the_region("Right central")
        self.and_i_see_the_feature_card("Right central")
        self.then_i_see_a_marker_on_the_diagram("?")

        self.when_i_add_the_feature()
        self.then_the_first_radio_is_focused()

    def test_adding_multiple_features(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_with_no_medical_information_added()
        self.and_i_am_on_the_record_breast_features_page()

        self.when_i_click_on_the_region("Right central")
        self.and_i_select_a_feature("Mole")
        self.and_i_add_the_feature()
        self.then_i_see_a_marker_on_the_diagram("1")
        self.and_i_see_the_key_lists_feature("Mole", "Right central")
        self.and_i_see_the_region_is_active("Right central")

        self.when_i_click_on_the_region("Left upper inner")
        self.and_i_select_a_feature("Scar")
        self.and_i_add_the_feature()
        self.then_i_see_a_marker_on_the_diagram("2")
        self.and_i_see_the_key_lists_feature("Mole", "Right central")
        self.and_i_see_the_key_lists_feature("Scar", "Left upper inner")
        self.and_i_see_the_region_is_active("Right central")
        self.and_i_see_the_region_is_active("Left upper inner")

    def test_accessibility(self):
        self.given_i_am_logged_in_as_a_clinical_user()
        self.and_there_is_an_appointment_with_no_medical_information_added()
        self.and_i_am_on_the_record_breast_features_page()
        self.then_the_accessibility_baseline_is_met()

    def given_there_is_an_appointment_with_no_medical_information_added(self):
        self.participant = ParticipantFactory(first_name="Janet", last_name="Williams")
        self.screening_episode = ScreeningEpisodeFactory(participant=self.participant)
        self.appointment = AppointmentFactory(
            screening_episode=self.screening_episode,
            clinic_slot__clinic__setting__provider=self.current_provider,
            current_status=AppointmentStatusNames.IN_PROGRESS,
            current_status__created_by=self.current_user,
        )
        self.appointment.completed_workflow_steps.create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY,
            created_by=self.current_user,
        )

    def given_i_am_on_the_record_medical_information_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": self.appointment.pk},
            )
        )

    def given_i_am_on_the_record_breast_features_page(self):
        self.page.goto(
            self.live_server_url
            + reverse(
                "mammograms:update_breast_features",
                kwargs={"pk": self.appointment.pk},
            )
        )

    def given_i_have_added_a_feature(self, region, label):
        self.when_i_click_on_the_region(region)
        self.page.get_by_label(label).check()
        self.page.get_by_role("button").filter(has_text="Add").click()

    and_there_is_an_appointment_with_no_medical_information_added = (
        given_there_is_an_appointment_with_no_medical_information_added
    )
    and_i_am_on_the_record_medical_information_page = (
        given_i_am_on_the_record_medical_information_page
    )
    and_i_am_on_the_record_breast_features_page = (
        given_i_am_on_the_record_breast_features_page
    )
    and_i_have_added_a_feature = given_i_have_added_a_feature

    def then_i_see_that_there_are_no_breast_features(self):
        card = self.page.locator("#breast-features")
        expect(card).to_contain_text(
            "No breast features have been recorded for this participant."
        )

    def when_i_click_on_add_breast_features(self):
        self.page.get_by_text("Add a feature").click()

    def when_i_click_on_the_view_or_edit_button(self):
        self.page.get_by_text("View or edit breast features").click()

    REGION_SELECTORS = {
        "Right central": ".app-breast-diagram__regions-right .right_central",
        "Left upper inner": ".app-breast-diagram__regions-left .left_upper_inner",
    }

    def when_i_click_on_the_region(self, region_name):
        self.page.locator(self.REGION_SELECTORS[region_name]).click(force=True)

    def when_i_select_a_feature(self, label):
        self.page.get_by_label(label).check()

    def when_i_add_the_feature(self):
        self.page.get_by_role("button").filter(has_text="Add").click()

    def when_i_save_the_form(self):
        self.page.get_by_role("button").filter(has_text="Save").click()

    def when_i_click_the_marker_on_the_diagram(self, number):
        figure = self.page.locator("figure.app-image-map")
        figure.locator("button.app-image-marker").filter(has_text=number).click()

    def when_i_click_the_marker_in_the_key(self, number):
        self.page.locator(".app-image-key__items a.app-image-marker").filter(
            has=self.page.locator(".app-image-marker__number", has_text=number)
        ).click()

    def when_i_cancel_the_feature(self):
        self.page.get_by_role("button").filter(has_text="Cancel").click()

    def when_i_remove_the_feature(self):
        self.page.get_by_role("button").filter(has_text="Remove").click()

    def when_i_save_the_feature(self):
        self.page.get_by_role("button").filter(has_text="Save changes").click()
        card = self.page.locator(".app-breast-diagram__card")
        expect(card).to_be_hidden()

    def when_i_clear_all_features(self):
        self.page.get_by_role("button").filter(has_text="Clear all features").click()

    and_i_select_a_feature = when_i_select_a_feature
    and_i_add_the_feature = when_i_add_the_feature
    and_i_save_the_feature = when_i_save_the_feature

    def then_i_see_a_marker_on_the_diagram(self, number):
        figure = self.page.locator("figure.app-image-map")
        marker = figure.locator("button.app-image-marker").filter(has_text=number)
        expect(marker).to_be_visible()

    def then_i_see_no_markers_on_the_diagram(self):
        figure = self.page.locator("figure.app-image-map")
        expect(figure.locator("button.app-image-marker")).to_have_count(0)

    def then_i_see_the_feature_card_is_hidden(self):
        card = self.page.locator(".app-breast-diagram__card")
        expect(card).to_be_hidden()

    def then_i_see_the_feature_card(self, region, label=None):
        card = self.page.locator(".app-breast-diagram__card")
        expect(card).to_be_visible()
        expect(card.locator(".app-breast-diagram__region")).to_have_text(region)
        if label:
            expect(self.page.get_by_label(label)).to_be_checked()

    def then_i_see_the_key_is_hidden(self):
        expect(self.page.locator(".app-image-key")).to_be_hidden()

    def then_i_see_no_features_added(self):
        self.then_i_see_no_markers_on_the_diagram()
        self.then_i_see_the_feature_card_is_hidden()
        self.then_i_see_the_key_is_hidden()

    def then_i_see_the_key_lists_feature(self, label, region):
        key = self.page.locator(".app-image-key")
        expect(key).to_be_visible()

        item = key.locator(".app-image-key__item").filter(
            has=self.page.locator(".app-image-marker__label", has_text=label)
        )
        expect(item).to_be_visible()
        expect(item.locator(".app-image-key__region")).to_have_text(region)

    def then_i_see_the_feature_is_added(self, region_name):
        card = self.page.locator("#breast-features")
        expect(card).to_contain_text("1 breast feature recorded")

        # Check the diagram is there
        figure = card.get_by_role("figure")
        expect(figure).to_be_attached()

        # Check the region is considered selected by the image map
        selector = self.REGION_SELECTORS[region_name]
        expect(figure.locator(selector)).to_have_attribute("data-active", "true")

    def then_i_see_the_region_is_active(self, region_name):
        figure = self.page.locator("figure.app-image-map")
        selector = self.REGION_SELECTORS[region_name]
        expect(figure.locator(selector)).to_have_attribute("data-active", "true")

    def then_the_first_radio_is_focused(self):
        first_radio = self.page.locator("input[name='feature']").first
        expect(first_radio).to_be_focused()

    def then_i_am_on_the_breast_feature_form(self):
        self.assert_page_title_contains("Record breast features")
        self.expect_url("mammograms:update_breast_features", pk=self.appointment.pk)

    def then_i_am_back_on_the_record_medical_information_page(self):
        self.expect_url("mammograms:record_medical_information", pk=self.appointment.pk)

    and_i_see_a_marker_on_the_diagram = then_i_see_a_marker_on_the_diagram
    and_i_see_the_feature_card_is_hidden = then_i_see_the_feature_card_is_hidden
    and_i_see_the_feature_card = then_i_see_the_feature_card
    and_i_see_the_key_lists_feature = then_i_see_the_key_lists_feature
    and_i_see_the_feature_is_added = then_i_see_the_feature_is_added
    and_i_see_the_region_is_active = then_i_see_the_region_is_active
