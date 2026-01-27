from datetime import date

import pytest
from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.urls import reverse
from pytest_django.asserts import (
    assertInHTML,
    assertMessages,
    assertQuerySetEqual,
    assertRedirects,
)

from manage_breast_screening.participants.forms import ParticipantReportedMammogramForm
from manage_breast_screening.participants.models import ParticipantReportedMammogram
from manage_breast_screening.participants.models.appointment import (
    AppointmentStatusNames,
    AppointmentWorkflowStepCompletion,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
    ParticipantReportedMammogramFactory,
)

DATES_SIX_MONTHS_OR_MORE = [
    date.today() - relativedelta(months=6),
    date.today() - relativedelta(months=6) - relativedelta(days=1),
    date.today() - relativedelta(years=50),
]

DATES_WITHIN_LAST_SIX_MONTHS = [
    date.today(),
    date.today() - relativedelta(months=6) + relativedelta(days=1),
    date.today() - relativedelta(months=6) + relativedelta(days=2),
]


def build_exact_date_form_data(exact_date, return_url=None):
    """Build form data for submitting an exact mammogram date."""
    data = {
        "location_type": ParticipantReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT,
        "when_taken": ParticipantReportedMammogramForm.WhenTaken.EXACT,
        "exact_date_0": exact_date.day,
        "exact_date_1": exact_date.month,
        "exact_date_2": exact_date.year,
        "name_is_the_same": ParticipantReportedMammogramForm.NameIsTheSame.YES,
    }
    if return_url:
        data["return_url"] = return_url
    return data


def assert_mammogram_validation_errors(response):
    """Assert that the standard mammogram validation errors are displayed."""
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


def assert_attended_not_screened_flow(client, appointment):
    """Assert the attended not screened flow completes correctly."""
    response = client.http.post(
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
        appointment.current_status.name == AppointmentStatusNames.ATTENDED_NOT_SCREENED
    )


def assert_success_message(response, message_text):
    """Assert that a success message is displayed."""
    assertMessages(
        response,
        [
            messages.Message(
                level=messages.SUCCESS,
                message=message_text,
            )
        ],
    )


@pytest.fixture
def participant_reported_mammogram(appointment):
    return ParticipantReportedMammogramFactory.create(
        appointment=appointment,
        location_type=ParticipantReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT,
    )


@pytest.fixture
def valid_mammogram_form_data():
    """Basic valid form data for mammogram submission."""
    return {
        "location_type": ParticipantReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT,
        "when_taken": ParticipantReportedMammogramForm.WhenTaken.NOT_SURE,
        "name_is_the_same": ParticipantReportedMammogramForm.NameIsTheSame.YES,
    }


