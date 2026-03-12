import uuid
from datetime import time

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
from manage_breast_screening.core.models import AuditLog
from manage_breast_screening.participants.models import Appointment
from manage_breast_screening.participants.models.appointment import (
    AppointmentStatusNames,
)
from manage_breast_screening.participants.tests.factories import ParticipantFactory


@pytest.mark.django_db
class TestParticipantCsvUploadView:
    @pytest.fixture
    def superuser_clinic(self, superuser_client):
        setting = SettingFactory.create(provider=superuser_client.current_provider)
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

    def test_404_when_clinic_not_found(self, superuser_client, superuser_clinic):
        unknown_clinic_pk = uuid.uuid4()
        response = superuser_client.http.get(
            reverse(
                "clinics:participant_csv_upload",
                kwargs={"pk": unknown_clinic_pk},
            )
        )
        assert response.status_code == 404

    def test_renders_response(self, superuser_client, superuser_clinic):
        response = superuser_client.http.get(
            reverse(
                "clinics:participant_csv_upload",
                kwargs={"pk": superuser_clinic.pk},
            )
        )
        assert response.status_code == 200

    def test_missing_data_produces_validation_error(
        self, superuser_client, superuser_clinic
    ):
        response = superuser_client.http.post(
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

    def test_non_utf8_file_produces_validation_error(
        self, superuser_client, superuser_clinic
    ):
        # Encode content as Windows-1252, which is not valid UTF-8 when it
        # contains characters outside the ASCII range
        non_utf8_content = "Forenames,Surname\nJo\xe9,Smith\n".encode("windows-1252")
        csv_file = SimpleUploadedFile(
            "participants.csv", non_utf8_content, content_type="text/csv"
        )

        response = superuser_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": csv_file},
        )

        assert response.status_code == 200

        assertInHTML(
            """
                <ul class="nhsuk-list nhsuk-error-summary__list">
                    <li><a href="#id_csv_file">The file could not be read as UTF-8</a></li>
                </ul>
            """,
            response.text,
        )

    def test_valid_post_redirects(self, superuser_client, superuser_clinic):
        lines = [
            "Row,NHS Number,Surname,Forenames,Title,Date of Birth,Age,Sex,Ethnic Origin,Address,Postcode,Telephone No.1,Tel No.2,Email Address,GP,Start Time",
            '1,999 999 9991,SMITH,TEST1,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET, AREA, CITY",AA1 2XY,1034567891,1034567891,zxcv@outlook.com,BSS/B81001 - TEST GROUP PRACTICE (PRAC:B81001),09:00',
            '2,999 999 9992,JONES,TEST2,MRS,15-Jun-1970,50,F,A White - British,"q, w, e, r, t",BB9 3ED,1034567892,,asdf@outlook.com,BSS/B81002 - TEST PARTNERSHIP (PRAC:B81002),10:00',
            '3,999 999 9993,JOHNSON,TEST3 MIDDLENAME,MRS,31-Dec-1960,50,F,A White - British,"22 FAKE STREET, CITY",CC3 3PK,1034567893,,qwerty@gmail.com,BSS/B81003 - TEST FAMILY PRACTICE (PRAC:B81003),11:00',
        ]

        csv_content = ("\n".join(lines)).encode("utf-8")
        uploaded_file = SimpleUploadedFile(
            "participants.csv", csv_content, content_type="text/csv"
        )
        response = superuser_client.http.post(
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
                    message="3 participants uploaded successfully.",
                )
            ],
        )

    def _make_csv(self, lines):
        csv_content = ("\n".join(lines)).encode("utf-8")
        return SimpleUploadedFile(
            "participants.csv", csv_content, content_type="text/csv"
        )

    def _header(self):
        return "Row,NHS Number,Surname,Forenames,Title,Date of Birth,Age,Sex,Ethnic Origin,Address,Postcode,Telephone No.1,Tel No.2,Email Address,GP,Start Time"

    def test_missing_headings(self, superuser_client, superuser_clinic):
        lines = [
            "a,b,c",
            "1,2,3",
        ]
        response = superuser_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert response.status_code == 200
        assertInHTML("<li>Missing column: NHS Number</li>", response.text)
        assertInHTML("<li>Missing column: Surname</li>", response.text)
        assertInHTML("<li>Missing column: Forenames</li>", response.text)
        assertInHTML("<li>Missing column: Date of Birth</li>", response.text)
        assertInHTML("<li>Missing column: Sex</li>", response.text)
        assertInHTML("<li>Missing column: Address</li>", response.text)
        assertInHTML("<li>Missing column: Postcode</li>", response.text)
        assertInHTML("<li>Missing column: Telephone No.1</li>", response.text)
        assertInHTML("<li>Missing column: Email Address</li>", response.text)
        assertInHTML("<li>Missing column: Start Time</li>", response.text)

    def test_rows_missing_columns(self, superuser_client, superuser_clinic):
        lines = [
            self._header(),
            '1,,SMITH,,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET",AA1 2XY,1034567890,,test@example.com,BSS',
            "2,",
            '3,,SMITH,,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET",',
        ]
        response = superuser_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert response.status_code == 200
        assertInHTML("<li>Row 1: Missing columns: Start Time</li>", response.text)
        assertInHTML(
            "<li>Row 2: Missing columns: Surname, Forenames, Title, Date of Birth, Age, Sex, Ethnic Origin, Address, Postcode, Telephone No.1, Tel No.2, Email Address, GP, Start Time</li>",
            response.text,
        )
        assertInHTML(
            "<li>Row 3: Missing columns: Telephone No.1, Tel No.2, Email Address, GP, Start Time</li>",
            response.text,
        )

    def test_csv_row_error_missing_forenames(self, superuser_client, superuser_clinic):
        lines = [
            self._header(),
            '1,,SMITH,,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET",AA1 2XY,1034567890,,test@example.com,BSS,9:00',
        ]
        response = superuser_client.http.post(
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

    def test_csv_row_error_missing_surname(self, superuser_client, superuser_clinic):
        lines = [
            self._header(),
            '1,999 999 9991,,TEST1,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET",AA1 2XY,1034567890,,test@example.com,BSS,9:00',
        ]
        response = superuser_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert response.status_code == 200
        assertInHTML("<li>Row 1: Surname is required</li>", response.text)

    @pytest.mark.parametrize(
        "nhs_number",
        [
            "BADNHS1",
            "xxxxxxxxxx",
            "123456789",
            "123 456 789",
            "12345678901",
            "123 4567 8901",
            "123-456-7890",
            "123_456_7890",
            "-1234567890",
            "-123456789",
            "12345678.90",
            "12345678.9",
            "1234S67890",
        ],
    )
    def test_csv_row_error_invalid_nhs_number(
        self, superuser_client, superuser_clinic, nhs_number
    ):
        lines = [
            self._header(),
            f'1,{nhs_number},SMITH,TEST1,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET",AA1 2XY,1034567890,,test@example.com,BSS,9:00',
        ]
        response = superuser_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert response.status_code == 200
        assertInHTML(
            "<li>Row 1: NHS Number must be 10 digits (spaces are ignored, e.g., 1234567890 or 123 456 7890)</li>",
            response.text,
        )

    def test_csv_row_error_duplicate_nhs_number(
        self, superuser_client, superuser_clinic
    ):
        # Create a participant with the same NHS number as in the CSV. This should trigger the duplicate NHS number validation error
        ParticipantFactory.create(nhs_number="9999999991")

        lines = [
            self._header(),
            '1,999 999 9991,SMITH,TEST1,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET",AA1 2XY,1034567890,,test@example.com,BSS,9:00',
        ]
        response = superuser_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert response.status_code == 200
        assertInHTML(
            "<li>Row 1: NHS Number already exists in the database</li>",
            response.text,
        )

    def test_csv_row_error_invalid_date_of_birth(
        self, superuser_client, superuser_clinic
    ):
        lines = [
            self._header(),
            '1,999 999 9991,SMITH,TEST1,MRS,1980-01-01,50,F,A White - British,"1 BUILDING, STREET",AA1 2XY,1034567890,,test@example.com,BSS,9:00',
        ]
        response = superuser_client.http.post(
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

    def test_csv_row_error_invalid_sex(self, superuser_client, superuser_clinic):
        lines = [
            self._header(),
            '1,999 999 9991,SMITH,TEST1,MRS,01-Jan-1980,50,M,A White - British,"1 BUILDING, STREET",AA1 2XY,1034567890,,test@example.com,BSS,9:00',
        ]
        response = superuser_client.http.post(
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
        self, superuser_client, superuser_clinic
    ):
        lines = [
            self._header(),
            '1,999 999 9991,SMITH,TEST1,MRS,01-Jan-1980,50,F,A White - British,"a, b, c, d, e, f",AA1 2XY,1034567890,,test@example.com,BSS,9:00',
        ]
        response = superuser_client.http.post(
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

    def test_csv_row_error_missing_address(self, superuser_client, superuser_clinic):
        lines = [
            self._header(),
            "1,999 999 9991,SMITH,TEST1,MRS,01-Jan-1980,50,F,A White - British,,AA1 2XY,1034567890,,test@example.com,BSS,9:00",
        ]
        response = superuser_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert response.status_code == 200
        assertInHTML("<li>Row 1: Address is required</li>", response.text)

    def test_multiple_row_errors_all_shown(self, superuser_client, superuser_clinic):
        lines = [
            self._header(),
            '1,BADNHS,SMITH,TEST1,MRS,BADDATE,50,M,A White - British,"1 BUILDING, STREET",AA1 2XY,1034567890,,test@example.com,BSS,9:00',
        ]
        response = superuser_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert response.status_code == 200
        assertInHTML(
            "<li>Row 1: NHS Number must be 10 digits (spaces are ignored, e.g., 1234567890 or 123 456 7890)</li>",
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
        self, superuser_client, superuser_clinic
    ):
        lines = [
            self._header(),
            '1,BADNHS1,SMITH,TEST1,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET",AA1 2XY,1034567890,,test1@example.com,BSS,9:00',
            '2,BADNHS2,JONES,TEST2,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET",BB2 3XY,1034567891,,test2@example.com,BSS,9:00',
        ]
        response = superuser_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert response.status_code == 200
        assertInHTML(
            "<li>Row 1: NHS Number must be 10 digits (spaces are ignored, e.g., 1234567890 or 123 456 7890)</li>",
            response.text,
        )
        assertInHTML(
            "<li>Row 2: NHS Number must be 10 digits (spaces are ignored, e.g., 1234567890 or 123 456 7890)</li>",
            response.text,
        )

    def test_valid_post_creates_participants(self, superuser_client, superuser_clinic):
        """
        Test valid CSV creates records with correct data, and that audit logs are created for all changes.

        Creates on participant with all fields populated, and another participant with only required fields populated.
        """

        lines = [
            self._header(),
            '1,999 999 9991,SMITH,TEST1,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET, CITY, COUNTY, UK",AA1 2XY,1034567890,,test1@example.com,BSS/B81001,09:07',
            '2,9999999992,JONES,TEST2,,31-Dec-1975,,F,,"2 BUILDING",,,,,,15:34',
        ]
        superuser_client.http.post(
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
        assert participant.address.lines == [
            "1 BUILDING",
            "STREET",
            "CITY",
            "COUNTY",
            "UK",
        ]
        assert participant.address.postcode == "AA1 2XY"

        assert participant.appointments.count() == 1
        appointment = participant.appointments.first()
        assert appointment.clinic_slot.clinic == superuser_clinic
        assert (
            appointment.clinic_slot.starts_at.date()
            == superuser_clinic.starts_at.date()
        )
        assert appointment.clinic_slot.starts_at.time() == time(9, 7)
        assert appointment.clinic_slot.duration_in_minutes == 15
        assert appointment.current_status.name == AppointmentStatusNames.SCHEDULED

        participant = Participant.objects.get(nhs_number="9999999992")
        assert participant.first_name == "TEST2"
        assert participant.last_name == "JONES"
        assert participant.gender == "Female"
        assert participant.nhs_number == "9999999992"
        assert participant.phone == ""
        assert participant.email == ""
        assert participant.date_of_birth.strftime("%Y-%m-%d") == "1975-12-31"
        assert participant.risk_level == "Routine"
        assert participant.address.lines == ["2 BUILDING"]
        assert participant.address.postcode == ""

        assert participant.appointments.count() == 1
        appointment = participant.appointments.first()
        assert appointment.clinic_slot.clinic == superuser_clinic
        assert (
            appointment.clinic_slot.starts_at.date()
            == superuser_clinic.starts_at.date()
        )
        assert appointment.clinic_slot.starts_at.time() == time(15, 34)
        assert appointment.clinic_slot.duration_in_minutes == 15
        assert appointment.current_status.name == AppointmentStatusNames.SCHEDULED

        # Expect 12 audit logs: 2 participants + 2 addresses + 2 clinic slots + 2 screening episodes + 2 appointments + 2 appointment statuses
        assert AuditLog.objects.count() == 12

    def test_valid_post_no_db_changes_when_row_has_errors(
        self, superuser_client, superuser_clinic
    ):
        lines = [
            self._header(),
            '1,999 999 9991,SMITH,TEST1,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET, CITY",AA1 2XY,1034567890,,test1@example.com,BSS/B81001,9:00',
            '2,BADNHS,JONES,TEST2,MRS,01-Jan-1980,50,F,A White - British,"1 BUILDING, STREET",BB2 3XY,1034567891,,test2@example.com,BSS,9:00',
        ]
        superuser_client.http.post(
            reverse(
                "clinics:participant_csv_upload", kwargs={"pk": superuser_clinic.pk}
            ),
            {"csv_file": self._make_csv(lines)},
        )
        assert Participant.objects.count() == 0
        assert ClinicSlot.objects.filter(clinic=superuser_clinic).count() == 0
        assert Appointment.objects.count() == 0
        assert AuditLog.objects.count() == 0
