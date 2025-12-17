from datetime import date

import pytest
from dateutil.relativedelta import relativedelta
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertRedirects

from manage_breast_screening.participants.forms import ParticipantReportedMammogramForm
from manage_breast_screening.participants.models import ParticipantReportedMammogram
from manage_breast_screening.participants.models.appointment import AppointmentStatus
from manage_breast_screening.participants.tests.factories import AppointmentFactory


@pytest.mark.django_db
class TestShowAppointment:
    def test_get(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_previous_mammogram",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_post_with_missing_parameters(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_previous_mammogram",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200
        assertInHTML(
            """
            <ul class="nhsuk-list nhsuk-error-summary__list">
                <li><a href="#id_location_type">Select where the breast x-rays were taken</a></li>
                <li><a href="#id_when_taken">Select when the x-rays were taken</a></li>
                <li><a href="#id_name_is_the_same">Select if the x-rays were taken with the same name</a></li>
            </ul>
            """,
            response.text,
        )

    def test_post_date_unsure(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        return_url = reverse(
            "mammograms:record_medical_information",
            kwargs={"pk": appointment.pk},
        )

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_previous_mammogram",
                kwargs={"pk": appointment.pk},
            ),
            {
                "return_url": return_url,
                "location_type": ParticipantReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT,
                "when_taken": ParticipantReportedMammogramForm.WhenTaken.NOT_SURE,
                "name_is_the_same": ParticipantReportedMammogramForm.NameIsTheSame.YES,
            },
        )

        assertRedirects(response, return_url)

    def test_post_approx_date(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        return_url = reverse(
            "mammograms:record_medical_information",
            kwargs={"pk": appointment.pk},
        )

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_previous_mammogram",
                kwargs={"pk": appointment.pk},
            ),
            {
                "return_url": return_url,
                "location_type": ParticipantReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT,
                "when_taken": ParticipantReportedMammogramForm.WhenTaken.APPROX,
                "approx_date": "last month",
                "name_is_the_same": ParticipantReportedMammogramForm.NameIsTheSame.YES,
            },
        )

        assertRedirects(response, return_url)

    @pytest.mark.parametrize(
        "exact_date",
        [
            date.today() - relativedelta(months=6),
            date.today() - relativedelta(months=6) - relativedelta(days=1),
            date.today() - relativedelta(years=50),
        ],
    )
    def test_post_exact_date_six_months_ago_or_later(
        self, clinical_user_client, exact_date
    ):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        return_url = reverse(
            "mammograms:record_medical_information",
            kwargs={"pk": appointment.pk},
        )

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_previous_mammogram",
                kwargs={"pk": appointment.pk},
            ),
            {
                "return_url": return_url,
                "location_type": ParticipantReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT,
                "when_taken": ParticipantReportedMammogramForm.WhenTaken.EXACT,
                "exact_date_0": exact_date.day,
                "exact_date_1": exact_date.month,
                "exact_date_2": exact_date.year,
                "name_is_the_same": ParticipantReportedMammogramForm.NameIsTheSame.YES,
            },
        )

        assertRedirects(response, return_url)

    @pytest.mark.parametrize(
        "exact_date",
        [
            date.today(),
            date.today() - relativedelta(months=6) + relativedelta(days=1),
            date.today() - relativedelta(months=6) + relativedelta(days=2),
        ],
    )
    def test_post_exact_date_within_last_six_months(
        self, clinical_user_client, exact_date
    ):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        return_url = reverse(
            "mammograms:record_medical_information",
            kwargs={"pk": appointment.pk},
        )

        assert (
            ParticipantReportedMammogram.objects.filter(
                participant=appointment.participant
            ).count()
            == 0
        )

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_previous_mammogram",
                kwargs={"pk": appointment.pk},
            ),
            {
                "return_url": return_url,
                "location_type": ParticipantReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT,
                "when_taken": ParticipantReportedMammogramForm.WhenTaken.EXACT,
                "exact_date_0": exact_date.day,
                "exact_date_1": exact_date.month,
                "exact_date_2": exact_date.year,
                "name_is_the_same": ParticipantReportedMammogramForm.NameIsTheSame.YES,
            },
        )

        mammogram = ParticipantReportedMammogram.objects.filter(
            participant=appointment.participant
        ).first()

        assertRedirects(
            response,
            reverse(
                "mammograms:appointment_should_not_proceed",
                kwargs={
                    "appointment_pk": appointment.pk,
                    "participant_reported_mammogram_pk": mammogram.pk,
                },
            )
            + f"?return_url={return_url}",
        )
        assert appointment.current_status.state == AppointmentStatus.CONFIRMED

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:attended_not_screened",
                kwargs={"appointment_pk": appointment.pk},
            ),
        )
        assertRedirects(
            response,
            reverse(
                "clinics:show",
                kwargs={"pk": appointment.clinic_slot.clinic.pk},
            ),
        )
        assert (
            appointment.current_status.state == AppointmentStatus.ATTENDED_NOT_SCREENED
        )
