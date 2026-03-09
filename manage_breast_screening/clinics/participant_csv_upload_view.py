import csv
import io
from datetime import datetime, timedelta
from functools import cached_property

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic.edit import FormView

from manage_breast_screening.participants.models import ParticipantAddress
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

        reader = csv.DictReader(io.StringIO(decoded_file))

        transformed_rows, row_errors = self.transform_rows(reader)

        if row_errors:
            for error in row_errors:
                form.add_error(None, error)
            return self.form_invalid(form)

        self.insert_data(transformed_rows)

        messages.success(
            self.request,
            f"{len(transformed_rows)} participants uploaded successfully.",
        )
        return redirect("clinics:show_clinic", pk=self.clinic.pk)

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

        errors = []
        output = {}

        first_name = row.get("Forenames", "").strip()
        if not first_name:
            errors.append("Forenames is required")
        output["first_name"] = first_name

        last_name = row.get("Surname", "").strip()
        if not last_name:
            errors.append("Surname is required")
        output["last_name"] = last_name

        gender = row.get("Sex", "").strip()
        if gender != "F":
            errors.append(f'Invalid value for "Sex": "{gender}". Only "F" is accepted.')
        output["gender"] = "Female"

        nhs_number = row.get("NHS Number", "").replace(" ", "")
        if not nhs_number.isdigit() or len(nhs_number) != 10:
            errors.append(
                "NHS Number must be 10 digits (spaces are ignored, e.g., 1234567890 or 123 456 7890)"
            )
        if Participant.objects.filter(nhs_number=nhs_number).exists():
            errors.append("NHS Number already exists in the database")
        output["nhs_number"] = nhs_number

        phone = row.get("Telephone No.1", "").strip()
        if not phone:
            errors.append("Telephone No.1 is required")
        output["phone"] = phone

        email = row.get("Email Address", "").strip()
        if not email:
            errors.append("Email Address is required")
        output["email"] = email

        date_of_birth = row.get("Date of Birth", "").strip()
        try:
            output["date_of_birth"] = datetime.strptime(
                date_of_birth, "%d-%b-%Y"
            ).date()
        except (ValueError, TypeError):
            errors.append(
                "Date of Birth must be in format DD-MMM-YYYY (e.g., 01-Jan-1980)"
            )

        address = row.get("Address", "").strip()
        address_lines = [line.strip() for line in address.split(",") if line.strip()]
        if len(address_lines) == 0:
            errors.append("Address is required")
        if len(address_lines) > 5:
            errors.append("Address must have at most 5 lines")
        output["address_lines"] = address_lines

        postcode = row.get("Postcode", "").strip()
        if not postcode:
            errors.append("Postcode is required")
        output["postcode"] = postcode

        if errors:
            return None, errors

        return output, []

    def insert_data(self, transformed_rows):
        slot_start_time = self.clinic.starts_at

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
                participant.save()

                ParticipantAddress(
                    participant=participant,
                    lines=row["address_lines"],
                    postcode=row["postcode"],
                ).save()

                clinic_slot = ClinicSlot(
                    clinic=self.clinic,
                    starts_at=slot_start_time,
                    duration_in_minutes=self.SLOT_DURATION_IN_MINUTES,
                )
                clinic_slot.save()
                slot_start_time += timedelta(minutes=self.SLOT_DURATION_IN_MINUTES)

                screening_episode = ScreeningEpisode(
                    participant=participant,
                )
                screening_episode.save()

                appointment = Appointment(
                    screening_episode=screening_episode,
                    clinic_slot=clinic_slot,
                )
                appointment.save()

                AppointmentStatus(
                    appointment=appointment,
                    name=AppointmentStatusNames.SCHEDULED,
                    created_by=self.request.user,
                ).save()
