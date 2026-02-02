import pytest
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertQuerySetEqual, assertRedirects

from manage_breast_screening.mammograms.forms.images.add_image_details_form import (
    AddImageDetailsForm,
)
from manage_breast_screening.manual_images.models import IncompleteImagesReason
from manage_breast_screening.participants.models.appointment import (
    AppointmentWorkflowStepCompletion,
)
from manage_breast_screening.participants.tests.factories import AppointmentFactory


@pytest.mark.django_db
class TestAddImageDetailsView:
    def test_renders_response(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_image_details",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_with_counts_for_all_images(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_image_details",
                kwargs={"pk": appointment.pk},
            ),
            {
                "rmlo_count": "1",
                "rcc_count": "2",
                "right_eklund_count": "3",
                "lmlo_count": "4",
                "lcc_count": "5",
                "left_eklund_count": "6",
                "additional_details": "Some additional details",
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:add_multiple_images_information",
                kwargs={"pk": appointment.pk},
            ),
        )

        study = appointment.study
        assert study.additional_details == "Some additional details"

        series_list = study.series_set.all()
        assert len(series_list) == 6
        self._assert_series(series_list[0], "MLO", "R", 1)
        self._assert_series(series_list[1], "CC", "R", 2)
        self._assert_series(series_list[2], "EKLUND", "R", 3)
        self._assert_series(series_list[3], "MLO", "L", 4)
        self._assert_series(series_list[4], "CC", "L", 5)
        self._assert_series(series_list[5], "EKLUND", "L", 6)
        self._assert_take_images_step_not_completed(appointment)

    def test_valid_post_with_high_count(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_image_details",
                kwargs={"pk": appointment.pk},
            ),
            {
                "rmlo_count": "0",
                "rcc_count": "0",
                "right_eklund_count": "0",
                "lmlo_count": "0",
                "lcc_count": "20",
                "left_eklund_count": "0",
                "additional_details": "",
                "not_all_mammograms_taken": "true",
                "reasons_incomplete": [IncompleteImagesReason.CONSENT_WITHDRAWN],
                "reasons_incomplete_details": "abc",
                "imperfect_but_best_possible": "true",
                "should_recall": AddImageDetailsForm.RecallChoices.PARTIAL_MAMMOGRAPHY,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:add_multiple_images_information",
                kwargs={"pk": appointment.pk},
            ),
        )

        study = appointment.study
        assert study.additional_details == ""

        series_list = study.series_set.all()
        assert len(series_list) == 1
        self._assert_series(series_list[0], "CC", "L", 20)
        self._assert_take_images_step_not_completed(appointment)

    def test_valid_post_with_all_counts_one_redirects_to_check_information(
        self, clinical_user_client
    ):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_image_details",
                kwargs={"pk": appointment.pk},
            ),
            {
                "rmlo_count": "1",
                "rcc_count": "1",
                "right_eklund_count": "0",
                "lmlo_count": "1",
                "lcc_count": "1",
                "left_eklund_count": "0",
                "additional_details": "",
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:check_information",
                kwargs={"pk": appointment.pk},
            ),
        )

        study = appointment.study
        series_list = study.series_set.all()
        assert len(series_list) == 4
        self._assert_take_images_step_completed(appointment, clinical_user_client.user)

    def test_invalid_post_renders_response_with_errors(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_image_details",
                kwargs={"pk": appointment.pk},
            ),
            {
                "rmlo_count": "-1",
                "rcc_count": "1.5",
                "right_eklund_count": "a",
                "lmlo_count": "21",
                "lcc_count": "100",
                "left_eklund_count": "",
                "additional_details": "Some additional details",
            },
        )
        assert response.status_code == 200
        assertInHTML(
            """
            <ul class="nhsuk-list nhsuk-error-summary__list">
                <li><a href="#id_rmlo_count">Number of RMLO images must be at least 0</a></li>
                <li><a href="#id_rcc_count">Enter a valid number of RCC images</a></li>
                <li><a href="#id_right_eklund_count">Enter a valid number of Right Eklund images</a></li>
                <li><a href="#id_lmlo_count">Number of LMLO images must be at most 20</a></li>
                <li><a href="#id_lcc_count">Number of LCC images must be at most 20</a></li>
                <li><a href="#id_left_eklund_count">Enter the number of Left Eklund images</a></li>
            </ul>
            """,
            response.text,
        )

    def test_zero_image_count_post_renders_response_with_errors(
        self, clinical_user_client
    ):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_image_details",
                kwargs={"pk": appointment.pk},
            ),
            {
                "rmlo_count": "0",
                "rcc_count": "0",
                "right_eklund_count": "0",
                "lmlo_count": "0",
                "lcc_count": "0",
                "left_eklund_count": "0",
            },
        )
        assert response.status_code == 200
        assertInHTML(
            """
            <ul class="nhsuk-list nhsuk-error-summary__list">
                <li>Enter at least one image count</li>
            </ul>
            """,
            response.text,
        )

    def _assert_series(
        self, series, expected_view_position, expected_laterality, expected_count
    ):
        assert series.view_position == expected_view_position
        assert series.laterality == expected_laterality
        assert series.count == expected_count

    def _assert_take_images_step_completed(self, appointment, user):
        assertQuerySetEqual(
            appointment.completed_workflow_steps.filter(created_by=user)
            .values_list("step_name", flat=True)
            .distinct(),
            [AppointmentWorkflowStepCompletion.StepNames.TAKE_IMAGES],
        )

    def _assert_take_images_step_not_completed(self, appointment):
        assert not appointment.completed_workflow_steps.filter(
            step_name=AppointmentWorkflowStepCompletion.StepNames.TAKE_IMAGES
        ).exists()
