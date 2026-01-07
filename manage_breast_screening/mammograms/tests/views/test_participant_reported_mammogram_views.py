from datetime import date

import pytest
from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertMessages, assertRedirects

from manage_breast_screening.participants.forms import AppointmentReportedMammogramForm
from manage_breast_screening.participants.models import AppointmentReportedMammogram
from manage_breast_screening.participants.models.appointment import AppointmentStatus
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    AppointmentReportedMammogramFactory,
)


@pytest.fixture
def appointment_reported_mammogram(appointment):
    return AppointmentReportedMammogramFactory.create(
        appointment=appointment,
        location_type=AppointmentReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT,
    )


@pytest.mark.django_db
class TestAddAppointmentReportedMammogram:
    def test_renders_response(self, clinical_user_client):
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

    def test_invalid_post_displays_errors(self, clinical_user_client):
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

    def test_valid_post_redirects_to_appointment(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_previous_mammogram",
                kwargs={"pk": appointment.pk},
            ),
            {
                "location_type": AppointmentReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT,
                "when_taken": AppointmentReportedMammogramForm.WhenTaken.NOT_SURE,
                "name_is_the_same": AppointmentReportedMammogramForm.NameIsTheSame.YES,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            ),
        )
        assertMessages(
            response,
            [
                messages.Message(
                    level=messages.SUCCESS,
                    message="Added a previous mammogram",
                )
            ],
        )

    @pytest.mark.parametrize(
        "exact_date",
        [
            date.today() - relativedelta(months=6),
            date.today() - relativedelta(months=6) - relativedelta(days=1),
            date.today() - relativedelta(years=50),
        ],
    )
    def test_post_exact_date_six_months_or_more(self, clinical_user_client, exact_date):
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
                "location_type": AppointmentReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT,
                "when_taken": AppointmentReportedMammogramForm.WhenTaken.EXACT,
                "exact_date_0": exact_date.day,
                "exact_date_1": exact_date.month,
                "exact_date_2": exact_date.year,
                "name_is_the_same": AppointmentReportedMammogramForm.NameIsTheSame.YES,
            },
        )

        assertRedirects(response, return_url)
        assertMessages(
            response,
            [
                messages.Message(
                    level=messages.SUCCESS,
                    message="Added a previous mammogram",
                )
            ],
        )

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
            AppointmentReportedMammogram.objects.filter(appointment=appointment).count()
            == 0
        )

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_previous_mammogram",
                kwargs={"pk": appointment.pk},
            ),
            {
                "return_url": return_url,
                "location_type": AppointmentReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT,
                "when_taken": AppointmentReportedMammogramForm.WhenTaken.EXACT,
                "exact_date_0": exact_date.day,
                "exact_date_1": exact_date.month,
                "exact_date_2": exact_date.year,
                "name_is_the_same": AppointmentReportedMammogramForm.NameIsTheSame.YES,
            },
        )

        mammogram = AppointmentReportedMammogram.objects.filter(
            appointment=appointment
        ).first()

        assertRedirects(
            response,
            reverse(
                "mammograms:appointment_should_not_proceed",
                kwargs={
                    "appointment_pk": appointment.pk,
                    "appointment_reported_mammogram_pk": mammogram.pk,
                },
            )
            + f"?return_url={return_url}",
        )
        assert appointment.current_status.name == AppointmentStatus.CONFIRMED

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
            appointment.current_status.name == AppointmentStatus.ATTENDED_NOT_SCREENED
        )


