import csv
import io
from datetime import datetime
from functools import cached_property

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic.edit import FormView

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.participants.models import (
    ParticipantAddress,
)
from manage_breast_screening.participants.models.appointment import (
    AppointmentStatus,
    AppointmentStatusNames,
)
from manage_breast_screening.participants.models.screening_episode import (
    ScreeningEpisode,
)

from ..participants.models import Appointment
from .models import Clinic, ClinicSlot, Participant
from .participant_csv_upload_form import ParticipantCsvUploadForm
from .presenters import ClinicPresenter


class ParticipantCsvUploadView(LoginRequiredMixin, FormView):
    """
    Allows superusers to upload a CSV file containing participant data to bulk create participants and appointments for a clinic.

    The clinic must already exist before uploading the CSV. You can create a clinic using the Django admin interface.
    """

    SLOT_DURATION_IN_MINUTES = 15
    REQUIRED_HEADINGS = [
        "NHS Number",
        "Surname",
        "Forenames",
        "Date of Birth",
        "Sex",
        "Address",
        "Postcode",
        "Telephone No.1",
        "Email Address",
        "Start Time",
    ]

    template_name = "clinics/participant_csv_upload.jinja"
    form_class = ParticipantCsvUploadForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied("You must be a superuser to access this page.")
        return super().dispatch(request, *args, **kwargs)

    @cached_property
    def clinic(self):
        try:
            provider = self.request.user.current_provider
            return provider.clinics.get(pk=self.kwargs["pk"])
        except Clinic.DoesNotExist:
            raise Http404("Clinic not found")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clinic"] = self.clinic
        context["presented_clinic"] = ClinicPresenter(self.clinic)
        return context

    def form_valid(self, form):
        try:
            decoded_file = form.cleaned_data["csv_file"].read().decode("utf-8")
        except UnicodeDecodeError:
            form.add_error("csv_file", "The file could not be read as UTF-8")
            return self.form_invalid(form)

        transformed_rows, csv_errors = self.parse_csv(decoded_file)

        if csv_errors:
            for error in csv_errors:
                form.add_error(None, error)
            return self.form_invalid(form)

        self.insert_data(transformed_rows)

        messages.success(
            self.request,
            f"{len(transformed_rows)} participants uploaded successfully.",
        )
        return redirect("clinics:show_clinic", pk=self.clinic.pk)

    def parse_csv(self, decoded_file):
        reader = csv.DictReader(io.StringIO(decoded_file))

        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            duplicates = set(
                [x for x in reader.fieldnames if reader.fieldnames.count(x) > 1]
            )
            return (None, [f"Duplicate columns found: {', '.join(duplicates)}"])

        column_errors = [
            f"Missing column: {heading}"
            for heading in self.REQUIRED_HEADINGS
            if heading not in reader.fieldnames
        ]
        if column_errors:
            return (None, column_errors)

        return self.transform_rows(reader)

    def transform_rows(self, reader: csv.DictReader) -> tuple[list[dict], list[str]]:
        """
        Transforms CSV rows into the format needed to insert into the database, while collecting any validation errors.

        Returns a tuple containing a list of transformed rows and a list of error messages.
        """

        rows = []
        errors = []
        for i, row in enumerate(reader, start=1):
            transformed_row, row_errors = self.transform_row(row)
            if row_errors:
                errors.extend([f"Row {i}: {e}" for e in row_errors])
            else:
                rows.append(transformed_row)
        return rows, errors

    def transform_row(self, row: dict) -> tuple[dict | None, list[str]]:
        """
        Transforms a single CSV row into the format needed to insert into the database, while collecting any validation errors.

        Returns a tuple of (transformed_row, errors) where transformed_row is a dict containing the transformed data if the row is valid,
        or None if there are validation errors.
        The errors element is a list of error messages describing any validation issues with the row.
        """

        none_keys = [k for k, v in row.items() if v is None]
        if none_keys:
            return (None, [f"Missing columns: {', '.join(none_keys)}"])

        errors = []
        output = {}

        first_name = self.get_stripped_value(row, "Forenames")
        if not first_name:
            errors.append("Forenames is required")
        output["first_name"] = first_name

        last_name = self.get_stripped_value(row, "Surname")
        if not last_name:
            errors.append("Surname is required")
        output["last_name"] = last_name

        gender = self.get_stripped_value(row, "Sex")
        if gender != "F":
            errors.append(f'Invalid value for "Sex": "{gender}". Only "F" is accepted.')
        output["gender"] = "Female"

        nhs_number = self.get_stripped_value(row, "NHS Number").replace(" ", "")
        if not self.is_valid_nhs_number(nhs_number):
            errors.append(
                "NHS Number must be 10 digits (spaces are ignored, e.g., 1234567890 or 123 456 7890)"
            )
        if Participant.objects.filter(nhs_number=nhs_number).exists():
            errors.append("NHS Number already exists in the database")
        output["nhs_number"] = nhs_number

        phone = self.get_stripped_value(row, "Telephone No.1")
        if not phone:
            errors.append("Telephone No.1 is required")
        output["phone"] = phone

        email = self.get_stripped_value(row, "Email Address")
        if not email:
            errors.append("Email Address is required")
        output["email"] = email

        date_of_birth = self.get_stripped_value(row, "Date of Birth")
        try:
            output["date_of_birth"] = datetime.strptime(
                date_of_birth, "%d-%b-%Y"
            ).date()
        except (ValueError, TypeError):
            errors.append(
                "Date of Birth must be in format DD-MMM-YYYY (e.g., 01-Jan-1980)"
            )

        address = self.get_stripped_value(row, "Address")
        address_lines = [line.strip() for line in address.split(",") if line.strip()]
        if len(address_lines) == 0:
            errors.append("Address is required")
        if len(address_lines) > 5:
            errors.append("Address must have at most 5 lines")
        output["address_lines"] = address_lines

        postcode = self.get_stripped_value(row, "Postcode")
        if not postcode:
            errors.append("Postcode is required")
        output["postcode"] = postcode

        start_time = self.get_stripped_value(row, "Start Time")
        try:
            output["start_time"] = datetime.strptime(start_time, "%H:%M").time()
        except ValueError:
            errors.append("Start Time must be in format HH:MM (e.g., 09:30 or 14:45)")

        if errors:
            return None, errors

        return output, []

    def insert_data(self, transformed_rows):
        auditor = Auditor.from_request(self.request)
        clinic_date = self.clinic.starts_at.date()

        with transaction.atomic():
            for row in transformed_rows:
                participant = Participant(
                    first_name=row["first_name"],
                    last_name=row["last_name"],
                    gender=row["gender"],
                    nhs_number=row["nhs_number"],
                    phone=row["phone"],
                    email=row["email"],
                    date_of_birth=row["date_of_birth"],
                    risk_level="Routine",
                )
                self.save(auditor, participant)

                participant_address = ParticipantAddress(
                    participant=participant,
                    lines=row["address_lines"],
                    postcode=row["postcode"],
                )
                self.save(auditor, participant_address)

                clinic_slot = ClinicSlot(
                    clinic=self.clinic,
                    starts_at=timezone.make_aware(
                        datetime.combine(clinic_date, row["start_time"])
                    ),
                    duration_in_minutes=self.SLOT_DURATION_IN_MINUTES,
                )
                self.save(auditor, clinic_slot)

                screening_episode = ScreeningEpisode(
                    participant=participant,
                )
                self.save(auditor, screening_episode)

                appointment = Appointment(
                    screening_episode=screening_episode,
                    clinic_slot=clinic_slot,
                )
                self.save(auditor, appointment)

                appointment_status = AppointmentStatus(
                    appointment=appointment,
                    name=AppointmentStatusNames.SCHEDULED,
                    created_by=self.request.user,
                )
                self.save(auditor, appointment_status)

    def get_stripped_value(self, row, key):
        value = row.get(key)
        return value.strip() if value else ""

    def is_valid_nhs_number(self, nhs_number):
        return nhs_number.isdigit() and len(nhs_number) == 10

    def save(self, auditor, obj):
        obj.save()
        auditor.audit_create(obj)
