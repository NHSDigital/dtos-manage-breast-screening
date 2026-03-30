from django.db import models
from django.db.models import TextChoices

from manage_breast_screening.participants.models.appointment import Appointment
from manage_breast_screening.users.models import User

from ...core.models import BaseModel


class SupportReasons(TextChoices):
    BREAST_IMPLANTS = ("BREAST_IMPLANTS", "Breast implants")
    MEDICAL_DEVICES = ("MEDICAL_DEVICES", "Implanted medical devices")
    VISION = ("VISION", "Vision")
    HEARING = ("HEARING", "Hearing")
    PHYSICAL_RESTRICTION = ("PHYSICAL_RESTRICTION", "Physical restriction")
    SOCIAL_EMOTIONAL_MENTAL_HEALTH = (
        "SOCIAL_EMOTIONAL_MENTAL_HEALTH",
        "Social, emotional, and mental health",
    )
    LANGUAGE = ("LANGUAGE", "Language")
    GENDER_IDENTITY = ("GENDER_IDENTITY", "Gender identity")
    OTHER = ("OTHER", "Other")


class ParticipantReportedMammogram(BaseModel):
    class LocationType(models.TextChoices):
        SAME_PROVIDER = (
            "SAME_PROVIDER",
            "At this NHS breast screening unit",
        )
        ANOTHER_NHS_PROVIDER = (
            "ANOTHER_NHS_PROVIDER",
            "At another NHS breast screening unit",
        )
        ELSEWHERE_UK = "ELSEWHERE_UK", "Elsewhere in the UK"
        OUTSIDE_UK = "OUTSIDE_UK", "Outside the UK"
        PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY", "Prefer not to say"

    class DateType(TextChoices):
        EXACT = (
            "EXACT",
            "Enter an exact date",
        )
        MORE_THAN_SIX_MONTHS = (
            "MORE_THAN_SIX_MONTHS",
            "Not sure (at least 6 months ago)",
        )
        LESS_THAN_SIX_MONTHS = (
            "LESS_THAN_SIX_MONTHS",
            "Not sure (less than 6 months ago)",
        )

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.PROTECT,
        related_name="reported_mammograms",
    )
    location_type = models.CharField(choices=LocationType)
    location_details = models.TextField(null=False, default="", blank=True)
    date_type = models.CharField(choices=DateType)
    exact_date = models.DateField(null=True, blank=True)
    approx_date = models.CharField(null=False, default="", blank=True)
    different_name = models.CharField(null=False, default="", blank=True)
    additional_information = models.TextField(null=False, default="", blank=True)
    reason_for_continuing = models.TextField(null=False, default="", blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, null=False)
