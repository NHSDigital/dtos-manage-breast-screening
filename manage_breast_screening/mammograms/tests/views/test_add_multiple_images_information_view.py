import pytest
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertRedirects

from manage_breast_screening.manual_images.models import RepeatReason, RepeatType
from manage_breast_screening.manual_images.tests.factories import (
    SeriesFactory,
    StudyFactory,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
)


@pytest.mark.django_db
class TestAddMultipleImagesInformationView:
    def test_renders_response_with_series(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        study = StudyFactory(appointment=appointment)
        SeriesFactory(study=study, laterality="R", view_position="MLO", count=2)

        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_multiple_images_information",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200
        assert "2 Right MLO images were taken." in response.text

    def test_redirects_when_no_series_with_multiple_images(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        study = StudyFactory(appointment=appointment)
        SeriesFactory(study=study, laterality="R", view_position="MLO", count=1)
        SeriesFactory(study=study, laterality="L", view_position="CC", count=1)

        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_multiple_images_information",
                kwargs={"pk": appointment.pk},
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:check_information",
                kwargs={"pk": appointment.pk},
            ),
        )

    def test_redirects_when_no_study(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )

        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_multiple_images_information",
                kwargs={"pk": appointment.pk},
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:check_information",
                kwargs={"pk": appointment.pk},
            ),
            fetch_redirect_response=False,
        )

    def test_valid_post_saves_data_and_redirects(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        study = StudyFactory(appointment=appointment)
        series = SeriesFactory(
            study=study, laterality="R", view_position="MLO", count=2
        )

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_multiple_images_information",
                kwargs={"pk": appointment.pk},
            ),
            {
                "rmlo_repeat_type": RepeatType.ALL_REPEATS.value,
                "rmlo_repeat_reasons": [
                    RepeatReason.PATIENT_MOVED.value,
                    RepeatReason.MOTION_BLUR.value,
                ],
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:check_information",
                kwargs={"pk": appointment.pk},
            ),
        )

        series.refresh_from_db()
        assert series.repeat_type == RepeatType.ALL_REPEATS.value
        assert series.repeat_reasons == [
            RepeatReason.PATIENT_MOVED.value,
            RepeatReason.MOTION_BLUR.value,
        ]

    def test_invalid_post_renders_errors(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        study = StudyFactory(appointment=appointment)
        SeriesFactory(study=study, laterality="R", view_position="MLO", count=2)

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_multiple_images_information",
                kwargs={"pk": appointment.pk},
            ),
            {},
        )

        assert response.status_code == 200
        assertInHTML(
            '<a href="#id_rmlo_repeat_type">Select whether the additional images were repeats</a>',
            response.text,
        )

    def test_shows_question_for_count_2(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        study = StudyFactory(appointment=appointment)
        SeriesFactory(study=study, laterality="L", view_position="CC", count=2)

        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_multiple_images_information",
                kwargs={"pk": appointment.pk},
            )
        )

        assert response.status_code == 200
        assert "Was the additional image a repeat?" in response.text

    def test_shows_question_for_count_greater_than_2(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        study = StudyFactory(appointment=appointment)
        SeriesFactory(study=study, laterality="L", view_position="CC", count=3)

        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_multiple_images_information",
                kwargs={"pk": appointment.pk},
            )
        )

        assert response.status_code == 200
        assert "Were the additional images repeats?" in response.text

    def test_multiple_series_all_shown(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        study = StudyFactory(appointment=appointment)
        SeriesFactory(study=study, laterality="R", view_position="MLO", count=2)
        SeriesFactory(study=study, laterality="L", view_position="CC", count=3)

        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_multiple_images_information",
                kwargs={"pk": appointment.pk},
            )
        )

        assert response.status_code == 200
        assert "2 Right MLO images were taken." in response.text
        assert "3 Left CC images were taken." in response.text

    def test_post_with_some_repeats_saves_count(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        study = StudyFactory(appointment=appointment)
        series = SeriesFactory(
            study=study, laterality="L", view_position="MLO", count=4
        )

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_multiple_images_information",
                kwargs={"pk": appointment.pk},
            ),
            {
                "lmlo_repeat_type": RepeatType.SOME_REPEATS.value,
                "lmlo_repeat_count": "2",
                "lmlo_repeat_reasons": [RepeatReason.EQUIPMENT_FAULT.value],
            },
        )

        assertRedirects(
            response,
            reverse(
                "mammograms:check_information",
                kwargs={"pk": appointment.pk},
            ),
        )

        series.refresh_from_db()
        assert series.repeat_type == RepeatType.SOME_REPEATS.value
        assert series.repeat_count == 2
        assert series.repeat_reasons == [RepeatReason.EQUIPMENT_FAULT.value]
