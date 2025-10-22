from django.db import models
from django.db.models import TextChoices

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
        NHS_BREAST_SCREENING_UNIT = (
            "NHS_BREAST_SCREENING_UNIT",
            "At an NHS breast screening unit",
        )
        ELSEWHERE_UK = "ELSEWHERE_UK", "Elsewhere in the UK"
        OUTSIDE_UK = "OUTSIDE_UK", "Outside the UK"
        PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY", "Prefer not to say"

    participant = models.ForeignKey(
        "participants.Participant",
        on_delete=models.PROTECT,
        related_name="reported_mammograms",
    )
    location_type = models.CharField(choices=LocationType)
    provider = models.ForeignKey(
        "clinics.Provider", on_delete=models.PROTECT, null=True, blank=True
    )
    location_details = models.TextField(null=False, default="", blank=True)
    exact_date = models.DateField(null=True, blank=True)
    approx_date = models.CharField(null=False, default="", blank=True)
    different_name = models.CharField(null=False, default="", blank=True)
    additional_information = models.TextField(null=False, default="", blank=True)