@pytest.mark.django_db
class TestAddParticipantReportedMammogram:
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
        assert_mammogram_validation_errors(response)

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, valid_mammogram_form_data
    ):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_previous_mammogram",
                kwargs={"pk": appointment.pk},
            ),
            valid_mammogram_form_data,
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            ),
        )
        assert_success_message(response, "Added a previous mammogram")

    @pytest.mark.parametrize("exact_date", DATES_SIX_MONTHS_OR_MORE)
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
            build_exact_date_form_data(exact_date, return_url),
        )

        assertRedirects(response, return_url)
        assert_success_message(response, "Added a previous mammogram")

    @pytest.mark.parametrize("exact_date", DATES_WITHIN_LAST_SIX_MONTHS)
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
            ParticipantReportedMammogram.objects.filter(appointment=appointment).count()
            == 0
        )

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_previous_mammogram",
                kwargs={"pk": appointment.pk},
            ),
            build_exact_date_form_data(exact_date, return_url),
        )

        mammogram = ParticipantReportedMammogram.objects.filter(
            appointment=appointment
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
        assert appointment.current_status.name == AppointmentStatusNames.SCHEDULED

        assert_attended_not_screened_flow(clinical_user_client, appointment)


@pytest.mark.django_db
class TestChangeParticipantReportedMammogram:
    @pytest.fixture
    def appointment(self, clinical_user_client):
        return AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )

    @pytest.fixture
    def participant_reported_mammogram(self, appointment):
        return ParticipantReportedMammogramFactory.create(
            appointment=appointment,
            location_type=ParticipantReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT,
        )

    def test_renders_response(
        self, clinical_user_client, appointment, participant_reported_mammogram
    ):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:change_previous_mammogram",
                kwargs={
                    "pk": appointment.pk,
                    "participant_reported_mammogram_pk": participant_reported_mammogram.pk,
                },
            )
        )
        assert response.status_code == 200

    def test_invalid_post_displays_errors(
        self, clinical_user_client, appointment, participant_reported_mammogram
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:change_previous_mammogram",
                kwargs={
                    "pk": appointment.pk,
                    "participant_reported_mammogram_pk": participant_reported_mammogram.pk,
                },
            ),
            {},
        )
        assert_mammogram_validation_errors(response)

    def test_valid_post_redirects_to_appointment(
        self,
        clinical_user_client,
        appointment,
        participant_reported_mammogram,
        valid_mammogram_form_data,
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:change_previous_mammogram",
                kwargs={
                    "pk": appointment.pk,
                    "participant_reported_mammogram_pk": participant_reported_mammogram.pk,
                },
            ),
            valid_mammogram_form_data,
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            ),
        )
        assert_success_message(response, "Updated a previous mammogram")

    @pytest.mark.parametrize("exact_date", DATES_SIX_MONTHS_OR_MORE)
    def test_post_exact_date_six_months_or_more(
        self,
        clinical_user_client,
        appointment,
        participant_reported_mammogram,
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
                    "participant_reported_mammogram_pk": participant_reported_mammogram.pk,
                },
            ),
            build_exact_date_form_data(exact_date, return_url),
        )

        assertRedirects(response, return_url)
        assert_success_message(response, "Updated a previous mammogram")

    @pytest.mark.parametrize("exact_date", DATES_WITHIN_LAST_SIX_MONTHS)
    def test_post_exact_date_within_last_six_months(
        self,
        clinical_user_client,
        appointment,
        participant_reported_mammogram,
        exact_date,
    ):
        return_url = reverse(
            "mammograms:record_medical_information",
            kwargs={"pk": appointment.pk},
        )

        assert (
            ParticipantReportedMammogram.objects.filter(appointment=appointment).count()
            == 1
        )

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:change_previous_mammogram",
                kwargs={
                    "pk": appointment.pk,
                    "participant_reported_mammogram_pk": participant_reported_mammogram.pk,
                },
            ),
            build_exact_date_form_data(exact_date, return_url),
        )

        mammogram = ParticipantReportedMammogram.objects.filter(
            appointment=appointment
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
        assert appointment.current_status.name == AppointmentStatusNames.SCHEDULED

        assert_attended_not_screened_flow(clinical_user_client, appointment)


@pytest.mark.django_db
class TestDeleteParticipantReportedMammogram:
    def test_delete_previous_mammogram(
        self,
        clinical_user_client,
        appointment,
        participant_reported_mammogram,
    ):
        assert ParticipantReportedMammogram.objects.filter(
            pk=participant_reported_mammogram.pk
        ).exists()

        clinical_user_client.http.post(
            reverse(
                "mammograms:delete_previous_mammogram",
                kwargs={
                    "pk": appointment.pk,
                    "participant_reported_mammogram_pk": participant_reported_mammogram.pk,
                },
            )
        )

        assert not ParticipantReportedMammogram.objects.filter(
            pk=participant_reported_mammogram.pk
        ).exists()


@pytest.mark.django_db
class TestAppointmentProceedAnywayView:
    @pytest.fixture
    def appointment(self, clinical_user_client):
        return AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )

    @pytest.fixture
    def participant_reported_mammogram(self, appointment):
        return ParticipantReportedMammogramFactory.create(
            appointment=appointment,
            location_type=ParticipantReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT,
        )

    def test_renders_response(
        self, clinical_user_client, appointment, participant_reported_mammogram
    ):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:proceed_anyway",
                kwargs={
                    "pk": appointment.pk,
                    "participant_reported_mammogram_pk": participant_reported_mammogram.pk,
                },
            )
        )
        assert response.status_code == 200

    def test_invalid_post_displays_errors(
        self, clinical_user_client, appointment, participant_reported_mammogram
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:proceed_anyway",
                kwargs={
                    "pk": appointment.pk,
                    "participant_reported_mammogram_pk": participant_reported_mammogram.pk,
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
        self, clinical_user_client, appointment, participant_reported_mammogram
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:proceed_anyway",
                kwargs={
                    "pk": appointment.pk,
                    "participant_reported_mammogram_pk": participant_reported_mammogram.pk,
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
        assert_success_message(response, "Updated a previous mammogram")


@pytest.mark.django_db
class TestCompleteScreening:
    def test_renders_response(self, clinical_user_client, appointment):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:check_information",
                kwargs={
                    "pk": appointment.pk,
                },
            )
        )
        assert response.status_code == 200

    def test_valid_transition(self, clinical_user_client):
        participant = ParticipantFactory.create(
            first_name="<b>J</b>ane", last_name="S<i>m</>i&th"
        )
        appointment = AppointmentFactory.create(
            screening_episode__participant=participant,
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
            current_status=AppointmentStatusNames.IN_PROGRESS,
        )

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:complete_screening",
                kwargs={
                    "pk": appointment.pk,
                },
            ),
        )
        assertRedirects(
            response,
            reverse(
                "clinics:show",
                kwargs={"pk": appointment.clinic_slot.clinic.pk},
            ),
        )
        view_appointment_url = reverse(
            "mammograms:show_appointment",
            kwargs={
                "pk": appointment.pk,
            },
        )
        assert_success_message(
            response,
            f"""
            <p class=\"nhsuk-notification-banner__heading\">
                &lt;b&gt;J&lt;/b&gt;ane S&lt;i&gt;m&lt;/&gt;i&amp;th has been screened.
                <a href=\"{view_appointment_url}\" class=\"app-u-nowrap\">
                    View their appointment
                </a>
            </p>
            """,
        )

        assert appointment.current_status.name == AppointmentStatusNames.SCREENED
        assertQuerySetEqual(
            appointment.completed_workflow_steps.filter(
                created_by=clinical_user_client.user
            )
            .values_list("step_name", flat=True)
            .distinct(),
            [AppointmentWorkflowStepCompletion.StepNames.CHECK_INFORMATION],
        )
