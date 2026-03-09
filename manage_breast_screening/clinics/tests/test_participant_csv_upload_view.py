from datetime import timedelta

import pytest
from django.contrib import messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertMessages, assertRedirects

from manage_breast_screening.clinics.models import ClinicSlot, Participant
from manage_breast_screening.clinics.tests.factories import (
    ClinicFactory,
    SettingFactory,
)
from manage_breast_screening.participants.models import Appointment
from manage_breast_screening.participants.models.appointment import (
    AppointmentStatusNames,
)


@pytest.mark.django_db
class TestParticipantCsvUploadView:
    @pytest.fixture
    def superuser_clinic(self, superuser_user_client):
        setting = SettingFactory.create(provider=superuser_user_client.current_provider)
        return ClinicFactory.create(setting=setting)

    def test_get_denied_when_not_superuser(
        self, clinical_user_client, superuser_clinic
    ):
        response = clinical_user_client.http.get(
            reverse(
                "clinics:participant_csv_upload",
                kwargs={"pk": superuser_clinic.pk},
            )
        )
        assert response.status_code == 403

    def test_post_denied_when_not_superuser(
        self, clinical_user_client, superuser_clinic
    ):
        response = clinical_user_client.http.post(
            reverse(
                "clinics:participant_csv_upload",
                kwargs={"pk": superuser_clinic.pk},
            )
        )
        assert response.status_code == 403

    def test_renders_response(self, superuser_user_client, superuser_clinic):
        response = superuser_user_client.http.get(
            reverse(
                "clinics:participant_csv_upload",
                kwargs={"pk": superuser_clinic.pk},
            )
        )
        assert response.status_code == 200

    def test_invalid_post_renders_response_with_errors(
        self, superuser_user_client, superuser_clinic
    ):
        response = superuser_user_client.http.post(
            reverse(
                "clinics:participant_csv_upload",
                kwargs={"pk": superuser_clinic.pk},
            )
        )
        assert response.status_code == 200

        assertInHTML(
            """
                <ul class="nhsuk-list nhsuk-error-summary__list">
                    <li><a href="#id_csv_file">Select a CSV file to upload</a></li>
                </ul>
            """,
            response.text,
        )

    def test_valid_post_redirects(self, superuser_user_client, superuser_clinic):
        lines = [
            "Row,NHS Number,Surname,Forenames,Title,Date of Birth,Age,Sex,Ethnic Origin,Address,Postcode,Telephone No.1,Tel No.2,Email Address,GP",
            '1,999 999 9991,SMITH,TEST1,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET, AREA, CITY",AA1 2XY,1034567891,1034567891,zxcv@outlook.com,BSS/B81001 - TEST GROUP PRACTICE (PRAC:B81001)',
            '2,999 999 9992,JONES,TEST2,MRS,15-Jun-1970,50,F,A White - British,"q, w, e, r, t",BB9 3ED,1034567892,,asdf@outlook.com,BSS/B81002 - TEST PARTNERSHIP (PRAC:B81002)',
            '3,999 999 9993,JOHNSON,TEST3 MIDDLENAME,MRS,31-Dec-1960,50,F,A White - British,"22 FAKE STREET, CITY",CC3 3PK,1034567893,,qwerty@gmail.com,BSS/B81003 - TEST FAMILY PRACTICE (PRAC:B81003)',
        ]

        csv_content = ("\n".join(lines)).encode("utf-8")
        uploaded_file = SimpleUploadedFile(
            "participants.csv", csv_content, content_type="text/csv"
        )
        response = superuser_user_client.http.post(
            reverse(
                "clinics:participant_csv_upload",
                kwargs={"pk": superuser_clinic.pk},
            ),
            {"csv_file": uploaded_file},
        )
        assertRedirects(
            response,
            reverse(
                "clinics:show_clinic",
                kwargs={"pk": superuser_clinic.pk},
            ),
        )
        assertMessages(
            response,
            [
                messages.Message(
                    level=messages.SUCCESS,
                    message="3 participant(s) uploaded successfully.",
                )
            ],
        )

    def _make_csv(self, lines):
        csv_content = ("\n".join(lines)).encode("utf-8")
        return SimpleUploadedFile(
            "participants.csv", csv_content, content_type="text/csv"
        )

    def _header(self):
        return "Row,NHS Number,Surname,Forenames,Title,Date of Birth,Age,Sex,Ethnic Origin,Address,Postcode,Telephone No.1,Tel No.2,Email Address,GP"

    def test_csv_row_error_missing_forenames(
        self, superuser_user_client, superuser_clinic
    ):
        lines = [
            self._header(),
            '1,,SMITH,,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET",AA1 2XY,1034567890,,test@example.com,BSS',
        ]
        response = superuser_user_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert response.status_code == 200
        assertInHTML(
            "<li>Row 1: Forenames is required</li>",
            response.text,
        )

    def test_csv_row_error_missing_surname(
        self, superuser_user_client, superuser_clinic
    ):
        lines = [
            self._header(),
            '1,999 999 9991,,TEST1,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET",AA1 2XY,1034567890,,test@example.com,BSS',
        ]
        response = superuser_user_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert response.status_code == 200
        assertInHTML("<li>Row 1: Surname is required</li>", response.text)

    def test_csv_row_error_invalid_nhs_number(
        self, superuser_user_client, superuser_clinic
    ):
        lines = [
            self._header(),
            '1,BADNHSNUM,SMITH,TEST1,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET",AA1 2XY,1034567890,,test@example.com,BSS',
        ]
        response = superuser_user_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert response.status_code == 200
        assertInHTML(
            "<li>Row 1: NHS Number must be in format nnn nnn nnnn (e.g., 123 456 7890)</li>",
            response.text,
        )

    def test_csv_row_error_invalid_date_of_birth(
        self, superuser_user_client, superuser_clinic
    ):
        lines = [
            self._header(),
            '1,999 999 9991,SMITH,TEST1,MRS,1980-01-01,50,F,A White - British,"1 BUILDING, STREET",AA1 2XY,1034567890,,test@example.com,BSS',
        ]
        response = superuser_user_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert response.status_code == 200
        assertInHTML(
            "<li>Row 1: Date of Birth must be in format DD-MMM-YYYY (e.g., 01-Jan-1980)</li>",
            response.text,
        )

    def test_csv_row_error_invalid_sex(self, superuser_user_client, superuser_clinic):
        lines = [
            self._header(),
            '1,999 999 9991,SMITH,TEST1,MRS,01-Jan-1980,50,M,A White - British,"1 BUILDING, STREET",AA1 2XY,1034567890,,test@example.com,BSS',
        ]
        response = superuser_user_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert response.status_code == 200
        assertInHTML(
            '<li>Row 1: Invalid value for "Sex": "M". Only "F" is accepted.</li>',
            response.text,
        )

    def test_csv_row_error_address_too_many_lines(
        self, superuser_user_client, superuser_clinic
    ):
        lines = [
            self._header(),
            '1,999 999 9991,SMITH,TEST1,MRS,01-Jan-1980,50,F,A White - British,"a, b, c, d, e, f",AA1 2XY,1034567890,,test@example.com,BSS',
        ]
        response = superuser_user_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert response.status_code == 200
        assertInHTML(
            "<li>Row 1: Address must have at most 5 lines</li>",
            response.text,
        )

    def test_csv_row_error_missing_address(
        self, superuser_user_client, superuser_clinic
    ):
        lines = [
            self._header(),
            "1,999 999 9991,SMITH,TEST1,MRS,01-Jan-1980,50,F,A White - British,,AA1 2XY,1034567890,,test@example.com,BSS",
        ]
        response = superuser_user_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert response.status_code == 200
        assertInHTML("<li>Row 1: Address is required</li>", response.text)

    def test_csv_row_error_missing_postcode(
        self, superuser_user_client, superuser_clinic
    ):
        lines = [
            self._header(),
            '1,999 999 9991,SMITH,TEST1,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET",,1034567890,,test@example.com,BSS',
        ]
        response = superuser_user_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert response.status_code == 200
        assertInHTML("<li>Row 1: Postcode is required</li>", response.text)

    def test_csv_row_error_missing_phone(self, superuser_user_client, superuser_clinic):
        lines = [
            self._header(),
            '1,999 999 9991,SMITH,TEST1,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET",AA1 2XY,,,test@example.com,BSS',
        ]
        response = superuser_user_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert response.status_code == 200
        assertInHTML("<li>Row 1: Telephone No.1 is required</li>", response.text)

    def test_csv_row_error_missing_email(self, superuser_user_client, superuser_clinic):
        lines = [
            self._header(),
            '1,999 999 9991,SMITH,TEST1,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET",AA1 2XY,1034567890,,,BSS',
        ]
        response = superuser_user_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert response.status_code == 200
        assertInHTML("<li>Row 1: Email Address is required</li>", response.text)

    def test_multiple_row_errors_all_shown(
        self, superuser_user_client, superuser_clinic
    ):
        lines = [
            self._header(),
            '1,BADNHS,SMITH,TEST1,MRS,BADDATE,50,M,A White - British,"1 BUILDING, STREET",AA1 2XY,1034567890,,test@example.com,BSS',
        ]
        response = superuser_user_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert response.status_code == 200
        assertInHTML(
            "<li>Row 1: NHS Number must be in format nnn nnn nnnn (e.g., 123 456 7890)</li>",
            response.text,
        )
        assertInHTML(
            "<li>Row 1: Date of Birth must be in format DD-MMM-YYYY (e.g., 01-Jan-1980)</li>",
            response.text,
        )
        assertInHTML(
            '<li>Row 1: Invalid value for "Sex": "M". Only "F" is accepted.</li>',
            response.text,
        )

    def test_errors_from_multiple_rows_all_shown(
        self, superuser_user_client, superuser_clinic
    ):
        lines = [
            self._header(),
            '1,BADNHS1,SMITH,TEST1,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET",AA1 2XY,1034567890,,test1@example.com,BSS',
            '2,BADNHS2,JONES,TEST2,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET",BB2 3XY,1034567891,,test2@example.com,BSS',
        ]
        response = superuser_user_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert response.status_code == 200
        assertInHTML(
            "<li>Row 1: NHS Number must be in format nnn nnn nnnn (e.g., 123 456 7890)</li>",
            response.text,
        )
        assertInHTML(
            "<li>Row 2: NHS Number must be in format nnn nnn nnnn (e.g., 123 456 7890)</li>",
            response.text,
        )

    def test_valid_post_creates_participants(
        self, superuser_user_client, superuser_clinic
    ):
        lines = [
            self._header(),
            '1,999 999 9991,SMITH,TEST1,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, CITY",AA1 2XY,1034567890,,test1@example.com,BSS/B81001',
            '2,999 999 9992,JONES,TEST2,MRS,31-Dec-1975,50,F,A White - British,"2 BUILDING, STREET, CITY, COUNTY, UK",BB2 3XY,1034567891,,test2@example.com,BSS/B81002',
        ]
        superuser_user_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )

        assert Participant.objects.count() == 2
        assert ClinicSlot.objects.filter(clinic=superuser_clinic).count() == 2
        assert Appointment.objects.count() == 2

        participant = Participant.objects.get(nhs_number="9999999991")
        assert participant.first_name == "TEST1"
        assert participant.last_name == "SMITH"
        assert participant.gender == "Female"
        assert participant.nhs_number == "9999999991"
        assert participant.phone == "1034567890"
        assert participant.email == "test1@example.com"
        assert participant.date_of_birth.strftime("%Y-%m-%d") == "1980-01-01"
        assert participant.risk_level == "Routine"
        assert participant.address.lines == ["1 BUILDING", "CITY"]
        assert participant.address.postcode == "AA1 2XY"

        assert participant.appointments.count() == 1
        appointment = participant.appointments.first()
        assert appointment.clinic_slot.clinic == superuser_clinic
        assert appointment.clinic_slot.starts_at == superuser_clinic.starts_at
        assert appointment.clinic_slot.duration_in_minutes == 15
        assert appointment.current_status.name == AppointmentStatusNames.SCHEDULED

        participant = Participant.objects.get(nhs_number="9999999992")
        assert participant.first_name == "TEST2"
        assert participant.last_name == "JONES"
        assert participant.gender == "Female"
        assert participant.nhs_number == "9999999992"
        assert participant.phone == "1034567891"
        assert participant.email == "test2@example.com"
        assert participant.date_of_birth.strftime("%Y-%m-%d") == "1975-12-31"
        assert participant.risk_level == "Routine"
        assert participant.address.lines == [
            "2 BUILDING",
            "STREET",
            "CITY",
            "COUNTY",
            "UK",
        ]
        assert participant.address.postcode == "BB2 3XY"

        assert participant.appointments.count() == 1
        appointment = participant.appointments.first()
        assert appointment.clinic_slot.clinic == superuser_clinic
        assert (
            appointment.clinic_slot.starts_at
            == superuser_clinic.starts_at + timedelta(minutes=15)
        )
        assert appointment.clinic_slot.duration_in_minutes == 15
        assert appointment.current_status.name == AppointmentStatusNames.SCHEDULED

    def test_valid_post_no_db_changes_when_row_has_errors(
        self, superuser_user_client, superuser_clinic
    ):
        lines = [
            self._header(),
            '1,999 999 9991,SMITH,TEST1,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET, CITY",AA1 2XY,1034567890,,test1@example.com,BSS/B81001',
            '2,BADNHS,JONES,TEST2,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET",BB2 3XY,1034567891,,test2@example.com,BSS',
        ]
        superuser_user_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert Participant.objects.count() == 0
        assert ClinicSlot.objects.filter(clinic=superuser_clinic).count() == 0
        assert Appointment.objects.count() == 0
