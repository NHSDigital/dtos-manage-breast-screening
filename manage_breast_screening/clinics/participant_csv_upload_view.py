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

    template_name = "clinics/participant_csv_upload.jinja"
    form_class = ParticipantCsvUploadForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transformer = ParticipantCsvTransformService()

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

        transformed_rows, csv_errors = self.transformer.transform_csv(decoded_file)

        if csv_errors:
            for error in csv_errors:
                form.add_error(None, error)
            return self.form_invalid(form)

        ParticipantCsvInsertService(self.clinic, self.request.user).insert_data(
            transformed_rows
        )

        messages.success(
            self.request,
            f"{len(transformed_rows)} participants uploaded successfully.",
        )
        return redirect("clinics:show_clinic", pk=self.clinic.pk)


class ParticipantCsvTransformService:
    def __init__(self, *args, **kwargs):
        self.field_validators = [
            ("first_name", "Forenames", self.validate_required),
            ("last_name", "Surname", self.validate_required),
            ("gender", "Sex", self.validate_gender),
            ("nhs_number", "NHS Number", self.validate_nhs_number),
            ("phone", "Telephone No.1", self.validate_required),
            ("email", "Email Address", self.validate_required),
            ("date_of_birth", "Date of Birth", self.validate_date_of_birth),
            ("address_lines", "Address", self.validate_address),
            ("postcode", "Postcode", self.validate_required),
            ("start_time", "Start Time", self.validate_start_time),
        ]
        self.required_headings = [
            csv_column_name for _, csv_column_name, _ in self.field_validators
        ]

    def transform_csv(self, decoded_file):
        reader = csv.DictReader(io.StringIO(decoded_file))

        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            duplicates = {
                x for x in reader.fieldnames if reader.fieldnames.count(x) > 1
            }
            return None, [f"Duplicate columns found: {', '.join(duplicates)}"]

        column_errors = [
            f"Missing column: {heading}"
            for heading in self.required_headings
            if heading not in reader.fieldnames
        ]
        if column_errors:
            return None, column_errors

        return self.transform_rows(reader)

    def transform_rows(self, reader: csv.DictReader) -> tuple[list[dict], list[str]]:
        """
        Transforms CSV rows into the format needed to insert into the database, while collecting any validation errors.

        Returns a tuple containing a list of transformed rows and a list of error messages.

        Rows with errors are excluded from the list of transformed rows.
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

        # If a row does not have enough columns, DictReader fills missing fields with None
        none_keys = [k for k, v in row.items() if v is None]
        if none_keys:
            return (None, [f"Missing columns: {', '.join(none_keys)}"])

        # Strip whitespace from all values
        row = {k: v.strip() for k, v in row.items()}

        errors = []
        output = {}

        for database_column_name, csv_column_name, validator in self.field_validators:
            value, field_error = validator(row, csv_column_name)
            if field_error:
                errors.append(field_error)
            output[database_column_name] = value

        if errors:
            return None, errors
        return output, []

    def validate_required(self, row, key):
        value = row.get(key)
        if not value:
            return None, f"{key} is required"
        return value, None

    def validate_gender(self, row, key):
        value = row.get(key)
        if value != "F":
            return None, f'Invalid value for "{key}": "{value}". Only "F" is accepted.'
        return "Female", None

    def validate_nhs_number(self, row, key):
        nhs_number = row.get(key).replace(" ", "")
        if not self.is_valid_nhs_number(nhs_number):
            return (
                None,
                "NHS Number must be 10 digits (spaces are ignored, e.g., 1234567890 or 123 456 7890)",
            )
        if Participant.objects.filter(nhs_number=nhs_number).exists():
            return None, "NHS Number already exists in the database"
        return nhs_number, None

    def is_valid_nhs_number(self, nhs_number):
        return nhs_number.isdigit() and len(nhs_number) == 10

    def validate_date_of_birth(self, row, key):
        try:
            return datetime.strptime(row.get(key), "%d-%b-%Y").date(), None
        except (ValueError, TypeError):
            return (
                None,
                "Date of Birth must be in format DD-MMM-YYYY (e.g., 01-Jan-1980)",
            )

    def validate_address(self, row, key):
        address_lines = [
            line.strip() for line in row.get(key).split(",") if line.strip()
        ]
        if len(address_lines) == 0:
            return None, "Address is required"
        if len(address_lines) > 5:
            return None, "Address must have at most 5 lines"
        return address_lines, None

    def validate_start_time(self, row, key):
        try:
            return datetime.strptime(row.get(key), "%H:%M").time(), None
        except ValueError:
            return None, "Start Time must be in format HH:MM (e.g., 09:30 or 14:45)"


class ParticipantCsvInsertService:
    SLOT_DURATION_IN_MINUTES = 15

    def __init__(self, clinic, user):
        self.clinic = clinic
        self.user = user
        self.auditor = Auditor(user)

    def insert_data(self, transformed_rows):
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
                self.save_and_audit(participant)

                participant_address = ParticipantAddress(
                    participant=participant,
                    lines=row["address_lines"],
                    postcode=row["postcode"],
                )
                self.save_and_audit(participant_address)

                clinic_slot = ClinicSlot(
                    clinic=self.clinic,
                    starts_at=timezone.make_aware(
                        datetime.combine(clinic_date, row["start_time"])
                    ),
                    duration_in_minutes=self.SLOT_DURATION_IN_MINUTES,
                )
                self.save_and_audit(clinic_slot)

                screening_episode = ScreeningEpisode(
                    participant=participant,
                )
                self.save_and_audit(screening_episode)

                appointment = Appointment(
                    screening_episode=screening_episode,
                    clinic_slot=clinic_slot,
                )
                self.save_and_audit(appointment)

                appointment_status = AppointmentStatus(
                    appointment=appointment,
                    name=AppointmentStatusNames.SCHEDULED,
                    created_by=self.user,
                )
                self.save_and_audit(appointment_status)

    def save_and_audit(self, obj):
        obj.save()
        self.auditor.audit_create(obj)