@pytest.mark.django_db
class TestChangeAppointmentReportedMammogram:
    @pytest.fixture
    def appointment(self, clinical_user_client):
        return AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )

    @pytest.fixture
    def appointment_reported_mammogram(self, appointment):
        return AppointmentReportedMammogramFactory.create(
            appointment=appointment,
            location_type=AppointmentReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT,
        )

    def test_renders_response(
        self, clinical_user_client, appointment, appointment_reported_mammogram
    ):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:change_previous_mammogram",
                kwargs={
                    "pk": appointment.pk,
                    "appointment_reported_mammogram_pk": appointment_reported_mammogram.pk,
                },
            )
        )
        assert response.status_code == 200

    def test_invalid_post_displays_errors(
        self, clinical_user_client, appointment, appointment_reported_mammogram
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:change_previous_mammogram",
                kwargs={
                    "pk": appointment.pk,
                    "appointment_reported_mammogram_pk": appointment_reported_mammogram.pk,
                },
            ),
            {},
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

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, appointment, appointment_reported_mammogram
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:change_previous_mammogram",
                kwargs={
                    "pk": appointment.pk,
                    "appointment_reported_mammogram_pk": appointment_reported_mammogram.pk,
                },
            ),
            {
                "location_type": AppointmentReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT,
                "when_taken": AppointmentReportedMammogramForm.WhenTaken.NOT_SURE,
                "name_is_the_same": AppointmentReportedMammogramForm.NameIsTheSame.YES,
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            ),
        )
        assertMessages(
            response,
            [
                messages.Message(
                    level=messages.SUCCESS,
                    message="Updated a previous mammogram",
                )
            ],
        )

    @pytest.mark.parametrize(
        "exact_date",
        [
            date.today() - relativedelta(months=6),
            date.today() - relativedelta(months=6) - relativedelta(days=1),
            date.today() - relativedelta(years=50),
        ],
    )
    def test_post_exact_date_six_months_or_more(
        self,
        clinical_user_client,
        appointment,
        appointment_reported_mammogram,
        exact_date,
    ):
        return_url = reverse(
            "mammograms:record_medical_information",
            kwargs={"pk": appointment.pk},
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:change_previous_mammogram",
                kwargs={
                    "pk": appointment.pk,
                    "appointment_reported_mammogram_pk": appointment_reported_mammogram.pk,
                },
            ),
            {
                "return_url": return_url,
                "location_type": AppointmentReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT,
                "when_taken": AppointmentReportedMammogramForm.WhenTaken.EXACT,
                "exact_date_0": exact_date.day,
                "exact_date_1": exact_date.month,
                "exact_date_2": exact_date.year,
                "name_is_the_same": AppointmentReportedMammogramForm.NameIsTheSame.YES,
            },
        )

        assertRedirects(response, return_url)
        assertMessages(
            response,
            [
                messages.Message(
                    level=messages.SUCCESS,
                    message="Updated a previous mammogram",
                )
            ],
        )

    @pytest.mark.parametrize(
        "exact_date",
        [
            date.today(),
            date.today() - relativedelta(months=6) + relativedelta(days=1),
            date.today() - relativedelta(months=6) + relativedelta(days=2),
        ],
    )
    def test_post_exact_date_within_last_six_months(
        self,
        clinical_user_client,
        appointment,
        appointment_reported_mammogram,
        exact_date,
    ):
        return_url = reverse(
            "mammograms:record_medical_information",
            kwargs={"pk": appointment.pk},
        )

        assert (
            AppointmentReportedMammogram.objects.filter(appointment=appointment).count()
            == 1
        )

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:change_previous_mammogram",
                kwargs={
                    "pk": appointment.pk,
                    "appointment_reported_mammogram_pk": appointment_reported_mammogram.pk,
                },
            ),
            {
                "return_url": return_url,
                "location_type": AppointmentReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT,
                "when_taken": AppointmentReportedMammogramForm.WhenTaken.EXACT,
                "exact_date_0": exact_date.day,
                "exact_date_1": exact_date.month,
                "exact_date_2": exact_date.year,
                "name_is_the_same": AppointmentReportedMammogramForm.NameIsTheSame.YES,
            },
        )

        mammogram = AppointmentReportedMammogram.objects.filter(
            appointment=appointment
        ).first()

        assertRedirects(
            response,
            reverse(
                "mammograms:appointment_should_not_proceed",
                kwargs={
                    "appointment_pk": appointment.pk,
                    "appointment_reported_mammogram_pk": mammogram.pk,
                },
            )
            + f"?return_url={return_url}",
        )
        assert appointment.current_status.name == AppointmentStatus.CONFIRMED

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
            appointment.current_status.name == AppointmentStatus.ATTENDED_NOT_SCREENED
        )


@pytest.mark.django_db
class TestDeleteAppointmentReportedMammogram:
    def test_delete_previous_mammogram(
        self,
        clinical_user_client,
        appointment,
        appointment_reported_mammogram,
    ):
        assert AppointmentReportedMammogram.objects.filter(
            pk=appointment_reported_mammogram.pk
        ).exists()

        clinical_user_client.http.post(
            reverse(
                "mammograms:delete_previous_mammogram",
                kwargs={
                    "pk": appointment.pk,
                    "appointment_reported_mammogram_pk": appointment_reported_mammogram.pk,
                },
            )
        )

        assert not AppointmentReportedMammogram.objects.filter(
            pk=appointment_reported_mammogram.pk
        ).exists()


@pytest.mark.django_db
class TestAppointmentProceedAnywayView:
    @pytest.fixture
    def appointment(self, clinical_user_client):
        return AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )

    @pytest.fixture
    def appointment_reported_mammogram(self, appointment):
        return AppointmentReportedMammogramFactory.create(
            appointment=appointment,
            location_type=AppointmentReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT,
        )

    def test_renders_response(
        self, clinical_user_client, appointment, appointment_reported_mammogram
    ):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:proceed_anyway",
                kwargs={
                    "pk": appointment.pk,
                    "appointment_reported_mammogram_pk": appointment_reported_mammogram.pk,
                },
            )
        )
        assert response.status_code == 200

    def test_invalid_post_displays_errors(
        self, clinical_user_client, appointment, appointment_reported_mammogram
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:proceed_anyway",
                kwargs={
                    "pk": appointment.pk,
                    "appointment_reported_mammogram_pk": appointment_reported_mammogram.pk,
                },
            ),
            {},
        )
        assert response.status_code == 200
        assertInHTML(
            """
            <ul class="nhsuk-list nhsuk-error-summary__list">
                <li><a href="#id_reason_for_continuing">Provide a reason for continuing</a></li>
            </ul>
            """,
            response.text,
        )

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, appointment, appointment_reported_mammogram
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:proceed_anyway",
                kwargs={
                    "pk": appointment.pk,
                    "appointment_reported_mammogram_pk": appointment_reported_mammogram.pk,
                },
            ),
            {
                "reason_for_continuing": "Because I said so",
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            ),
        )
        assertMessages(
            response,
            [
                messages.Message(
                    level=messages.SUCCESS,
                    message="Updated a previous mammogram",
                )
            ],
        )
