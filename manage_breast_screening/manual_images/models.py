from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from manage_breast_screening.core.models import BaseModel


class Study(BaseModel):
    appointment = models.ForeignKey(
        "participants.Appointment", on_delete=models.PROTECT
    )

    additional_details = models.TextField(blank=True, null=False, default="")


class RepeatReason(models.TextChoices):
    PATIENT_MOVED = "PATIENT_MOVED", "Patient moved during exposure"
    UNABLE_COMPRESSION = "UNABLE_COMPRESSION", "Unable to maintain compression"
    INADEQUATE_COMPRESSION = (
        "INADEQUATE_COMPRESSION",
        "Inadequate compression achieved",
    )
    INCORRECT_POSITIONING = (
        "INCORRECT_POSITIONING",
        "Incorrect positioning identified",
    )
    IMAGE_TOO_LIGHT = "IMAGE_TOO_LIGHT", "Image too light - exposure needs adjustment"
    IMAGE_TOO_DARK = "IMAGE_TOO_DARK", "Image too dark - exposure needs adjustment"
    MOTION_BLUR = "MOTION_BLUR", "Motion blur affecting image quality"
    EQUIPMENT_FAULT = "EQUIPMENT_FAULT", "Equipment technical fault"
    FOLDED_SKIN = "FOLDED_SKIN", "Folded skin needs smoothing"
    PECTORAL_MUSCLE = "PECTORAL_MUSCLE", "Pectoral muscle not visualised correctly"
    OTHER = "OTHER", "Other"


class RepeatType(models.TextChoices):
    # For count == 2
    YES_REPEAT = "YES_REPEAT", "Yes, it was a repeat"
    NO_EXTRA_NEEDED = (
        "NO_EXTRA_NEEDED",
        "No, an extra image was needed to capture the complete view",
    )
    # For count > 2 (future)
    ALL_REPEATS = "ALL_REPEATS", "Yes, all images were repeats"
    SOME_REPEATS = (
        "SOME_REPEATS",
        "Yes, some were repeats and some were extra images",
    )
    ALL_EXTRA = (
        "ALL_EXTRA",
        "No, all extra images were needed to capture the complete view",
    )


class Series(BaseModel):
    study = models.ForeignKey(Study, on_delete=models.PROTECT)

    view_position = models.CharField(
        max_length=10,
        blank=True,
        help_text="e.g., CC, MLO",
        choices=[("CC", "CC"), ("MLO", "MLO"), ("EKLUND", "EKLUND")],
    )
    laterality = models.CharField(
        max_length=1,
        blank=True,
        help_text="L or R",
        choices=[("L", "Left"), ("R", "Right")],
    )
    count = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(20)]
    )

    is_repeat = models.CharField(
        max_length=20, choices=RepeatType.choices, blank=True, null=True
    )
    repeat_reasons = ArrayField(
        base_field=models.CharField(max_length=30, choices=RepeatReason.choices),
        default=list,
        blank=True,
    )

    class Meta:
        unique_together = ["study", "view_position", "laterality"]
