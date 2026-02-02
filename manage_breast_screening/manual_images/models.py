from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from manage_breast_screening.core.models import BaseModel


class StudyCompleteness(models.TextChoices):
    """
    A COMPLETE study is one where at least 1 image is taken
    for each of the 4 standard views.

    A study is PARTIAL if it is missing images for 1 or more views,
    but the study is considered done. There is a reason for not
    taking a full set, that cannot be addressed by recalling
    the participant for another appointment.

    A study is INCOMPLETE if the full set couldn't be taken,
    but the reason is temporary, and the participant could
    be invited back to complete the set.
    """

    COMPLETE = "COMPLETE", "Complete set of images"
    PARTIAL = "PARTIAL", "Partial mammography"
    INCOMPLETE = "INCOMPLETE", "Incomplete set of images"


class IncompleteImagesReason(models.TextChoices):
    CONSENT_WITHDRAWN = "CONSENT_WITHDRAWN", "Consent withdrawn"
    LANGUAGE_OR_LEARNING_DIFFICULTIES = (
        "LANGUAGE_OR_LEARNING_DIFFICULTIES",
        "Language or learning difficulties",
    )
    UNABLE_TO_SCAN_TISSUE = "UNABLE_TO_SCAN_TISSUE", "Unable to scan tissue"
    WHEELCHAIR = "WHEELCHAIR", "Positioning difficulties due to wheelchair"
    OTHER_MOBILITY = (
        "OTHER_MOBILITY",
        "Positioning difficulties for other mobility reasons",
    )
    TECHNICAL_ISSUES = "TECHNICAL_ISSUES", "Technical issues"
    OTHER = "OTHER", "Other"


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
    ALL_REPEATS = "ALL_REPEATS", "All additional images were repeats"
    SOME_REPEATS = "SOME_REPEATS", "Some were repeats, some were extra images"
    NO_REPEATS = "NO_REPEATS", "No repeats - all extra images were needed"



class Study(BaseModel):
    appointment = models.OneToOneField(
        "participants.Appointment", on_delete=models.PROTECT
    )

    additional_details = models.TextField(blank=True, null=False, default="")
    imperfect_but_best_possible = models.BooleanField(default=False, null=False)
    completeness = models.CharField(
        choices=StudyCompleteness, blank=True, null=False, default=""
    )

    reasons_incomplete = ArrayField(
        base_field=models.CharField(
            choices=IncompleteImagesReason, blank=True, null=False, default=""
        ),
        default=list,
        null=False,
    )
    reasons_incomplete_details = models.TextField(blank=True, null=False, default="")

    def has_series_with_multiple_images(self):
        """Check if any series has more than one image."""
        return self.series_set.filter(count__gt=1).exists()


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

    repeat_type = models.CharField(
        max_length=20, choices=RepeatType.choices, blank=True, null=True
    )
    repeat_count = models.PositiveSmallIntegerField(blank=True, null=True)
    repeat_reasons = ArrayField(
        base_field=models.CharField(max_length=30, choices=RepeatReason.choices),
        default=list,
        blank=True,
    )

    class Meta:
        unique_together = ["study", "view_position", "laterality"]

    def __str__(self):
        match (self.view_position, self.laterality):
            case ("CC", "R"):
                return "RCC"
            case ("MLO", "R"):
                return "RMLO"
            case ("EKLUND", "R"):
                return "Right Eklund"
            case ("CC", "L"):
                return "LCC"
            case ("MLO", "L"):
                return "LMLO"
            case ("EKLUND", "L"):
                return "Left Eklund"
            case _:
                return f"{self.view_position} {self.laterality}"
